"""Optional Cloud Integration Adapter for Hive AI Image Detection.

Official Hive Documentation: https://docs.thehive.ai/docs/ai-image-and-video-detection
Endpoint: POST https://api.thehive.ai/api/v2/task/sync

SECURITY & GOVERNANCE:
- The Hive API key is stored strictly on the backend and NEVER exposed to frontend clients.
- If HIVE_API_KEY is not configured, the adapter cleanly reports CONFIGURATION_REQUIRED
  and skips third-party cloud verification without failing local pipeline execution.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx
from backend.app.core.config import settings

logger = logging.getLogger("aicf.ml.image.hive")


@dataclass
class HiveImageDetectionResult:
    """Structured outcome from Hive AI image task submission."""

    is_configured: bool
    status: str  # "SUCCESS", "CONFIGURATION_REQUIRED", "PROVIDER_ERROR", "TIMEOUT"
    provider_name: str = "Hive AI"
    model_version: str | None = None
    ai_generated_score: float | None = None
    generator_attribution: dict[str, float] | None = None
    classes_detected: list[dict[str, Any]] | None = None
    raw_response_summary: str | None = None
    error_message: str | None = None


class HiveImageAdapter:
    """Adapter for official Hive AI Visual Moderation and Image Synthetic Detection."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self.api_key = api_key or getattr(settings, "HIVE_API_KEY", None)
        base = getattr(settings, "HIVE_API_BASE_URL", "https://api.thehive.ai/api/v2")
        self.base_url = (base_url or base).rstrip("/")
        self.endpoint = f"{self.base_url}/task/sync"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def analyze_image(
        self,
        image_bytes: bytes,
        file_name: str,
        timeout_seconds: float = 30.0,
    ) -> HiveImageDetectionResult:
        """Submits image to official Hive API if credentials are provided."""
        if not self.is_configured:
            return HiveImageDetectionResult(
                is_configured=False,
                status="CONFIGURATION_REQUIRED",
                error_message=(
                    "HIVE_API_KEY environment variable is not configured. "
                    "Third-party Hive verification skipped (local pipeline active)."
                ),
            )

        headers = {
            "Authorization": f"token {self.api_key}",
            "Accept": "application/json",
        }

        # Hive API accepts multipart form upload with 'media'
        files = {
            "media": (file_name, image_bytes, "image/png"),
        }

        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                response = await client.post(self.endpoint, headers=headers, files=files)

            if response.status_code in (401, 403):
                logger.error("Hive AI authentication failed (HTTP %d). Invalid API token.", response.status_code)
                return HiveImageDetectionResult(
                    is_configured=True,
                    status="PROVIDER_ERROR",
                    error_message=f"Hive API authentication rejected (HTTP {response.status_code}). Verify HIVE_API_KEY.",
                )

            if response.status_code == 429:
                logger.warning("Hive AI rate limit exceeded.")
                return HiveImageDetectionResult(
                    is_configured=True,
                    status="PROVIDER_ERROR",
                    error_message="Hive API rate limit exceeded (HTTP 429).",
                )

            if response.status_code != 200:
                logger.error("Hive API returned error HTTP %d: %s", response.status_code, response.text[:200])
                return HiveImageDetectionResult(
                    is_configured=True,
                    status="PROVIDER_ERROR",
                    error_message=f"Hive API returned error status HTTP {response.status_code}.",
                )

            payload = response.json()
            return self._parse_hive_response(payload)

        except httpx.TimeoutException:
            logger.warning("Hive API request timed out after %.1fs", timeout_seconds)
            return HiveImageDetectionResult(
                is_configured=True,
                status="TIMEOUT",
                error_message=f"Hive API timed out after {timeout_seconds}s.",
            )
        except Exception as exc:
            logger.error("Unexpected error contacting Hive API: %s", exc)
            return HiveImageDetectionResult(
                is_configured=True,
                status="PROVIDER_ERROR",
                error_message=f"Hive network failure: {exc}",
            )

    def _parse_hive_response(self, data: dict[str, Any]) -> HiveImageDetectionResult:
        """Parses synchronous Hive response safely."""
        try:
            status_list = data.get("status", [])
            if not status_list:
                return HiveImageDetectionResult(
                    is_configured=True,
                    status="PROVIDER_ERROR",
                    error_message="Empty status returned by Hive API.",
                )

            first_resp = status_list[0].get("response", {})
            outputs = first_resp.get("output", [])
            if not outputs:
                return HiveImageDetectionResult(
                    is_configured=True,
                    status="PROVIDER_ERROR",
                    error_message="No output objects returned by Hive API.",
                )

            classes = outputs[0].get("classes", [])
            ai_score: float | None = None
            generators: dict[str, float] = {}

            for c in classes:
                c_name = c.get("class", "").lower()
                score = float(c.get("score", 0.0))
                if c_name in ("ai_generated", "yes", "artificial"):
                    ai_score = round(score, 4)
                elif c_name in ("midjourney", "stable_diffusion", "dall_e", "flux", "firefly"):
                    generators[c_name] = round(score, 4)

            return HiveImageDetectionResult(
                is_configured=True,
                status="SUCCESS",
                ai_generated_score=ai_score,
                generator_attribution=generators if generators else None,
                classes_detected=classes,
                raw_response_summary=f"Processed by Hive AI. {len(classes)} classes extracted.",
            )
        except Exception as exc:
            logger.error("Failed to parse Hive API response JSON: %s", exc)
            return HiveImageDetectionResult(
                is_configured=True,
                status="PROVIDER_ERROR",
                error_message=f"Hive response parse error: {exc}",
            )
