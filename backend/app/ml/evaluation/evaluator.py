"""Core evaluation orchestrator for AICF Text, Image, and Video models.

Performs deterministic, reproducible model benchmarking on real detection engines,
recording per-sample predictions, execution time, hardware environment, and full
statistical metrics with zero hallucination.
"""

from datetime import UTC, datetime
import json
import logging
from pathlib import Path
import time
from typing import Any

from backend.app.ml.evaluation.datasets import (
    get_dataset_metadata,
    load_image_benchmark,
    load_text_benchmark,
)
from backend.app.ml.evaluation.metrics import compute_classification_metrics
from backend.app.ml.image.detector import image_detector
from backend.app.ml.text.detector import text_detector

logger = logging.getLogger("aicf.ml.evaluation.evaluator")

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
BENCHMARK_CACHE_FILE = RESULTS_DIR / "latest_benchmark.json"

# In-memory evaluation cache
_EVALUATION_CACHE: dict[str, Any] = {}


def evaluate_text_model(dataset_path: str | Path | None = None) -> dict[str, Any]:
    """Execute evaluation on the configured RoBERTa AI Text Detection model.

    Evaluates actual text_detector against the benchmark dataset.
    """
    start_eval_time = time.time()
    logger.info("Starting Text Model evaluation...")

    # Load dataset
    try:
        samples = load_text_benchmark(dataset_path)
    except Exception as exc:
        logger.error("Failed to load text benchmark dataset: %s", exc)
        return {
            "status": "EVALUATION FAILED",
            "modality": "text",
            "model_name": text_detector.model_name,
            "error": f"Failed to load dataset: {exc}",
        }

    if not samples:
        return {
            "status": "INSUFFICIENT DATA",
            "modality": "text",
            "model_name": text_detector.model_name,
            "message": "Text benchmark dataset contains 0 samples.",
        }

    # Ensure model is initialized
    text_detector.load_model()

    y_true: list[int] = []
    y_pred: list[int] = []
    y_prob: list[float] = []
    inconclusive_count = 0
    error_count = 0
    sample_records: list[dict[str, Any]] = []

    for s in samples:
        try:
            res = text_detector.analyze_text(s.text)
            if res.get("status") == "SUCCESS":
                cls = res.get("classification")
                ai_p = float(res.get("ai_probability", 0.5))

                if cls == "LIKELY AI-GENERATED":
                    pred_label = 1
                    y_true.append(s.label)
                    y_pred.append(pred_label)
                    y_prob.append(ai_p)
                elif cls == "LIKELY HUMAN":
                    pred_label = 0
                    y_true.append(s.label)
                    y_pred.append(pred_label)
                    y_prob.append(ai_p)
                else:
                    pred_label = -1
                    inconclusive_count += 1

                sample_records.append(
                    {
                        "sample_id": s.id,
                        "ground_truth": s.label,
                        "predicted_label": pred_label,
                        "classification": cls,
                        "ai_probability": ai_p,
                        "domain": s.domain,
                        "source": s.source,
                    }
                )
            else:
                error_count += 1
                sample_records.append(
                    {
                        "sample_id": s.id,
                        "ground_truth": s.label,
                        "error": res.get("error", "Inference status not SUCCESS"),
                    }
                )
        except Exception as exc:
            error_count += 1
            logger.warning("Error evaluating text sample %s: %s", s.id, exc)
            sample_records.append(
                {
                    "sample_id": s.id,
                    "ground_truth": s.label,
                    "error": str(exc),
                }
            )

    metrics = compute_classification_metrics(
        y_true=y_true,
        y_pred=y_pred,
        y_prob=y_prob,
        inconclusive_count=inconclusive_count,
        error_count=error_count,
    )

    elapsed_s = round(time.time() - start_eval_time, 2)
    dataset_meta = get_dataset_metadata("text")

    result = {
        "modality": "text",
        "evaluation_timestamp": datetime.now(UTC).isoformat(),
        "elapsed_seconds": elapsed_s,
        "model_specifications": {
            "model_name": text_detector.model_name,
            "version": text_detector.version,
            "architecture": "RoBERTa-base sequence classification (125M parameters)",
            "source": "HuggingFace Hub: roberta-base-openai-detector",
            "license": "MIT",
            "intended_task": "Binary detection of AI-generated vs. authentic human text",
            "device": str(text_detector._device),
            "limitations": [
                "Fine-tuned predominantly on GPT-2 distribution; degraded on newer frontier LLMs.",
                "Sensitive to text length (<50 words triggers inconclusive boundary).",
                "Vulnerable to paraphrasing and human-in-the-loop editing.",
            ],
        },
        "dataset_metadata": dataset_meta,
        "evaluation_results": metrics,
        "sample_records": sample_records,
    }

    _EVALUATION_CACHE["text"] = result
    _persist_cache()
    return result


