"""Unit and Integration Tests for Step 09: Model Evaluation & Benchmarking."""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app
from backend.app.ml.evaluation.datasets import get_dataset_metadata
from backend.app.ml.evaluation.evaluator import (
    get_audio_evaluation_status,
    get_video_evaluation_status,
)
from backend.app.ml.evaluation.metrics import (
    compute_brier_score,
    compute_classification_metrics,
    compute_confusion_matrix,
    compute_expected_calibration_error,
    wilson_score_interval,
)


# =========================================================================
# Phase 3 & 6: Mathematical & Metric Unit Tests
# =========================================================================

def test_wilson_score_interval_known_cases() -> None:
    """Verify Wilson confidence interval properties across boundary conditions."""
    # 0 trials
    assert wilson_score_interval(0, 0) == (0.0, 0.0)

    # 10 successes out of 10
    lower, upper = wilson_score_interval(10, 10, confidence=0.95)
    assert 0.65 <= lower <= 0.75
    assert upper == 1.0

    # 0 successes out of 10
    lower, upper = wilson_score_interval(0, 10, confidence=0.95)
    assert lower == 0.0
    assert 0.25 <= upper <= 0.35

    # 5 successes out of 10 (symmetric around 0.5)
    lower, upper = wilson_score_interval(5, 10, confidence=0.95)
    assert lower < 0.5 < upper
    assert round(0.5 - lower, 3) == round(upper - 0.5, 3)


def test_confusion_matrix_ordering_and_counts() -> None:
    """Verify confusion matrix class indexing:
    Class 0 = Authentic / Human (Negative)
    Class 1 = Synthetic / AI-Generated (Positive)
    matrix_2x2: [[TN, FP], [FN, TP]]
    """
    y_true = [0, 0, 1, 1, 0, 1]
    y_pred = [0, 1, 1, 0, 0, 1]

    cm = compute_confusion_matrix(y_true, y_pred)
    assert cm["true_positives"] == 2   # True 1, Pred 1 (indices 2, 5)
    assert cm["false_positives"] == 1  # True 0, Pred 1 (index 1)
    assert cm["true_negatives"] == 2   # True 0, Pred 0 (indices 0, 4)
    assert cm["false_negatives"] == 1  # True 1, Pred 0 (index 3)


def test_metric_calculations_known_case() -> None:
    """Test standard metrics calculation on controlled ground truth."""
    y_true = [0, 0, 0, 1, 1, 1]
    y_pred = [0, 0, 1, 1, 1, 0]
    # TP = 2, FP = 1, TN = 2, FN = 1
    # Accuracy = 4/6 = 0.6667
    # Precision = 2/3 = 0.6667
    # Recall = 2/3 = 0.6667
    # F1 = 0.6667
    # FPR = 1/3 = 0.3333
    # FNR = 1/3 = 0.3333
    metrics = compute_classification_metrics(y_true, y_pred)
    assert metrics["status"] == "EVALUATED"
    m = metrics["metrics"]
    assert m["accuracy"] == 0.6667
    assert m["precision"] == 0.6667
    assert m["recall"] == 0.6667
    assert m["f1_score"] == 0.6667
    assert m["false_positive_rate"] == 0.3333
    assert m["false_negative_rate"] == 0.3333


def test_empty_and_zero_positive_datasets() -> None:
    """Handle 0 samples or 0 predicted positives gracefully without ZeroDivisionError."""
    # Empty dataset
    empty_res = compute_classification_metrics(y_true=[], y_pred=[])
    assert empty_res["status"] == "INSUFFICIENT DATA"
    assert empty_res["evaluated_count"] == 0

    # Zero predicted positives (all pred 0)
    y_true = [0, 1, 0, 1]
    y_pred = [0, 0, 0, 0]
    res = compute_classification_metrics(y_true, y_pred)
    assert res["status"] == "EVALUATED"
    assert res["metrics"]["precision"] is None
    assert res["metrics"]["recall"] == 0.0
    assert res["metrics"]["f1_score"] is None


