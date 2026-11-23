"""Unified Cloud Verification Hub Manager for AICF.

Coordinates:
1. Hive AI (Image, Video, Text)
2. GPTZero (Text)
3. Copyleaks (Text)

STRICT SECURITY & GOVERNANCE RULES:
- Raw API keys are NEVER exposed in frontend code, responses, logs, or unencrypted storage.
- Explicit user consent is MANDATORY before transmitting any payload to external providers.
- Local detection operates as the primary engine; cloud services are strictly optional.
- Never fabricates or mocks cloud scores when providers fail or keys are absent.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from backend.app.core.config import settings
from backend.app.core.crypto_vault import decrypt_api_key, encrypt_api_key, mask_api_key
from backend.app.ml.cloud.copyleaks_adapter import CopyleaksAdapter
from backend.app.ml.cloud.gptzero_adapter import GPTZeroAdapter
from backend.app.ml.cloud.hive_unified import UnifiedHiveAdapter
from backend.app.models.cloud_credential import UserCloudCredential
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("aicf.ml.cloud.manager")

SUPPORTED_PROVIDERS: dict[str, dict[str, Any]] = {
    "hive": {
        "name": "Hive AI",
        "description": "Visual moderation, synthetic media deepfake detection, and generative text classification.",
        "supported_types": ["image", "video", "text"],
        "doc_url": "https://docs.thehive.ai/docs/ai-image-and-video-detection",
        "auth_format": "Authorization: token <HIVE_API_KEY>",
    },
    "gptzero": {
        "name": "GPTZero",
        "description": "Perplexity and burstiness transformer-based AI document text prediction.",
        "supported_types": ["text"],
        "doc_url": "https://gptzero.readme.io/reference/predict-text",
        "auth_format": "x-api-key: <GPTZERO_API_KEY>",
    },
    "copyleaks": {
        "name": "Copyleaks",
        "description": "Enterprise text AI content detection and attribution verification.",
        "supported_types": ["text"],
        "doc_url": "https://api.copyleaks.com/documentation/v3/ai-detection",
        "auth_format": "Authorization: Bearer <TOKEN>",
    },
}


@dataclass
class CloudProviderStatus:
    """Public status card for a third-party cloud verification provider."""

    provider: str
    name: str
    description: str
    supported_types: list[str]
    is_configured: bool
    source: str  # "USER_CONFIGURED", "SYSTEM_ENVIRONMENT", "NONE"
    masked_key: str
    api_connection_status: str  # "READY", "CONFIGURATION_REQUIRED", "TEST_PASSED", "TEST_FAILED"
    last_tested_at: datetime | None
    last_test_status: str | None
    last_test_message: str | None
    doc_url: str


class CloudVerificationManager:
    """Manages secure resolution, testing, and invocation of authorized cloud verification APIs."""

    async def resolve_api_key(
        self,
        user_id: int,
        provider: str,
        db: AsyncSession,
    ) -> tuple[str | None, str]:
        """Resolves API key for a provider, prioritizing user's encrypted credential over system env."""
        # 1. Check user vault in database
        stmt = select(UserCloudCredential).where(
            UserCloudCredential.user_id == user_id,
            UserCloudCredential.provider == provider,
        )
        res = await db.execute(stmt)
        cred = res.scalar_one_or_none()

        if cred and cred.is_enabled and cred.encrypted_key:
            try:
                decrypted = decrypt_api_key(cred.encrypted_key, user_id=user_id)
                if decrypted and decrypted.strip():
                    return decrypted.strip(), "USER_CONFIGURED"
            except Exception as exc:
                logger.error("Failed to decrypt user credential for '%s': %s", provider, exc)

        # 2. Check system-level environment configuration fallback
        sys_key: str | None = None
        if provider == "hive":
            sys_key = getattr(settings, "HIVE_API_KEY", None)
        elif provider == "gptzero":
            sys_key = getattr(settings, "GPTZERO_API_KEY", None)
        elif provider == "copyleaks":
            sys_key = getattr(settings, "COPYLEAKS_API_KEY", None)

        if sys_key and sys_key.strip():
            return sys_key.strip(), "SYSTEM_ENVIRONMENT"

        return None, "NONE"

    async def get_all_provider_statuses(
        self,
        user_id: int,
        db: AsyncSession,
    ) -> list[CloudProviderStatus]:
        """Returns the complete list of cloud providers with safe masked credentials."""
        # Fetch all user credentials
        stmt = select(UserCloudCredential).where(UserCloudCredential.user_id == user_id)
        res = await db.execute(stmt)
        user_creds = {c.provider: c for c in res.scalars().all()}

        statuses: list[CloudProviderStatus] = []
        for p_id, p_meta in SUPPORTED_PROVIDERS.items():
            key, source = await self.resolve_api_key(user_id, p_id, db)
            cred = user_creds.get(p_id)

            is_cfg = bool(key)
            masked = mask_api_key(key) if key else "NOT_CONFIGURED"

            if not is_cfg:
                conn_status = "CONFIGURATION_REQUIRED"
            elif cred and cred.last_test_status:
                conn_status = "TEST_PASSED" if cred.last_test_status == "SUCCESS" else "TEST_FAILED"
            else:
                conn_status = "READY"

            statuses.append(
                CloudProviderStatus(
                    provider=p_id,
                    name=p_meta["name"],
                    description=p_meta["description"],
                    supported_types=p_meta["supported_types"],
                    is_configured=is_cfg,
                    source=source,
                    masked_key=masked,
                    api_connection_status=conn_status,
                    last_tested_at=cred.last_tested_at if cred else None,
                    last_test_status=cred.last_test_status if cred else None,
                    last_test_message=cred.last_test_message if cred else None,
                    doc_url=p_meta["doc_url"],
                )
            )

        return statuses

    async def save_user_credential(
        self,
        user_id: int,
        provider: str,
        api_key: str,
        db: AsyncSession,
    ) -> tuple[bool, str]:
        """Encrypts and persists an analyst's API key."""
        clean_p = provider.lower().strip()
        if clean_p not in SUPPORTED_PROVIDERS:
            return False, f"Unsupported cloud provider '{provider}'."

        clean_key = api_key.strip()
        if not clean_key:
            return False, "API key cannot be empty."

        encrypted = encrypt_api_key(clean_key, user_id=user_id)
        hint = mask_api_key(clean_key)

        stmt = select(UserCloudCredential).where(
            UserCloudCredential.user_id == user_id,
            UserCloudCredential.provider == clean_p,
        )
        res = await db.execute(stmt)
        cred = res.scalar_one_or_none()

        if cred:
            cred.encrypted_key = encrypted
            cred.masked_hint = hint
            cred.is_enabled = True
            cred.last_test_status = None
            cred.last_test_message = None
        else:
            cred = UserCloudCredential(
                user_id=user_id,
                provider=clean_p,
                encrypted_key=encrypted,
                masked_hint=hint,
                is_enabled=True,
            )
            db.add(cred)

        await db.commit()
        return True, f"Successfully encrypted and saved credentials for {SUPPORTED_PROVIDERS[clean_p]['name']}."

    async def delete_user_credential(
        self,
        user_id: int,
        provider: str,
        db: AsyncSession,
    ) -> tuple[bool, str]:
        """Deletes user's cloud credential."""
        clean_p = provider.lower().strip()
        stmt = select(UserCloudCredential).where(
            UserCloudCredential.user_id == user_id,
            UserCloudCredential.provider == clean_p,
        )
        res = await db.execute(stmt)
        cred = res.scalar_one_or_none()

        if not cred:
            return False, f"No credentials found for provider '{provider}'."

        await db.delete(cred)
        await db.commit()
        return True, f"Credentials removed for {SUPPORTED_PROVIDERS.get(clean_p, {}).get('name', provider)}."

    async def test_provider_connection(
        self,
        user_id: int,
        provider: str,
        custom_key: str | None,
        db: AsyncSession,
    ) -> tuple[bool, str]:
        """Performs an authorized verification request against the provider."""
        clean_p = provider.lower().strip()
        if clean_p not in SUPPORTED_PROVIDERS:
            return False, f"Unknown provider '{provider}'."

        # If a custom key is tested, use it; otherwise resolve stored key
        if custom_key and custom_key.strip():
            key = custom_key.strip()
        else:
            key, _ = await self.resolve_api_key(user_id, clean_p, db)

        if not key:
            return False, f"No API key available to test for {SUPPORTED_PROVIDERS[clean_p]['name']}."

        now = datetime.now(UTC)
        success = False
        message = ""

        if clean_p == "hive":
            adapter = UnifiedHiveAdapter(api_key=key)
            success, message = await adapter.test_connection()
        elif clean_p == "gptzero":
            adapter_gz = GPTZeroAdapter(api_key=key)
            success, message = await adapter_gz.test_connection()
        elif clean_p == "copyleaks":
            adapter_cl = CopyleaksAdapter(api_key=key)
            success, message = await adapter_cl.test_connection()

        # Update test status in database if user has a record
        stmt = select(UserCloudCredential).where(
            UserCloudCredential.user_id == user_id,
            UserCloudCredential.provider == clean_p,
        )
        res = await db.execute(stmt)
        cred = res.scalar_one_or_none()
        if cred:
            cred.last_tested_at = now
            cred.last_test_status = "SUCCESS" if success else "FAILED"
            cred.last_test_message = message[:250]
            await db.commit()

        return success, message

    # Multi-Modal Verification Invocations (Requires Explicit User Consent)
    async def verify_text(
        self,
        text: str,
        user_id: int,
        user_consent: bool,
        db: AsyncSession,
        providers: list[str] | None = None,
    ) -> dict[str, Any]:
        """Runs external cloud verification on text if user granted explicit consent."""
        if not user_consent:
            return {
                "error": "Explicit user consent is required before transmitting text payload to third-party providers.",
                "results": {},
            }

        target_providers = providers or ["gptzero", "copyleaks", "hive"]
        results: dict[str, Any] = {}

        for p in target_providers:
            key, _ = await self.resolve_api_key(user_id, p, db)
            if p == "gptzero":
                res_gz = await GPTZeroAdapter(api_key=key).analyze_text(text)
                results["gptzero"] = {
                    "is_configured": res_gz.is_configured,
                    "status": res_gz.status,
                    "ai_score": res_gz.completely_generated_prob,
                    "class_probabilities": res_gz.class_probabilities,
                    "error_message": res_gz.error_message,
                }
            elif p == "copyleaks":
                res_cl = await CopyleaksAdapter(api_key=key).analyze_text(text)
                results["copyleaks"] = {
                    "is_configured": res_cl.is_configured,
                    "status": res_cl.status,
                    "ai_score": res_cl.ai_probability,
                    "human_score": res_cl.human_probability,
                    "error_message": res_cl.error_message,
                }
            elif p == "hive":
                res_hv = await UnifiedHiveAdapter(api_key=key).analyze_text(text)
                results["hive"] = {
                    "is_configured": res_hv.is_configured,
                    "status": res_hv.status,
                    "ai_score": res_hv.ai_generated_score,
                    "error_message": res_hv.error_message,
                }

        return {"results": results}


cloud_manager = CloudVerificationManager()
