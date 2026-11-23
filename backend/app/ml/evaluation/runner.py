"""Command-line runner for AICF Model Evaluation and Benchmarking.

Usage:
    python -m backend.app.ml.evaluation.runner --modality all
    python -m backend.app.ml.evaluation.runner --modality text
    python -m backend.app.ml.evaluation.runner --modality image
"""

import argparse
import json
import logging
from pathlib import Path

from backend.app.ml.evaluation.evaluator import (
    evaluate_image_model,
    evaluate_text_model,
    get_all_evaluation_summaries,
    get_audio_evaluation_status,
    get_video_evaluation_status,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("aicf.benchmark.cli")


def print_metrics_summary(title: str, results: dict) -> None:
    """Print readable benchmark summary table to console."""
    print("\n" + "=" * 70)
    print(f" {title.upper()} EVALUATION REPORT")
    print("=" * 70)

    model_spec = results.get("model_specifications", {})
    print(f"Model: {model_spec.get('model_name')} (v{model_spec.get('version')})")
    print(f"Architecture: {model_spec.get('architecture')}")
    print(f"Source: {model_spec.get('source')}")

    eval_data = results.get("evaluation_results", {})
    status = eval_data.get("status")
    print(f"Evaluation Status: {status}")

    if status == "EVALUATED":
        metrics = eval_data.get("metrics", {})
        cm = eval_data.get("confusion_matrix", {})
        counts = eval_data.get("class_counts", {})

        print("-" * 70)
        print("CONFUSION MATRIX:")
        print(f"  True Positives (Synthetic -> Synthetic):  {cm.get('true_positives')}")
        print(f"  False Positives (Authentic -> Synthetic): {cm.get('false_positives')} (Type I)")
        print(f"  True Negatives (Authentic -> Authentic):  {cm.get('true_negatives')}")
        print(f"  False Negatives (Synthetic -> Authentic): {cm.get('false_negatives')} (Type II)")
        print("-" * 70)
        print("SAMPLE COUNTS:")
        print(f"  Evaluated Samples:    {eval_data.get('evaluated_samples')}")
        print(f"  Inconclusive Samples: {eval_data.get('inconclusive_samples')}")
        print(f"  Error Samples:        {eval_data.get('error_samples')}")
        print(f"  Ground Truth Synth:   {counts.get('ground_truth_synthetic')}")
        print(f"  Ground Truth Auth:    {counts.get('ground_truth_authentic')}")
        print("-" * 70)
        print("PERFORMANCE METRICS:")
        print(
            f"  Accuracy:  {metrics.get('accuracy')}  (95% CI: {metrics.get('accuracy_ci_95')})"
        )
        print(
            f"  Precision: {metrics.get('precision')}  (95% CI: {metrics.get('precision_ci_95')})"
        )
        print(
            f"  Recall:    {metrics.get('recall')}  (95% CI: {metrics.get('recall_ci_95')})"
        )
        print(f"  F1 Score:  {metrics.get('f1_score')}")
        print(f"  FPR:       {metrics.get('false_positive_rate')}")
        print(f"  FNR:       {metrics.get('false_negative_rate')}")
        print(f"  Brier Score: {metrics.get('brier_score')}")
        print(f"  ECE:         {metrics.get('expected_calibration_error')}")
    else:
        print(f"Message: {eval_data.get('message', 'No additional details.')}")

    print("=" * 70 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AICF Model Evaluation & Benchmarking CLI",
    )
    parser.add_argument(
        "--modality",
        type=str,
        choices=["all", "text", "image", "video", "audio"],
        default="all",
        help="Modality to benchmark (default: all)",
    )
    parser.add_argument(
        "--text-dataset",
        type=str,
        default=None,
        help="Path to custom text benchmark JSON dataset",
    )
    parser.add_argument(
        "--images-dir",
        type=str,
        default=None,
        help="Path to custom images benchmark directory",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save full evaluation JSON report",
    )

    args = parser.parse_args()

    results: dict = {}

    if args.modality == "text":
        results = evaluate_text_model(dataset_path=args.text_dataset)
        print_metrics_summary("AI Text Forensics", results)
    elif args.modality == "image":
        results = evaluate_image_model(images_dir=args.images_dir)
        print_metrics_summary("AI Image Forensics", results)
    elif args.modality == "video":
        results = get_video_evaluation_status()
        print_metrics_summary("AI Video Forensics", results)
    elif args.modality == "audio":
        results = get_audio_evaluation_status()
        print_metrics_summary("AI Audio Forensics", results)
    elif args.modality == "all":
        results = get_all_evaluation_summaries(force_refresh=True)
        print_metrics_summary("AI Text Forensics", results.get("text", {}))
        print_metrics_summary("AI Image Forensics", results.get("image", {}))
        print_metrics_summary("AI Video Forensics", results.get("video", {}))
        print_metrics_summary("AI Audio Forensics", results.get("audio", {}))

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"Saved evaluation report to '{out_path}'.")


if __name__ == "__main__":
    main()
