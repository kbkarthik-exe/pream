"""Automated test suite for AI Image Forensics Engine (AICF Step 05).

Covers:
1. Valid JPEG, PNG, and WebP files.
2. Corrupted image files.
3. Unsupported file types.
4. Empty uploads.
5. Oversized files.
6. Excessive image dimensions.
7. Authentication requirements.
8. User-to-user result isolation.
9. Model unavailable / loading failure handling.
10. Inference exceptions and safe error handling.
11. Inconclusive classification for low-resolution images.
12. SHA-256 calculation accuracy.
13. Temporary file cleanup.
14. Database history persistence.
15. Save to forensic cases archive.
"""

import hashlib
import io
import os
import tempfile

import numpy as np
import pytest
from backend.app.core.config import settings
from backend.app.ml.image import image_detector
from httpx import AsyncClient
from PIL import Image


def create_in_memory_image(
    width: int = 128,
    height: int = 128,
    fmt: str = "JPEG",
    mode: str = "RGB",
) -> bytes:
    """Generate in-memory valid image bytes in requested format."""
    arr = np.random.randint(40, 220, (height, width, 3), dtype=np.uint8)
    img = Image.fromarray(arr, mode=mode)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


async def create_authenticated_analyst(client: AsyncClient, suffix: str = "1") -> dict[str, str]:
    """Helper to register and authenticate an analyst session."""
    payload = {
        "email": f"analyst_img_{suffix}@aicf.internal",
        "username": f"analyst_img_{suffix}",
        "password": "SecurePassword123!",
        "full_name": f"Analyst Img {suffix}",
    }
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201
    return {
        settings.COOKIE_NAME: resp.cookies[settings.COOKIE_NAME],
    }


# 1. Authentication Requirements
@pytest.mark.asyncio
async def test_image_analysis_unauthenticated(client: AsyncClient):
    """Unauthenticated requests must be rejected with HTTP 401 Unauthorized."""
    img_bytes = create_in_memory_image(128, 128, "JPEG")
    files = {"file": ("test.jpg", img_bytes, "image/jpeg")}
    response = await client.post("/api/v1/image/analyze", files=files)
    assert response.status_code == 401
    assert "Authentication required" in response.json()["detail"]


# 2. Empty Uploads
@pytest.mark.asyncio
async def test_image_analysis_empty_upload(client: AsyncClient):
    """Uploading an empty file (0 bytes) must return HTTP 422 Unprocessable Entity."""
    cookies = await create_authenticated_analyst(client, "empty")
    client.cookies = cookies

    files = {"file": ("empty.jpg", b"", "image/jpeg")}
    response = await client.post("/api/v1/image/analyze", files=files)
    assert response.status_code == 422
    assert "empty" in response.json()["detail"].lower()


# 3. Corrupted Image Files
@pytest.mark.asyncio
async def test_image_analysis_corrupted_file(client: AsyncClient):
    """Corrupted image bytes must be rejected safely with HTTP 422."""
    cookies = await create_authenticated_analyst(client, "corrupt")
    client.cookies = cookies

    corrupt_bytes = b"\xff\xd8\xff\xe0" + b"CORRUPTED_RAW_GARBAGE_BYTES" * 10
    files = {"file": ("corrupt.jpg", corrupt_bytes, "image/jpeg")}
    response = await client.post("/api/v1/image/analyze", files=files)
    assert response.status_code == 422
    assert "corrupted" in response.json()["detail"].lower()


# 4. Unsupported File Types
@pytest.mark.asyncio
async def test_image_analysis_unsupported_format(client: AsyncClient):
    """Unsupported file formats (e.g., text, pdf) disguised as images must be rejected."""
    cookies = await create_authenticated_analyst(client, "unsupp")
    client.cookies = cookies

    text_bytes = b"Hello world, this is a plain text file pretending to be an image."
    files = {"file": ("fake.png", text_bytes, "image/png")}
    response = await client.post("/api/v1/image/analyze", files=files)
    assert response.status_code == 422
    err_detail = response.json()["detail"].lower()
    assert "corrupted" in err_detail or "unsupported" in err_detail