def test_invalid_and_mismatched_labels() -> None:
    """Ensure invalid labels and length mismatches raise explicit ValueErrors."""
    with pytest.raises(ValueError, match="Length mismatch"):
        compute_confusion_matrix([0, 1], [0])

    with pytest.raises(ValueError, match="Invalid true label"):
        compute_confusion_matrix([0, 2], [0, 1])


def test_probabilistic_calibration_metrics() -> None:
    """Verify Brier Score and Expected Calibration Error (ECE)."""
    # Perfect probability predictions
    y_true = [0, 1]
    y_prob = [0.0, 1.0]
    assert compute_brier_score(y_true, y_prob) == 0.0
    assert compute_expected_calibration_error(y_true, y_prob) == 0.0

    # Inverted probability predictions
    y_prob_inv = [1.0, 0.0]
    assert compute_brier_score(y_true, y_prob_inv) == 1.0
    assert compute_expected_calibration_error(y_true, y_prob_inv) == 1.0


def test_reproducibility() -> None:
    """Verify metric calculations are strictly deterministic given identical inputs."""
    y_true = [0, 1, 1, 0, 1, 0, 1, 1, 0, 0]
    y_pred = [0, 1, 0, 0, 1, 1, 1, 1, 0, 0]
    y_prob = [0.1, 0.9, 0.4, 0.2, 0.85, 0.75, 0.92, 0.88, 0.15, 0.05]

    run1 = compute_classification_metrics(y_true, y_pred, y_prob)
    run2 = compute_classification_metrics(y_true, y_pred, y_prob)
    assert run1 == run2


def test_unconfigured_video_and_cancelled_audio() -> None:
    """Ensure unconfigured video and cancelled audio states are transparent."""
    v_status = get_video_evaluation_status()
    assert v_status["status"] == "MODEL UNAVAILABLE"
    assert v_status["evaluation_results"]["status"] == "MODEL UNAVAILABLE"

    a_status = get_audio_evaluation_status()
    assert a_status["status"] == "CANCELLED"
    assert a_status["evaluation_results"]["status"] == "CANCELLED"

    audio_meta = get_dataset_metadata("audio")
    assert audio_meta["status"] == "CANCELLED"


# =========================================================================
# Phase 6: API Authorization & Security Integration Tests
# =========================================================================

@pytest.mark.asyncio
async def test_evaluation_summary_unauthorized() -> None:
    """Evaluation summary requires valid authentication credentials."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        res = await ac.get("/api/v1/evaluation/summary")
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_evaluation_run_unauthorized() -> None:
    """Evaluation execution requires valid authentication credentials."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        res = await ac.post("/api/v1/evaluation/run?modality=text")
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_evaluation_summary_authorized(client: AsyncClient) -> None:
    """Authenticated users can retrieve evaluation summaries with sanitized paths."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "eval_tester@aicf.internal",
            "username": "eval_tester",
            "password": "Password123!",
        },
    )
    assert reg.status_code == 201

    res = await client.get("/api/v1/evaluation/summary", cookies=reg.cookies)
    assert res.status_code == 200
    data = res.json()
    assert "text" in data
    assert "image" in data
    assert "video" in data
    assert "audio" in data

    # Verify no local absolute paths leak
    res_str = str(data)
    assert "C:\\Users\\" not in res_str
    assert "c:/Users/" not in res_str


@pytest.mark.asyncio
async def test_evaluation_single_modality_endpoints(client: AsyncClient) -> None:
    """Retrieve individual modality evaluations via authenticated GET /{modality}."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "eval_modality_tester@aicf.internal",
            "username": "eval_mod_tester",
            "password": "Password123!",
        },
    )
    assert reg.status_code == 201

    for mod in ("text", "image", "video", "audio"):
        res = await client.get(f"/api/v1/evaluation/{mod}", cookies=reg.cookies)
        assert res.status_code == 200
        data = res.json()
        assert data["modality"] == mod
        assert "model_specifications" in data
        assert "evaluation_results" in data
