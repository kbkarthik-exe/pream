"""Evaluation utility for AI Image Detection model.

Evaluates the detector on a directory of labeled image samples (real vs. synthetic)
and computes Precision, Recall, F1 score, False Positive Rate, False Negative Rate,
and Confusion Matrix.

Usage:
    python -m backend.app.ml.image.evaluate --dataset-dir path/to/dataset
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Any

from backend.app.ml.image.detector import image_detector

logger = logging.getLogger("aicf.ml.image.evaluate")


def evaluate_dataset(
    dataset_dir: str | Path,
    ai_subdir: str = "synthetic",
    human_subdir: str = "authentic",
    max_samples_per_class: int = 100,
) -> dict[str, Any]:
    """Evaluate image detector on a directory structured with two subdirectories:

    synthetic/ and authentic/ (or ai/ and real/).
    """
    base_path = Path(dataset_dir)
    if not base_path.exists():
        return {
            "status": "EVALUATION REQUIRED",
            "message": f"Evaluation dataset directory '{dataset_dir}' does not exist.",
        }

    ai_dir = base_path / ai_subdir
    human_dir = base_path / human_subdir

    if not ai_dir.exists() or not human_dir.exists():
        return {
            "status": "EVALUATION REQUIRED",
            "message": (
                f"Directory must contain '{ai_subdir}' and '{human_subdir}' subfolders. "
                "Provided paths not found."
            ),
        }

    # Gather image files
    exts = ("*.jpg", "*.jpeg", "*.png", "*.webp")
    ai_files: list[Path] = []
    for ext in exts:
        ai_files.extend(ai_dir.glob(ext))

    human_files: list[Path] = []
    for ext in exts:
        human_files.extend(human_dir.glob(ext))

    ai_files = ai_files[:max_samples_per_class]
    human_files = human_files[:max_samples_per_class]

    if not ai_files and not human_files:
        return {
            "status": "EVALUATION REQUIRED",
            "message": "No valid JPEG, PNG, or WebP image files found in subdirectories.",
        }

    tp = 0  # AI predicted as AI
    fp = 0  # Human predicted as AI
    tn = 0  # Human predicted as Human
    fn = 0  # AI predicted as Human
    inconclusive = 0

    # Ensure model is loaded
    image_detector.load_model()

    # Process AI-generated samples
    for f in ai_files:
        try:
            bytes_data = f.read_bytes()
            res = image_detector.analyze_image_bytes(bytes_data, file_name=f.name)
            cls = res.get("classification")
            if cls == "LIKELY AI-GENERATED":
                tp += 1
            elif cls == "LIKELY HUMAN":
                fn += 1
            else:
                inconclusive += 1
        except Exception as e:
            logger.warning("Error evaluating %s: %s", f, e)

    # Process Human-created samples
    for f in human_files:
        try:
            bytes_data = f.read_bytes()
            res = image_detector.analyze_image_bytes(bytes_data, file_name=f.name)
            cls = res.get("classification")
            if cls == "LIKELY HUMAN":
                tn += 1
            elif cls == "LIKELY AI-GENERATED":
                fp += 1
            else:
                inconclusive += 1
        except Exception as e:
            logger.warning("Error evaluating %s: %s", f, e)

    total_ai = len(ai_files)
    total_human = len(human_files)
    total_samples = total_ai + total_human

    precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
    recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
    f1 = (
        round(2 * (precision * recall) / (precision + recall), 4)
        if (precision + recall) > 0
        else 0.0
    )
    fpr = round(fp / (fp + tn), 4) if (fp + tn) > 0 else 0.0
    fnr = round(fn / (fn + tp), 4) if (fn + tp) > 0 else 0.0

    return {
        "status": "EVALUATION COMPLETED",
        "dataset_source": str(base_path),
        "total_samples": total_samples,
        "class_counts": {
            "synthetic_samples": total_ai,
            "authentic_samples": total_human,
        },
        "metrics": {
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "false_positive_rate": fpr,
            "false_negative_rate": fnr,
            "inconclusive_count": inconclusive,
        },
        "confusion_matrix": {
            "true_positives": tp,
            "false_positives": fp,
            "true_negatives": tn,
            "false_negatives": fn,
        },
        "domain_limitations": [
            "Metrics reflect performance exclusively on the provided held-out distribution.",
            "Compression artifacts and downsampling in the wild may alter error rates.",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate AICF Image Detection Model")
    parser.add_argument("--dataset-dir", type=str, required=True, help="Path to benchmark folder")
    parser.add_argument("--ai-subdir", type=str, default="synthetic")
    parser.add_argument("--human-subdir", type=str, default="authentic")
    parser.add_argument("--max-samples", type=int, default=100)
    args = parser.parse_args()

    results = evaluate_dataset(
        dataset_dir=args.dataset_dir,
        ai_subdir=args.ai_subdir,
        human_subdir=args.human_subdir,
        max_samples_per_class=args.max_samples,
    )
    print(json.dumps(results, indent=2))