# 5. Oversized Files
@pytest.mark.asyncio
async def test_image_analysis_oversized_file(client: AsyncClient, monkeypatch):
    """Files exceeding maximum allowed size must return HTTP 422."""
    cookies = await create_authenticated_analyst(client, "oversized")
    client.cookies = cookies

    # Set temporary low threshold for testing size validation
    monkeypatch.setattr(settings, "IMAGE_MAX_SIZE_BYTES", 500)
    img_bytes = create_in_memory_image(128, 128, "JPEG")  # ~2-5 KB > 500 bytes

    files = {"file": ("large.jpg", img_bytes, "image/jpeg")}
    response = await client.post("/api/v1/image/analyze", files=files)
    assert response.status_code == 422
    assert "exceeds maximum" in response.json()["detail"]


# 6. Excessive Image Dimensions
@pytest.mark.asyncio
async def test_image_analysis_excessive_dimensions(client: AsyncClient, monkeypatch):
    """Images exceeding maximum pixel safety limits must return HTTP 422."""
    cookies = await create_authenticated_analyst(client, "dims")
    client.cookies = cookies

    # Mock low pixel threshold
    monkeypatch.setattr(settings, "IMAGE_MAX_PIXELS", 5000)  # Lower than 128x128 = 16,384 px
    img_bytes = create_in_memory_image(128, 128, "PNG")

    files = {"file": ("bigdims.png", img_bytes, "image/png")}
    response = await client.post("/api/v1/image/analyze", files=files)
    assert response.status_code == 422
    assert "exceeds" in response.json()["detail"]


# 7. Valid JPEG Ingestion & Real Inference
@pytest.mark.asyncio
async def test_image_analysis_valid_jpeg(client: AsyncClient):
    """Valid JPEG must execute real inference and return structured results."""
    cookies = await create_authenticated_analyst(client, "jpeg")
    client.cookies = cookies

    img_bytes = create_in_memory_image(128, 128, "JPEG")
    expected_hash = hashlib.sha256(img_bytes).hexdigest()

    files = {"file": ("sample.jpg", img_bytes, "image/jpeg")}
    data = {"save_to_cases": "false"}
    response = await client.post("/api/v1/image/analyze", files=files, data=data)
    assert response.status_code == 200

    res = response.json()
    assert res["status"] in ("SUCCESS", "INCONCLUSIVE")
    assert res["image_format"] == "JPEG"
    assert res["image_width"] == 128
    assert res["image_height"] == 128
    assert res["file_hash"] == expected_hash
    assert res["classification"] in ("LIKELY AI-GENERATED", "LIKELY HUMAN", "INCONCLUSIVE")
    assert res["confidence_score"] is not None
    assert len(res["evidence"]) > 0
    assert len(res["limitations"]) > 0


# 8. Valid PNG Ingestion & Real Inference
@pytest.mark.asyncio
async def test_image_analysis_valid_png(client: AsyncClient):
    """Valid PNG must execute real inference and return structured results."""
    cookies = await create_authenticated_analyst(client, "png")
    client.cookies = cookies

    img_bytes = create_in_memory_image(128, 128, "PNG")
    expected_hash = hashlib.sha256(img_bytes).hexdigest()

    files = {"file": ("sample.png", img_bytes, "image/png")}
    response = await client.post("/api/v1/image/analyze", files=files)
    assert response.status_code == 200

    res = response.json()
    assert res["status"] in ("SUCCESS", "INCONCLUSIVE")
    assert res["image_format"] == "PNG"
    assert res["file_hash"] == expected_hash