def evaluate_image_model(images_dir: str | Path | None = None) -> dict[str, Any]:
    """Execute evaluation on the configured Swin ViT AI Image Detection model.

    Evaluates actual image_detector against the benchmark dataset.
    """
    start_eval_time = time.time()
    logger.info("Starting Image Model evaluation...")

    try:
        samples = load_image_benchmark(images_dir)
    except Exception as exc:
        logger.error("Failed to load image benchmark dataset: %s", exc)
        return {
            "status": "EVALUATION REQUIRED",
            "modality": "image",
            "model_name": image_detector.model_name,
            "error": f"Failed to load image benchmark: {exc}",
        }

    if not samples:
        return {
            "status": "INSUFFICIENT DATA",
            "modality": "image",
            "model_name": image_detector.model_name,
            "message": "Image benchmark directory contains 0 samples.",
        }

    image_detector.load_model()

    y_true: list[int] = []
    y_pred: list[int] = []
    y_prob: list[float] = []
    inconclusive_count = 0
    error_count = 0
    sample_records: list[dict[str, Any]] = []

    for s in samples:
        try:
            with open(s.file_path, "rb") as f:
                img_bytes = f.read()

            res = image_detector.analyze_image_bytes(img_bytes, file_name=Path(s.file_path).name)

            if res.get("status") == "SUCCESS":
                cls = res.get("classification")
                ai_p = float(res.get("ai_probability", 0.5))

                if cls == "LIKELY AI-GENERATED":
                    pred_label = 1
                    y_true.append(s.label)
                    y_pred.append(pred_label)
                    y_prob.append(ai_p)
                elif cls == "LIKELY HUMAN":
                    pred_label = 0
                    y_true.append(s.label)
                    y_pred.append(pred_label)
                    y_prob.append(ai_p)
                else:
                    pred_label = -1
                    inconclusive_count += 1

                sample_records.append(
                    {
                        "sample_id": s.id,
                        "ground_truth": s.label,
                        "predicted_label": pred_label,
                        "classification": cls,
                        "ai_probability": ai_p,
                        "file_path": s.file_path,
                    }
                )
            else:
                error_count += 1
                sample_records.append(
                    {
                        "sample_id": s.id,
                        "ground_truth": s.label,
                        "error": res.get("error", "Image inference status not SUCCESS"),
                    }
                )
        except Exception as exc:
            error_count += 1
            logger.warning("Error evaluating image sample %s: %s", s.id, exc)
            sample_records.append(
                {
                    "sample_id": s.id,
                    "ground_truth": s.label,
                    "error": str(exc),
                }
            )

    metrics = compute_classification_metrics(
        y_true=y_true,
        y_pred=y_pred,
        y_prob=y_prob,
        inconclusive_count=inconclusive_count,
        error_count=error_count,
    )

    elapsed_s = round(time.time() - start_eval_time, 2)
    dataset_meta = get_dataset_metadata("image")

    result = {
        "modality": "image",
        "evaluation_timestamp": datetime.now(UTC).isoformat(),
        "elapsed_seconds": elapsed_s,
        "model_specifications": {
            "model_name": image_detector.model_name,
            "version": image_detector.version,
            "architecture": "Swin Vision Transformer (Swin-Tiny/Base fine-tuned)",
            "source": "HuggingFace Hub: umm-maybe/AI-image-detector",
            "license": "Apache 2.0 / MIT",
            "intended_task": "Binary detection of generative synthetic images vs. authentic photography",
            "device": str(image_detector._device),
            "limitations": [
                "Vulnerable to aggressive JPEG compression (< 50 quality).",
                "Downscaling below 64x64 pixels forces inconclusive verdict.",
                "Artistic and painted human photographs may trigger false positive spectral artifacts.",
            ],
        },
        "dataset_metadata": dataset_meta,
        "evaluation_results": metrics,
        "sample_records": sample_records,
    }

    _EVALUATION_CACHE["image"] = result
    _persist_cache()
    return result


