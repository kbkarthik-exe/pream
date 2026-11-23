"""Official Cloud Integration Adapter for Copyleaks AI Text Detection.

Official Copyleaks Documentation: https://api.copyleaks.com/documentation/v3/ai-detection
Endpoints:
- Token login: POST https://id.copyleaks.com/v3/account/login/api
- AI Detection: POST https://api.copyleaks.com/v3/ai-detection/by-text

SECURITY & GOVERNANCE:
- The Copyleaks API key and credentials are stored strictly on the backend.
- If no key is configured, cleanly reports CONFIGURATION_REQUIRED without failing local analysis.
- Third-party cloud verdicts are kept strictly isolated from local model scores.
- Requires explicit user consent before transmitting text payload.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx
from backend.app.core.config import settings

logger = logging.getLogger("aicf.ml.cloud.copyleaks")


@dataclass
class CopyleaksDetectionResult:
    """Structured outcome from official Copyleaks text prediction."""

    is_configured: bool
    status: str  # "SUCCESS", "CONFIGURATION_REQUIRED", "PROVIDER_ERROR", "TIMEOUT"
    provider_name: str = "Copyleaks"
    ai_probability: float | None = None
    human_probability: float | None = None
    scanned_words: int | None = None
    raw_response_summary: str | None = None
    error_message: str | None = None


class CopyleaksAdapter:
    """Adapter for official Copyleaks AI Detection API."""

    def __init__(
        self,
        api_key: str | None = None,
        email: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.api_key = api_key or getattr(settings, "COPYLEAKS_API_KEY", None)
        self.email = email or getattr(settings, "COPYLEAKS_EMAIL", None)
        base = getattr(settings, "COPYLEAKS_API_BASE_URL", "https://api.copyleaks.com/v3")
        self.base_url = (base_url or base).rstrip("/")
        self.detection_endpoint = f"{self.base_url}/ai-detection/by-text"
        self.auth_endpoint = "https://id.copyleaks.com/v3/account/login/api"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def analyze_text(
        self,
        text: str,
        timeout_seconds: float = 25.0,
    ) -> CopyleaksDetectionResult:
        """Submits document text to official Copyleaks AI Detection API."""
        if not self.is_configured:
            return CopyleaksDetectionResult(
                is_configured=False,
                status="CONFIGURATION_REQUIRED",
                error_message=(
                    "Copyleaks API key is not configured. "
                    "Cloud verification skipped (AICF local multi-model ensemble active)."
                ),
            )

        clean_text = text.strip()
        if len(clean_text) < 100:
            return CopyleaksDetectionResult(
                is_configured=True,
                status="PROVIDER_ERROR",
                error_message="Copyleaks requires at least 100 characters for AI detection.",
            )

        # Copyleaks accepts either direct Bearer token (if user configured a session token)
        # or exchanges (email, key) for Bearer token.
        auth_token = self.api_key.strip()
        if self.email and self.email.strip():
            # Perform token exchange
            try:
                token = await self._exchange_credentials(self.email.strip(), self.api_key.strip())
                if token:
                    auth_token = token
            except Exception as exc:
                return CopyleaksDetectionResult(
                    is_configured=True,
                    status="PROVIDER_ERROR",
                    error_message=f"Copyleaks authentication exchange failed: {exc}",
                )

        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        body = {
            "text": clean_text,
            "sandbox": False,
        }

        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                response = await client.post(self.detection_endpoint, headers=headers, json=body)

            if response.status_code in (401, 403):
                logger.error("Copyleaks authentication failed (HTTP %d).", response.status_code)
                return CopyleaksDetectionResult(
                    is_configured=True,
                    status="PROVIDER_ERROR",
                    error_message=f"Copyleaks authentication failed (HTTP {response.status_code}). Verify your Copyleaks key.",
                )

            if response.status_code == 429:
                return CopyleaksDetectionResult(
                    is_configured=True,
                    status="PROVIDER_ERROR",
                    error_message="Copyleaks rate limit reached (HTTP 429).",
                )

            if response.status_code != 200:
                return CopyleaksDetectionResult(
                    is_configured=True,
                    status="PROVIDER_ERROR",
                    error_message=f"Copyleaks returned HTTP {response.status_code}: {response.text[:120]}",
                )

            payload = response.json()
            return self._parse_response(payload)

        except httpx.TimeoutException:
            return CopyleaksDetectionResult(
                is_configured=True,
                status="TIMEOUT",
                error_message=f"Copyleaks API timed out after {timeout_seconds}s.",
            )
        except Exception as exc:
            return CopyleaksDetectionResult(
                is_configured=True,
                status="PROVIDER_ERROR",
                error_message=f"Copyleaks network error: {exc}",
            )

    async def _exchange_credentials(self, email: str, key: str) -> str | None:
        """Exchanges email and API key for a Copyleaks Bearer access token."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                self.auth_endpoint,
                json={"email": email, "key": key},
                headers={"Content-Type": "application/json"},
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("access_token")
            logger.warning("Copyleaks login endpoint returned HTTP %d", resp.status_code)
            return None

    async def test_connection(self) -> tuple[bool, str]:
        """Pings Copyleaks to test credential validity."""
        if not self.is_configured:
            return False, "Copyleaks credentials not configured."

        test_text = (
            "This is a forensic verification sample submitted to validate Copyleaks API communication "
            "and check authorization status for synthetic media detection."
        )
        res = await self.analyze_text(test_text, timeout_seconds=15.0)
        if res.status == "SUCCESS":
            return True, "Copyleaks connection verified successfully."
        return False, res.error_message or "Copyleaks verification test failed."

    def _parse_response(self, data: dict[str, Any]) -> CopyleaksDetectionResult:
        """Parses official Copyleaks response JSON safely."""
        try:
            summary = data.get("summary", {})
            ai_score = summary.get("ai")
            human_score = summary.get("human")
            words = data.get("scannedWords", 0)

            ai_p = round(float(ai_score), 4) if ai_score is not None else None
            hum_p = round(float(human_score), 4) if human_score is not None else None

            return CopyleaksDetectionResult(
                is_configured=True,
                status="SUCCESS",
                ai_probability=ai_p,
                human_probability=hum_p,
                scanned_words=words,
                raw_response_summary=f"Processed by Copyleaks. {words} word(s) scanned.",
            )
        except Exception as exc:
            return CopyleaksDetectionResult(
                is_configured=True,
                status="PROVIDER_ERROR",
                error_message=f"Failed to parse Copyleaks response: {exc}",
            )