# 9. Valid WebP Ingestion & Real Inference
@pytest.mark.asyncio
async def test_image_analysis_valid_webp(client: AsyncClient):
    """Valid WebP must execute real inference and return structured results."""
    cookies = await create_authenticated_analyst(client, "webp")
    client.cookies = cookies

    img_bytes = create_in_memory_image(128, 128, "WEBP")
    expected_hash = hashlib.sha256(img_bytes).hexdigest()

    files = {"file": ("sample.webp", img_bytes, "image/webp")}
    response = await client.post("/api/v1/image/analyze", files=files)
    assert response.status_code == 200

    res = response.json()
    assert res["status"] in ("SUCCESS", "INCONCLUSIVE")
    assert res["image_format"] == "WEBP"
    assert res["file_hash"] == expected_hash


# 10. Low Resolution Image Returns INCONCLUSIVE
@pytest.mark.asyncio
async def test_image_analysis_low_resolution_inconclusive(client: AsyncClient):
    """Images below 64x64 or below minimum dimension gate must yield INCONCLUSIVE."""
    cookies = await create_authenticated_analyst(client, "lowres")
    client.cookies = cookies

    # 48x48 is below the 64x64 reliable vision transformer receptive field threshold
    img_bytes = create_in_memory_image(48, 48, "PNG")
    files = {"file": ("tiny.png", img_bytes, "image/png")}
    response = await client.post("/api/v1/image/analyze", files=files)
    assert response.status_code == 200

    res = response.json()
    assert res["classification"] == "INCONCLUSIVE"


# 11. Model Unavailable / Loading Failure Handling
@pytest.mark.asyncio
async def test_image_analysis_model_unavailable(client: AsyncClient, monkeypatch):
    """When the vision model is unconfigured or fails to load, it must return BLOCKED status."""
    cookies = await create_authenticated_analyst(client, "unavail")
    client.cookies = cookies

    # Simulate model loading failure
    monkeypatch.setattr(image_detector, "_is_loaded", False)
    monkeypatch.setattr(image_detector, "_model", None)
    monkeypatch.setattr(image_detector, "load_model", lambda: False)
    monkeypatch.setattr(image_detector, "_load_error", "Weights unavailable in local test sandbox")

    img_bytes = create_in_memory_image(128, 128, "JPEG")
    files = {"file": ("test.jpg", img_bytes, "image/jpeg")}
    response = await client.post("/api/v1/image/analyze", files=files)
    assert response.status_code == 200

    res = response.json()
    assert res["status"] == "BLOCKED"
    assert res["classification"] == "INCONCLUSIVE"
    assert any("simulated results are disabled" in lim for lim in res["limitations"])


# 12. Inference Exceptions Safe Handling
@pytest.mark.asyncio
async def test_image_analysis_inference_exception(client: AsyncClient, monkeypatch):
    """Inference exceptions must return FAILED status safely without leaking stack traces."""
    cookies = await create_authenticated_analyst(client, "except")
    client.cookies = cookies

    def mock_forward(*args, **kwargs):
        raise RuntimeError("GPU Out of Memory or Tensor mismatch simulation")

    monkeypatch.setattr(image_detector, "_is_loaded", True)
    monkeypatch.setattr(image_detector, "_model", mock_forward)

    img_bytes = create_in_memory_image(128, 128, "JPEG")
    files = {"file": ("error.jpg", img_bytes, "image/jpeg")}
    response = await client.post("/api/v1/image/analyze", files=files)
    assert response.status_code == 200

    res = response.json()
    assert res["status"] == "FAILED"
    assert res["classification"] == "INCONCLUSIVE"


# 13. User-to-User Result Isolation
@pytest.mark.asyncio
async def test_image_analysis_user_isolation(client: AsyncClient):
    """Analyst B cannot access Analyst A's private analysis record (HTTP 403 Forbidden)."""
    # Analyst A creates an analysis
    cookies_a = await create_authenticated_analyst(client, "userA")
    client.cookies = cookies_a

    img_bytes = create_in_memory_image(128, 128, "JPEG")
    files = {"file": ("private.jpg", img_bytes, "image/jpeg")}
    res_a = await client.post("/api/v1/image/analyze", files=files)
    assert res_a.status_code == 200
    analysis_id = res_a.json()["analysis_id"]

    # Analyst B attempts to view Analyst A's analysis record
    cookies_b = await create_authenticated_analyst(client, "userB")
    client.cookies = cookies_b

    response = await client.get(f"/api/v1/image/{analysis_id}")
    assert response.status_code == 403
    assert "forbidden" in response.json()["detail"].lower()


