"""Forensic Model Evaluation Metrics and Statistical Calculations.

Computes binary classification metrics, confusion matrices, Wilson score confidence
intervals, and probabilistic calibration metrics (Brier score and Expected Calibration Error).

Positive Class (1): SYNTHETIC / AI-GENERATED
Negative Class (0): AUTHENTIC / HUMAN
"""

import math
from typing import Any


def wilson_score_interval(
    k: int,
    n: int,
    confidence: float = 0.95,
) -> tuple[float, float]:
    """Calculate the Wilson score confidence interval for a binomial proportion.

    Args:
        k: Number of successes (positive outcomes).
        n: Total number of trials.
        confidence: Desired confidence level (default 0.95 for 95% CI).

    Returns:
        tuple (lower_bound, upper_bound) rounded to 4 decimal places.
    """
    if n <= 0:
        return (0.0, 0.0)

    # Normal critical value for two-sided confidence level
    # 90% -> 1.6449, 95% -> 1.95996, 99% -> 2.57583
    if confidence == 0.99:
        z = 2.57583
    elif confidence == 0.90:
        z = 1.64485
    else:
        z = 1.95996  # Standard 95% confidence

    p_hat = float(k) / float(n)
    z_sq = z * z

    denom = 1.0 + (z_sq / n)
    center = (p_hat + (z_sq / (2.0 * n))) / denom
    spread = z * math.sqrt((p_hat * (1.0 - p_hat) / n) + (z_sq / (4.0 * n * n))) / denom

    lower = max(0.0, round(center - spread, 4))
    upper = min(1.0, round(center + spread, 4))
    return (lower, upper)


def compute_confusion_matrix(
    y_true: list[int],
    y_pred: list[int],
) -> dict[str, int]:
    """Compute binary confusion matrix counts.

    Ordering:
        Class 0: Authentic / Human (Negative)
        Class 1: Synthetic / AI-Generated (Positive)

    Returns:
        dict with keys: true_positives, false_positives, true_negatives, false_negatives.
    """
    if len(y_true) != len(y_pred):
        raise ValueError(
            f"Length mismatch: y_true has {len(y_true)} items, y_pred has {len(y_pred)} items."
        )

    tp = 0
    fp = 0
    tn = 0
    fn = 0

    for true_label, pred_label in zip(y_true, y_pred, strict=True):
        if true_label == 1:
            if pred_label == 1:
                tp += 1
            else:
                fn += 1
        elif true_label == 0:
            if pred_label == 1:
                fp += 1
            else:
                tn += 1
        else:
            raise ValueError(f"Invalid true label '{true_label}'. Labels must be 0 or 1.")

    return {
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
    }


def compute_brier_score(
    y_true: list[int],
    y_prob: list[float],
) -> float | None:
    """Compute the Brier Score (Mean Squared Error of probability assessments).

    Lower is better (0.0 represents perfect probabilistic calibration).
    """
    if not y_true or len(y_true) != len(y_prob):
        return None

    squared_errors = [
        (prob - float(label)) ** 2 for label, prob in zip(y_true, y_prob, strict=True)
    ]
    return round(sum(squared_errors) / len(squared_errors), 4)


def compute_expected_calibration_error(
    y_true: list[int],
    y_prob: list[float],
    n_bins: int = 10,
) -> float | None:
    """Compute Expected Calibration Error (ECE) across equal-width probability bins."""
    if not y_true or len(y_true) != len(y_prob):
        return None

    n_samples = len(y_true)
    if n_samples == 0:
        return None

    bin_boundaries = [i / n_bins for i in range(n_bins + 1)]
    ece = 0.0

    for b in range(n_bins):
        bin_lower = bin_boundaries[b]
        bin_upper = bin_boundaries[b + 1]

        # Gather samples falling into bin [bin_lower, bin_upper]
        bin_indices = [
            i
            for i, p in enumerate(y_prob)
            if (bin_lower <= p < bin_upper) or (b == n_bins - 1 and bin_lower <= p <= bin_upper)
        ]

        bin_size = len(bin_indices)
        if bin_size > 0:
            bin_acc = sum(y_true[i] for i in bin_indices) / bin_size
            bin_conf = sum(y_prob[i] for i in bin_indices) / bin_size
            ece += (bin_size / n_samples) * abs(bin_acc - bin_conf)

    return round(ece, 4)


