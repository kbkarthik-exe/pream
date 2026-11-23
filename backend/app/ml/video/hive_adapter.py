"""Optional Cloud Integration Adapter for Hive AI Video and Image Detection.

Official Hive Documentation: https://docs.thehive.ai/docs/ai-image-and-video-detection
Endpoint: POST https://api.thehive.ai/api/v2/task/sync

CRITICAL SECURITY & GOVERNANCE RULES:
- The Hive API key is stored strictly on the backend and NEVER exposed to clients or frontend logs.
- If HIVE_API_KEY is not configured, the adapter cleanly reports CONFIGURATION_REQUIRED
  and skips third-party verification without failing local pipeline execution.
- Third-party Hive results are kept strictly isolated from local model telemetry.
"""

import logging
from dataclasses import dataclass
from typing import Any

import httpx
from backend.app.core.config import settings

logger = logging.getLogger("aicf.ml.video.hive")


@dataclass
class HiveDetectionResult:
    """Structured outcome from Hive AI task submission."""

    is_configured: bool
    status: str  # "SUCCESS", "CONFIGURATION_REQUIRED", "PROVIDER_ERROR", "TIMEOUT"
    provider_name: str = "Hive AI"
    model_version: str | None = None
    ai_generated_score: float | None = None
    deepfake_score: float | None = None
    classes_detected: list[dict[str, Any]] | None = None
    raw_response_summary: str | None = None
    error_message: str | None = None


class HiveVideoAdapter:
    """Adapter for official Hive AI Visual Moderation and Synthetic Media Detection."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self.api_key = api_key or settings.HIVE_API_KEY
        self.base_url = (base_url or settings.HIVE_API_BASE_URL).rstrip("/")
        self.endpoint = f"{self.base_url}/task/sync"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def analyze_video(
        self,
        video_bytes: bytes,
        file_name: str,
        timeout_seconds: float = 45.0,
    ) -> HiveDetectionResult:
        """Submits video stream to official Hive API if credentials are provided."""
        if not self.is_configured:
            return HiveDetectionResult(
                is_configured=False,
                status="CONFIGURATION_REQUIRED",
                error_message="HIVE_API_KEY environment variable is not configured. Third-party Hive verification skipped.",
            )

        headers = {
            "Authorization": f"token {self.api_key}",
            "Accept": "application/json",
        }

        # Hive API accepts multipart form upload with 'media' or file field
        files = {
            "media": (file_name, video_bytes, "video/mp4"),
        }

        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                response = await client.post(self.endpoint, headers=headers, files=files)

            if response.status_code == 401 or response.status_code == 403:
                logger.error("Hive AI authentication failed (HTTP %d). Invalid API token.", response.status_code)
                return HiveDetectionResult(
                    is_configured=True,
                    status="PROVIDER_ERROR",
                    error_message=f"Hive API authentication rejected (HTTP {response.status_code}). Verify HIVE_API_KEY.",
                )

            if response.status_code == 429:
                logger.warning("Hive AI rate limit exceeded.")
                return HiveDetectionResult(
                    is_configured=True,
                    status="PROVIDER_ERROR",
                    error_message="Hive API rate limit exceeded (HTTP 429).",
                )

            if response.status_code != 200:
                logger.error("Hive API returned error HTTP %d: %s", response.status_code, response.text[:200])
                return HiveDetectionResult(
                    is_configured=True,
                    status="PROVIDER_ERROR",
                    error_message=f"Hive API returned error status HTTP {response.status_code}.",
                )

            data = response.json()
            return self._parse_hive_response(data)

        except httpx.TimeoutException:
            logger.warning("Hive API request timed out after %.1fs", timeout_seconds)
            return HiveDetectionResult(
                is_configured=True,
                status="TIMEOUT",
                error_message=f"Hive API request timed out after {timeout_seconds:.0f} seconds.",
            )
        except Exception as exc:
            logger.error("Hive API connection failed: %s", exc)
            return HiveDetectionResult(
                is_configured=True,
                status="PROVIDER_ERROR",
                error_message=f"Hive API communication error: {exc}",
            )

    def _parse_hive_response(self, data: dict[str, Any]) -> HiveDetectionResult:
        """Parses the Hive response schema extracting AI generation and deepfake classes."""
        try:
            status_entries = data.get("status", [])
            if not status_entries:
                return HiveDetectionResult(
                    is_configured=True,
                    status="SUCCESS",
                    raw_response_summary="Hive returned 200 OK with empty response payload.",
                )

            entry = status_entries[0]
            resp = entry.get("response", {})
            outputs = resp.get("output", [])

            ai_gen_score: float | None = None
            deepfake_score: float | None = None
            detected_classes: list[dict[str, Any]] = []

            for out in outputs:
                classes = out.get("classes", [])
                for cls_obj in classes:
                    cls_name = cls_obj.get("class", "").lower()
                    score = float(cls_obj.get("score", 0.0))
                    detected_classes.append({"class": cls_name, "score": round(score, 4)})

                    if cls_name in ("ai_generated", "yes_ai_generated"):
                        if ai_gen_score is None or score > ai_gen_score:
                            ai_gen_score = score
                    elif cls_name in ("deepfake", "yes_deepfake"):
                        if deepfake_score is None or score > deepfake_score:
                            deepfake_score = score

            return HiveDetectionResult(
                is_configured=True,
                status="SUCCESS",
                ai_generated_score=round(ai_gen_score, 4) if ai_gen_score is not None else None,
                deepfake_score=round(deepfake_score, 4) if deepfake_score is not None else None,
                classes_detected=detected_classes[:10],
                raw_response_summary=f"Processed by Hive AI. {len(detected_classes)} class scores evaluated.",
            )

        except Exception as exc:
            logger.warning("Failed to parse Hive API response schema: %s", exc)
            return HiveDetectionResult(
                is_configured=True,
                status="PROVIDER_ERROR",
                error_message=f"Failed to parse Hive response: {exc}",
            )


hive_adapter = HiveVideoAdapter()