# 14. History Persistence & Save to Forensic Cases
@pytest.mark.asyncio
async def test_image_analysis_history_and_case_save(client: AsyncClient):
    """Analysis is persisted in history and optionally created in ForensicReport cases."""
    cookies = await create_authenticated_analyst(client, "hist")
    client.cookies = cookies

    img_bytes = create_in_memory_image(128, 128, "PNG")
    files = {"file": ("evidence_case.png", img_bytes, "image/png")}
    data = {"save_to_cases": "true"}

    resp = await client.post("/api/v1/image/analyze", files=files, data=data)
    assert resp.status_code == 200
    case_report_id = resp.json().get("case_report_id")
    assert case_report_id is not None

    # Verify history retrieval
    hist_resp = await client.get("/api/v1/image/history")
    assert hist_resp.status_code == 200
    history_items = hist_resp.json()
    assert len(history_items) >= 1
    assert any(h["file_name"] == "evidence_case.png" for h in history_items)

    # Verify report is accessible in reports endpoint
    report_resp = await client.get(f"/api/v1/reports/{case_report_id}")
    assert report_resp.status_code == 200
    assert report_resp.json()["media_type"] == "image"


# 15. Temporary File Cleanup & Memory Safety
@pytest.mark.asyncio
async def test_image_analysis_no_temp_file_leak(client: AsyncClient):
    """Image analysis must process entirely in memory without leaving temporary files on disk."""
    cookies = await create_authenticated_analyst(client, "cleanup")
    client.cookies = cookies

    temp_dir = tempfile.gettempdir()
    initial_files = set(os.listdir(temp_dir))

    img_bytes = create_in_memory_image(128, 128, "JPEG")
    files = {"file": ("clean_check.jpg", img_bytes, "image/jpeg")}
    resp = await client.post("/api/v1/image/analyze", files=files)
    assert resp.status_code == 200

    final_files = set(os.listdir(temp_dir))
    new_files = final_files - initial_files
    # Verify no persistent AICF image dump files were orphaned
    assert not any("aicf" in f.lower() and "clean_check" in f.lower() for f in new_files)


# 16. Multi-Detector Image Ensemble Calibration
def test_image_analysis_ensemble_calibration():
    """Verify ImageEnsembleAggregator applies temperature scaling and covariance discount."""
    from backend.app.ml.image.ensemble import ImageEnsembleAggregator

    aggregator = ImageEnsembleAggregator(temperature=1.20, covariance_rho=0.68)

    # Moderate extreme probability via temperature scaling
    cal_extreme = aggregator.calibrate_probability(0.99)
    assert 0.85 <= cal_extreme < 0.99, f"Expected moderated probability, got {cal_extreme}"

    # Verify multi-model consensus discounting correlated agreement
    res = aggregator.aggregate(
        swin_score=0.92,
        vit_score=0.90,
        fft_features={"spectral_anisotropy": 0.52, "high_freq_ratio": 0.08},
        noise_features={"noise_variance": 12.0},
        ela_features={"ela_discontinuity_score": 7.5},
        image_dims=(256, 256),
    )
    assert res["active_detectors_count"] == 2
    assert res["classification"] == "Likely AI-generated"
    assert res["consensus_score"] > 0.70
    assert any("covariance discount" in note.lower() for note in res["notes"])


# 17. Secondary ViT Image Detector Execution
def test_image_analysis_secondary_vit_execution():
    """Verify VitImageDetector handles predictions and pre-flight gates gracefully."""
    from backend.app.ml.image.detector import VitImageDetector
    from PIL import Image

    vit = VitImageDetector()
    test_img = Image.new("RGB", (128, 128), color=(100, 150, 200))
    ai_prob, human_prob, latency, evidence = vit.predict(test_img)

    # If weights are cached, returns valid probabilities; if resource constrained, returns None with honest evidence
    if vit.is_loaded:
        assert ai_prob is not None
        assert human_prob is not None
        assert 0.0 <= ai_prob <= 1.0
        assert latency >= 0.0
    else:
        assert vit.status in ("UNAVAILABLE", "RESOURCE_CONSTRAINED")
        assert len(evidence) > 0