def get_video_evaluation_status() -> dict[str, Any]:
    """Return honest evaluation status for unconfigured Video detection engine."""
    return {
        "modality": "video",
        "evaluation_timestamp": datetime.now(UTC).isoformat(),
        "status": "MODEL UNAVAILABLE",
        "model_specifications": {
            "model_name": "aicf-video-deepfake-transformer",
            "version": "unconfigured",
            "architecture": "Scaffolded BaseDetector interface",
            "source": "Local scaffold (no weights downloaded)",
            "license": "Proprietary / In Development",
            "intended_task": "Deepfake video detection & temporal facial boundary analysis",
            "limitations": [
                "Pipeline requires video frame extraction, optical flow, and transformer model weights.",
                "No weights are configured in the active environment.",
            ],
        },
        "dataset_metadata": get_dataset_metadata("video"),
        "evaluation_results": {
            "status": "MODEL UNAVAILABLE",
            "message": (
                "Video detection engine is unconfigured; no model weights loaded. "
                "Benchmarking cannot execute."
            ),
        },
    }


def get_audio_evaluation_status() -> dict[str, Any]:
    """Return status for formally cancelled Audio detection engine."""
    return {
        "modality": "audio",
        "evaluation_timestamp": datetime.now(UTC).isoformat(),
        "status": "CANCELLED",
        "model_specifications": {
            "model_name": "N/A",
            "version": "N/A",
            "architecture": "None",
            "limitations": ["Audio detection feature has been cancelled."],
        },
        "dataset_metadata": get_dataset_metadata("audio"),
        "evaluation_results": {
            "status": "CANCELLED",
            "message": "AI Audio Detection engine is CANCELLED per project specification.",
        },
    }


def _load_cache_from_disk() -> dict[str, Any]:
    """Load benchmark cache from disk if available."""
    if BENCHMARK_CACHE_FILE.exists():
        try:
            with open(BENCHMARK_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception as exc:
            logger.warning("Failed reading benchmark cache: %s", exc)
    return {}


def get_all_evaluation_summaries(force_refresh: bool = False) -> dict[str, Any]:
    """Retrieve full multimodal evaluation report across text, image, video, and audio."""
    cached = _load_cache_from_disk()
    if not force_refresh and "text" in cached and "image" in cached:
        if "video" not in cached:
            cached["video"] = get_video_evaluation_status()
        if "audio" not in cached:
            cached["audio"] = get_audio_evaluation_status()
        return cached

    # Refresh or evaluate missing modalities
    text_res = (
        evaluate_text_model()
        if (force_refresh or "text" not in cached)
        else cached["text"]
    )
    image_res = (
        evaluate_image_model()
        if (force_refresh or "image" not in cached)
        else cached["image"]
    )
    video_res = get_video_evaluation_status()
    audio_res = get_audio_evaluation_status()

    summary = {
        "timestamp": datetime.now(UTC).isoformat(),
        "text": text_res,
        "image": image_res,
        "video": video_res,
        "audio": audio_res,
    }

    _persist_cache(summary)
    return summary


def _persist_cache(data: dict[str, Any] | None = None) -> None:
    """Save latest benchmark summary to disk without clobbering other modalities."""
    merged = _load_cache_from_disk()
    to_save = data if data is not None else _EVALUATION_CACHE
    merged.update(to_save)
    merged["timestamp"] = datetime.now(UTC).isoformat()
    try:
        with open(BENCHMARK_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2)
    except Exception as exc:
        logger.warning("Failed to persist benchmark cache: %s", exc)

