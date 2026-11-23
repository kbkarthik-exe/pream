"""AICF Model Evaluation & Benchmarking Package.

Provides reproducible dataset evaluation, metric calculations (Precision, Recall, F1,
FPR, FNR, Wilson Confidence Intervals, Brier Score, and Confusion Matrix), and
evaluation reporting for text, image, and video detection engines.
"""

from backend.app.ml.evaluation.metrics import (
    compute_classification_metrics,
    compute_confusion_matrix,
    wilson_score_interval,
)

__all__ = [
    "compute_classification_metrics",
    "compute_confusion_matrix",
    "wilson_score_interval",
]
