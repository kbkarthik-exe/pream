"""Official Cloud Integration Adapter for GPTZero AI Text Detection.

Official GPTZero Documentation: https://gptzero.readme.io/reference/predict-text
Endpoint: POST https://api.gptzero.me/v2/predict/text

SECURITY & GOVERNANCE:
- The GPTZero API key is stored strictly on the backend and NEVER exposed to clients or frontend logs.
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

logger = logging.getLogger("aicf.ml.cloud.gptzero")


@dataclass
class GPTZeroDetectionResult:
    """Structured outcome from official GPTZero text prediction."""

    is_configured: bool
    status: str  # "SUCCESS", "CONFIGURATION_REQUIRED", "PROVIDER_ERROR", "TIMEOUT", "INSUFFICIENT_LENGTH"
    provider_name: str = "GPTZero"
    completely_generated_prob: float | None = None
    average_generated_prob: float | None = None
    class_probabilities: dict[str, float] | None = None
    sentences_count: int | None = None
    raw_response_summary: str | None = None
    error_message: str | None = None


class GPTZeroAdapter:
    """Adapter for official GPTZero Text Prediction API."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self.api_key = api_key or getattr(settings, "GPTZERO_API_KEY", None)
        base = getattr(settings, "GPTZERO_API_BASE_URL", "https://api.gptzero.me/v2")
        self.base_url = (base_url or base).rstrip("/")
        self.endpoint = f"{self.base_url}/predict/text"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def analyze_text(
        self,
        text: str,
        timeout_seconds: float = 20.0,
    ) -> GPTZeroDetectionResult:
        """Submits document text to official GPTZero API."""
        if not self.is_configured:
            return GPTZeroDetectionResult(
                is_configured=False,
                status="CONFIGURATION_REQUIRED",
                error_message=(
                    "GPTZero API key is not configured. "
                    "Cloud verification skipped (AICF local multi-model ensemble active)."
                ),
            )

        clean_text = text.strip()
        # GPTZero requires at least 250 characters (~50 words) for reliable statistical prediction
        if len(clean_text) < 250:
            return GPTZeroDetectionResult(
                is_configured=True,
                status="INSUFFICIENT_LENGTH",
                error_message="GPTZero requires at least 250 characters for external prediction.",
            )

        headers = {
            "x-api-key": self.api_key.strip(),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        body = {
            "document": clean_text,
            "version": "2024-01-09",
            "multilingual": False,
        }

        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                response = await client.post(self.endpoint, headers=headers, json=body)

            if response.status_code in (401, 403):
                logger.error("GPTZero authentication failed (HTTP %d). Invalid API key.", response.status_code)
                return GPTZeroDetectionResult(
                    is_configured=True,
                    status="PROVIDER_ERROR",
                    error_message=f"GPTZero API authentication rejected (HTTP {response.status_code}). Verify your GPTZero API key.",
                )

            if response.status_code == 429:
                logger.warning("GPTZero rate limit exceeded.")
                return GPTZeroDetectionResult(
                    is_configured=True,
                    status="PROVIDER_ERROR",
                    error_message="GPTZero rate limit exceeded (HTTP 429). Please retry later.",
                )

            if response.status_code != 200:
                logger.error("GPTZero API error HTTP %d: %s", response.status_code, response.text[:200])
                return GPTZeroDetectionResult(
                    is_configured=True,
                    status="PROVIDER_ERROR",
                    error_message=f"GPTZero returned HTTP {response.status_code}: {response.text[:120]}",
                )

            payload = response.json()
            return self._parse_response(payload)

        except httpx.TimeoutException:
            logger.warning("GPTZero API timed out after %.1fs", timeout_seconds)
            return GPTZeroDetectionResult(
                is_configured=True,
                status="TIMEOUT",
                error_message=f"GPTZero API timed out after {timeout_seconds}s.",
            )
        except Exception as exc:
            logger.error("Unexpected error contacting GPTZero: %s", exc)
            return GPTZeroDetectionResult(
                is_configured=True,
                status="PROVIDER_ERROR",
                error_message=f"GPTZero network failure: {exc}",
            )

    async def test_connection(self) -> tuple[bool, str]:
        """Pings GPTZero with a standardized verification sentence to test credentials."""
        if not self.is_configured:
            return False, "GPTZero API key not configured."

        test_doc = (
            "The rapid advancement of artificial intelligence and machine learning models "
            "has transformed academic research and automated forensic analysis in digital media forensics."
        )
        res = await self.analyze_text(test_doc, timeout_seconds=15.0)
        if res.status == "SUCCESS":
            return True, "GPTZero API connection verified successfully."
        return False, res.error_message or "GPTZero test request failed."

    def _parse_response(self, data: dict[str, Any]) -> GPTZeroDetectionResult:
        """Parses official GPTZero v2 API response JSON safely."""
        try:
            docs = data.get("documents", [])
            if not docs:
                return GPTZeroDetectionResult(
                    is_configured=True,
                    status="PROVIDER_ERROR",
                    error_message="No documents array in GPTZero response.",
                )

            d = docs[0]
            completely_ai = d.get("completely_generated_prob")
            avg_ai = d.get("average_generated_prob")
            class_probs = d.get("class_probabilities", {})
            sentences = d.get("sentences", [])

            comp_prob = round(float(completely_ai), 4) if completely_ai is not None else None
            avg_prob = round(float(avg_ai), 4) if avg_ai is not None else None

            formatted_classes: dict[str, float] = {}
            for k, v in class_probs.items():
                if v is not None:
                    formatted_classes[k] = round(float(v), 4)

            return GPTZeroDetectionResult(
                is_configured=True,
                status="SUCCESS",
                completely_generated_prob=comp_prob,
                average_generated_prob=avg_prob,
                class_probabilities=formatted_classes if formatted_classes else None,
                sentences_count=len(sentences),
                raw_response_summary=f"Processed by GPTZero v2. {len(sentences)} sentence(s) analyzed.",
            )
        except Exception as exc:
            logger.error("Failed to parse GPTZero response: %s", exc)
            return GPTZeroDetectionResult(
                is_configured=True,
                status="PROVIDER_ERROR",
                error_message=f"GPTZero parse error: {exc}",
            )