def compute_classification_metrics(
    y_true: list[int],
    y_pred: list[int],
    y_prob: list[float] | None = None,
    inconclusive_count: int = 0,
    error_count: int = 0,
) -> dict[str, Any]:
    """Compute full suite of binary classification metrics with confidence intervals."""
    total_evaluated = len(y_true)
    total_samples = total_evaluated + inconclusive_count + error_count

    if total_evaluated == 0:
        return {
            "status": "INSUFFICIENT DATA",
            "message": "No evaluated predictions provided for metric calculation.",
            "total_samples": total_samples,
            "evaluated_count": 0,
            "inconclusive_count": inconclusive_count,
            "error_count": error_count,
        }

    cm = compute_confusion_matrix(y_true, y_pred)
    tp = cm["true_positives"]
    fp = cm["false_positives"]
    tn = cm["true_negatives"]
    fn = cm["false_negatives"]

    # Class counts
    total_positive = tp + fn  # Ground truth Synthetic
    total_negative = tn + fp  # Ground truth Authentic

    # Accuracy
    accuracy = round((tp + tn) / total_evaluated, 4) if total_evaluated > 0 else 0.0
    acc_ci = wilson_score_interval(tp + tn, total_evaluated)

    # Precision (Positive Predictive Value)
    predicted_positives = tp + fp
    if predicted_positives > 0:
        precision: float | None = round(tp / predicted_positives, 4)
        prec_ci = wilson_score_interval(tp, predicted_positives)
    else:
        precision = None
        prec_ci = (0.0, 0.0)

    # Recall (Sensitivity / True Positive Rate)
    if total_positive > 0:
        recall: float | None = round(tp / total_positive, 4)
        rec_ci = wilson_score_interval(tp, total_positive)
    else:
        recall = None
        rec_ci = (0.0, 0.0)

    # F1 Score
    if precision is not None and recall is not None and (precision + recall) > 0:
        f1_score: float | None = round(2 * (precision * recall) / (precision + recall), 4)
    else:
        f1_score = None

    # Error Rates
    # False Positive Rate (FPR): FP / (FP + TN)
    fpr: float | None = round(fp / total_negative, 4) if total_negative > 0 else None
    # False Negative Rate (FNR): FN / (FN + TP)
    fnr: float | None = round(fn / total_positive, 4) if total_positive > 0 else None

    # Calibration Metrics
    brier = compute_brier_score(y_true, y_prob) if y_prob else None
    ece = compute_expected_calibration_error(y_true, y_prob) if y_prob else None

    return {
        "status": "EVALUATED",
        "total_samples": total_samples,
        "evaluated_samples": total_evaluated,
        "inconclusive_samples": inconclusive_count,
        "error_samples": error_count,
        "class_counts": {
            "ground_truth_synthetic": total_positive,
            "ground_truth_authentic": total_negative,
            "predicted_synthetic": predicted_positives,
            "predicted_authentic": tn + fn,
        },
        "confusion_matrix": {
            "true_positives": tp,
            "false_positives": fp,
            "true_negatives": tn,
            "false_negatives": fn,
            "matrix_2x2": [
                [tn, fp],
                [fn, tp],
            ],
            "labels": {
                "rows": ["Actual Authentic (0)", "Actual Synthetic (1)"],
                "columns": ["Predicted Authentic (0)", "Predicted Synthetic (1)"],
            },
        },
        "metrics": {
            "accuracy": accuracy,
            "accuracy_ci_95": acc_ci,
            "precision": precision,
            "precision_ci_95": prec_ci,
            "recall": recall,
            "recall_ci_95": rec_ci,
            "f1_score": f1_score,
            "false_positive_rate": fpr,
            "false_negative_rate": fnr,
            "brier_score": brier,
            "expected_calibration_error": ece,
        },
    }
