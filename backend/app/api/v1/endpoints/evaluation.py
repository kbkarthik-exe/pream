"""Evaluation API endpoints for forensic model benchmarking and accuracy metrics."""

import logging
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.api.deps import get_current_user
from backend.app.ml.evaluation.evaluator import (
    evaluate_image_model,
    evaluate_text_model,
    get_all_evaluation_summaries,
    get_audio_evaluation_status,
    get_video_evaluation_status,
)
from backend.app.models.user import User

logger = logging.getLogger("aicf.api.evaluation")

router = APIRouter()


def _sanitize_record(record: dict[str, Any]) -> dict[str, Any]:
    """Sanitize evaluation records to prevent leaking local filesystem paths."""
    sanitized = dict(record)
    if "file_path" in sanitized:
        # Keep only basename for display purposes
        sanitized["file_path"] = sanitized["file_path"].split("/")[-1].split("\\")[-1]
    return sanitized


def _sanitize_evaluation_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Ensure no private paths or secrets are exposed in evaluation responses."""
    if not isinstance(payload, dict):
        return payload

    clean = dict(payload)
    for mod in ("text", "image", "video", "audio"):
        if mod in clean and isinstance(clean[mod], dict):
            mod_data = dict(clean[mod])
            if "sample_records" in mod_data and isinstance(mod_data["sample_records"], list):
                mod_data["sample_records"] = [
                    _sanitize_record(r) for r in mod_data["sample_records"]
                ]
            clean[mod] = mod_data

    # If payload is single modality
    if "sample_records" in clean and isinstance(clean["sample_records"], list):
        clean["sample_records"] = [_sanitize_record(r) for r in clean["sample_records"]]

    return clean


@router.get(
    "/summary",
    summary="Get multimodal model evaluation benchmarks",
    response_description="Latest benchmark metrics across all forensics engines",
)
async def get_evaluation_summary(
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Retrieve verified evaluation metrics, confusion matrices, and error rates.

    Requires authenticated user credentials. Returns honest, measured results
    for real models and transparent status markers for unconfigured engines.
    """
    try:
        summaries = get_all_evaluation_summaries(force_refresh=False)
        return _sanitize_evaluation_payload(summaries)
    except Exception as exc:
        logger.error("Failed to retrieve evaluation summary: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate evaluation summary: {exc}",
        ) from exc


@router.post(
    "/run",
    summary="Execute reproducible benchmark evaluation",
    response_description="Updated benchmark metrics after re-evaluation",
)
async def run_evaluation(
    modality: Literal["all", "text", "image"] = Query(
        "all",
        description="Target modality to evaluate: 'all', 'text', or 'image'",
    ),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Execute reproducible model benchmarking on real detection engines.

    Requires authenticated user credentials. Re-computes full metrics suite
    against verified benchmark datasets.
    """
    try:
        if modality == "text":
            res = evaluate_text_model()
            return {"modality": "text", "result": _sanitize_evaluation_payload(res)}
        elif modality == "image":
            res = evaluate_image_model()
            return {"modality": "image", "result": _sanitize_evaluation_payload(res)}
        else:
            # Re-evaluate all configured modalities
            summaries = get_all_evaluation_summaries(force_refresh=True)
            return _sanitize_evaluation_payload(summaries)
    except Exception as exc:
        logger.error("Evaluation run failed for modality '%s': %s", modality, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation execution failed: {exc}",
        ) from exc


@router.get(
    "/{modality}",
    summary="Get evaluation metrics for a specific modality",
    response_description="Benchmark metrics for single detection modality",
)
async def get_modality_evaluation(
    modality: Literal["text", "image", "video", "audio"],
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Retrieve benchmark metrics for a single forensic modality."""
    try:
        summaries = get_all_evaluation_summaries(force_refresh=False)
        if modality in summaries:
            return _sanitize_evaluation_payload(summaries[modality])

        if modality == "video":
            return get_video_evaluation_status()
        elif modality == "audio":
            return get_audio_evaluation_status()

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Modality '{modality}' not found.",
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to fetch evaluation for '%s': %s", modality, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch modality evaluation: {exc}",
        ) from exc