# 18. Error Level Analysis & Explainability Heatmap
def test_image_analysis_ela_explainability_heatmap():
    """Verify Error Level Analysis generates valid quantitative metrics and data URLs."""
    from backend.app.ml.image.heatmap import (
        compute_error_level_analysis,
        generate_image_forensic_heatmap,
    )
    from PIL import Image

    test_img = Image.new("RGB", (128, 128), color=(180, 90, 60))
    ela = compute_error_level_analysis(test_img, quality=95)
    assert "ela_mean_error" in ela
    assert "ela_discontinuity_score" in ela
    assert ela["heatmap_data_url"].startswith("data:image/png;base64,")

    full_heat = generate_image_forensic_heatmap(test_img)
    assert "heatmap_data_url" in full_heat
    assert "explanation" in full_heat
    assert len(full_heat["explanation"]) > 20


# 19. Multi-Detector API Response
@pytest.mark.asyncio
async def test_image_analysis_multi_detector_api_response(client: AsyncClient):
    """Verify POST /api/v1/image/analyze returns structured detector_scores, ensemble, and heatmap."""
    cookies = await create_authenticated_analyst(client, "multidet")
    client.cookies = cookies

    img_bytes = create_in_memory_image(128, 128, "PNG")
    files = {"file": ("multi_test.png", img_bytes, "image/png")}
    resp = await client.post("/api/v1/image/analyze", files=files)
    assert resp.status_code == 200

    data = resp.json()
    assert "detector_scores" in data
    assert len(data["detector_scores"]) >= 3
    assert any(d["detector_id"] == "umm-maybe/AI-image-detector" for d in data["detector_scores"])
    assert any(d["detector_id"] == "spectral-spatial-profiler" for d in data["detector_scores"])
    assert any(d["detector_id"] == "error-level-analysis" for d in data["detector_scores"])

    assert "ensemble" in data
    assert data["ensemble"] is not None
    assert "consensus_score" in data["ensemble"]
    assert "temperature_applied" in data["ensemble"]

    assert "heatmap" in data
    assert data["heatmap"] is not None
    assert data["heatmap"]["heatmap_data_url"].startswith("data:image/png;base64,")


# 20. PDF Generation with Multi-Detector Consensus Table
@pytest.mark.asyncio
async def test_image_analysis_pdf_with_ensemble(client: AsyncClient):
    """Verify PDF generator successfully compiles image report containing ensemble and ELA tables."""
    cookies = await create_authenticated_analyst(client, "pdfens")
    client.cookies = cookies

    img_bytes = create_in_memory_image(128, 128, "JPEG")
    files = {"file": ("pdf_target.jpg", img_bytes, "image/jpeg")}
    post_resp = await client.post("/api/v1/image/analyze", files=files)
    assert post_resp.status_code == 200
    analysis_id = post_resp.json()["analysis_id"]

    pdf_resp = await client.get(f"/api/v1/image/{analysis_id}/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert pdf_resp.content.startswith(b"%PDF-")
    assert len(pdf_resp.content) > 5000


# 21. Hive AI Image Cloud Adapter Handling
@pytest.mark.asyncio
async def test_image_analysis_hive_cloud_adapter_unconfigured():
    """Verify HiveImageAdapter handles missing API key cleanly without failure."""
    from backend.app.ml.image.hive_adapter import HiveImageAdapter

    adapter = HiveImageAdapter(api_key=None)
    assert not adapter.is_configured

    res = await adapter.analyze_image(b"fake_bytes", "test.png")
    assert not res.is_configured
    assert res.status == "CONFIGURATION_REQUIRED"
    assert "not configured" in res.error_message.lower()
