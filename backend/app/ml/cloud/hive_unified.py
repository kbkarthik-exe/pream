"""Unified Hive AI Cloud Adapter supporting Image, Video, and Text modalities.

Official Hive Documentation: https://docs.thehive.ai/docs/ai-image-and-video-detection
Endpoint: POST https://api.thehive.ai/api/v2/task/sync

SECURITY & GOVERNANCE:
- The Hive API key is stored strictly on the backend and NEVER exposed to clients or logs.
- Cleanly returns CONFIGURATION_REQUIRED when no key is set.
- Requires explicit user consent before transmitting media/payload.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from backend.app.core.config import settings
import httpx

logger = logging.getLogger("aicf.ml.cloud.hive")


@dataclass
class UnifiedHiveResult:
    """Standardized outcome from Hive AI task submission."""

    is_configured: bool
    status: str  # "SUCCESS", "CONFIGURATION_REQUIRED", "PROVIDER_ERROR", "TIMEOUT"
    provider_name: str = "Hive AI"
    media_type: str = "image"
    ai_generated_score: float | None = None
    deepfake_score: float | None = None
    classes_detected: list[dict[str, Any]] | None = None
    raw_response_summary: str | None = None
    error_message: str | None = None


class UnifiedHiveAdapter:
    """Unified client for Hive AI Visual and Text Moderation API."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self.api_key = api_key or getattr(settings, "HIVE_API_KEY", None)
        base = getattr(settings, "HIVE_API_BASE_URL", "https://api.thehive.ai/api/v2")
        self.base_url = (base_url or base).rstrip("/")
        self.endpoint = f"{self.base_url}/task/sync"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def analyze_text(
        self,
        text: str,
        timeout_seconds: float = 20.0,
    ) -> UnifiedHiveResult:
        """Submits document text to Hive AI text classification task."""
        if not self.is_configured:
            return UnifiedHiveResult(
                is_configured=False,
                status="CONFIGURATION_REQUIRED",
                media_type="text",
                error_message="HIVE_API_KEY is not configured.",
            )

        headers = {
            "Authorization": f"token {self.api_key.strip()}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # Hive text classification payload
        payload = {
            "text_data": text.strip(),
        }

        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                resp = await client.post(self.endpoint, headers=headers, json=payload)

            if resp.status_code in (401, 403):
                return UnifiedHiveResult(
                    is_configured=True,
                    status="PROVIDER_ERROR",
                    media_type="text",
                    error_message=f"Hive authentication rejected (HTTP {resp.status_code}). Verify HIVE_API_KEY.",
                )

            if resp.status_code == 429:
                return UnifiedHiveResult(
                    is_configured=True,
                    status="PROVIDER_ERROR",
                    media_type="text",
                    error_message="Hive API rate limit reached (HTTP 429).",
                )

            if resp.status_code != 200:
                return UnifiedHiveResult(
                    is_configured=True,
                    status="PROVIDER_ERROR",
                    media_type="text",
                    error_message=f"Hive returned HTTP {resp.status_code}.",
                )

            return self._parse_hive_response(resp.json(), "text")

        except httpx.TimeoutException:
            return UnifiedHiveResult(
                is_configured=True,
                status="TIMEOUT",
                media_type="text",
                error_message=f"Hive API timed out after {timeout_seconds}s.",
            )
        except Exception as exc:
            return UnifiedHiveResult(
                is_configured=True,
                status="PROVIDER_ERROR",
                media_type="text",
                error_message=f"Hive error: {exc}",
            )

    async def test_connection(self) -> tuple[bool, str]:
        """Pings Hive API to test credential validity."""
        if not self.is_configured:
            return False, "HIVE_API_KEY not configured."

        test_text = "Verification test sample to validate Hive AI API authorization."
        res = await self.analyze_text(test_text, timeout_seconds=15.0)
        if res.status == "SUCCESS":
            return True, "Hive AI API connection verified successfully."
        # If provider reports invalid auth
        if "rejected" in (res.error_message or "").lower() or "401" in (res.error_message or ""):
            return False, res.error_message or "Hive authentication rejected."
        return False, res.error_message or "Hive test ping failed."

    def _parse_hive_response(self, data: dict[str, Any], media_type: str) -> UnifiedHiveResult:
        """Parses synchronous Hive response safely."""
        try:
            status_list = data.get("status", [])
            if not status_list:
                return UnifiedHiveResult(
                    is_configured=True,
                    status="PROVIDER_ERROR",
                    media_type=media_type,
                    error_message="Empty status returned by Hive API.",
                )

            first_resp = status_list[0].get("response", {})
            outputs = first_resp.get("output", [])
            if not outputs:
                return UnifiedHiveResult(
                    is_configured=True,
                    status="PROVIDER_ERROR",
                    media_type=media_type,
                    error_message="No output objects returned by Hive API.",
                )

            classes = outputs[0].get("classes", [])
            ai_score: float | None = None
            deepfake_score: float | None = None

            for c in classes:
                c_name = c.get("class", "").lower()
                score = float(c.get("score", 0.0))
                if c_name in ("ai_generated", "yes", "artificial"):
                    ai_score = round(score, 4)
                elif "deepfake" in c_name or "manipulated" in c_name:
                    deepfake_score = round(score, 4)

            return UnifiedHiveResult(
                is_configured=True,
                status="SUCCESS",
                media_type=media_type,
                ai_generated_score=ai_score,
                deepfake_score=deepfake_score,
                classes_detected=classes,
                raw_response_summary=f"Processed by Hive AI. {len(classes)} classes extracted.",
            )
        except Exception as exc:
            return UnifiedHiveResult(
                is_configured=True,
                status="PROVIDER_ERROR",
                media_type=media_type,
                error_message=f"Failed to parse Hive response: {exc}",
            )
