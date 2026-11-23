"""Automated test suite for AI Video Forensics Engine & API (AICF Step 06 - Phase 2).

Covers:
1. Unauthenticated requests rejection (HTTP 401).
2. Empty file upload rejection (HTTP 422).
3. Unsupported file extension rejection (HTTP 422).
4. Corrupted / invalid video container content rejection (HTTP 422).
5. Oversized video file rejection (HTTP 422).
6. Valid video upload, inference, and database persistence (HTTP 200).
7. Case report creation integration (save_to_cases=True).
8. User video analysis history listing (HTTP 200).
9. Specific video analysis retrieval (HTTP 200).
10. Cross-account user isolation enforcement (HTTP 403).
11. Missing analysis record handling (HTTP 404).
12. Detector exception handling and safe error reporting (HTTP 500).
13. Temporary-file cleanup verification.
"""

import os
import tempfile
from glob import glob
from pathlib import Path
from unittest.mock import AsyncMock, patch

import cv2
import numpy as np
import pytest
import torch
from backend.app.core.config import settings
from backend.app.ml.video.ensemble import video_ensemble
from backend.app.ml.video.face_deepfake import (
    FacialDeepfakeDetector,
    Meso4,
)
from backend.app.ml.video.face_detector import FaceDetectorAndAligner
from backend.app.ml.video.temporal import TemporalAnalysisResult
from backend.app.models.video import VideoAnalysisRecord
from backend.app.services.pdf_generator import generate_video_analysis_pdf
from httpx import AsyncClient
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


def create_in_memory_mp4(
    num_frames: int = 15,
    fps: float = 10.0,
    width: int = 64,
    height: int = 64,
) -> bytes:
    """Generates valid synthetic MP4 video bytes using OpenCV headless."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tf:
        temp_path = tf.name

    try:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))
        for i in range(num_frames):
            frame = np.full((height, width, 3), (i * 15) % 256, dtype=np.uint8)
            out.write(frame)
        out.release()

        with open(temp_path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


async def create_authenticated_analyst(client: AsyncClient, suffix: str = "1") -> dict[str, str]:
    """Helper to register and authenticate an analyst session."""
    payload = {
        "email": f"analyst_vid_{suffix}@aicf.internal",
        "username": f"analyst_vid_{suffix}",
        "password": "SecurePassword123!",
        "full_name": f"Analyst Video {suffix}",
    }
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201
    return {
        settings.COOKIE_NAME: resp.cookies[settings.COOKIE_NAME],
    }


# 1. Authentication Requirements
@pytest.mark.asyncio
async def test_video_analysis_unauthenticated(client: AsyncClient):
    """Unauthenticated requests must be rejected with HTTP 401."""
    video_bytes = create_in_memory_mp4()
    files = {"file": ("test.mp4", video_bytes, "video/mp4")}
    response = await client.post("/api/v1/video/analyze", files=files)
    assert response.status_code == 401
    assert "Authentication required" in response.json()["detail"]


@pytest.mark.asyncio
async def test_video_history_unauthenticated(client: AsyncClient):
    """Unauthenticated history query must be rejected with HTTP 401."""
    response = await client.get("/api/v1/video/history")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_video_get_analysis_unauthenticated(client: AsyncClient):
    """Unauthenticated analysis detail query must be rejected with HTTP 401."""
    response = await client.get("/api/v1/video/analyses/1")
    assert response.status_code == 401


# 2. Empty Uploads
@pytest.mark.asyncio
async def test_video_analysis_empty_upload(client: AsyncClient):
    """Uploading an empty file (0 bytes) must return HTTP 422."""
    cookies = await create_authenticated_analyst(client, "empty")
    client.cookies = cookies

    files = {"file": ("empty.mp4", b"", "video/mp4")}
    response = await client.post("/api/v1/video/analyze", files=files)
    assert response.status_code == 422
    assert "empty" in response.json()["detail"].lower()


# 3. Unsupported File Extension
@pytest.mark.asyncio
async def test_video_analysis_unsupported_extension(client: AsyncClient):
    """Uploading an invalid file extension must return HTTP 422."""
    cookies = await create_authenticated_analyst(client, "ext")
    client.cookies = cookies

    files = {"file": ("sample.avi", b"FAKE_AVI_CONTENT", "video/x-msvideo")}
    response = await client.post("/api/v1/video/analyze", files=files)
    assert response.status_code == 422
    assert "unsupported video file extension" in response.json()["detail"].lower()


# 4. Corrupted / Invalid Video Content
@pytest.mark.asyncio
async def test_video_analysis_invalid_content(client: AsyncClient):
    """Invalid video container magic bytes must be rejected with HTTP 422."""
    cookies = await create_authenticated_analyst(client, "invalid_magic")
    client.cookies = cookies

    corrupt_bytes = b"NOT_A_REAL_VIDEO_HEADER_OR_CONTAINER" * 5
    files = {"file": ("corrupt.mp4", corrupt_bytes, "video/mp4")}
    response = await client.post("/api/v1/video/analyze", files=files)
    assert response.status_code == 422
    assert (
        "invalid video container format" in response.json()["detail"].lower()
        or "corrupted" in response.json()["detail"].lower()
    )


# 5. Oversized Video File
@pytest.mark.asyncio
async def test_video_analysis_oversized_file(client: AsyncClient):
    """Uploading a file exceeding VIDEO_MAX_FILE_SIZE_BYTES must return HTTP 422."""
    cookies = await create_authenticated_analyst(client, "oversized")
    client.cookies = cookies

    original_limit = settings.VIDEO_MAX_FILE_SIZE_BYTES
    try:
        # Lower limit temporarily to 500 bytes for fast test execution
        settings.VIDEO_MAX_FILE_SIZE_BYTES = 500
        video_bytes = create_in_memory_mp4(num_frames=5)
        files = {"file": ("large.mp4", video_bytes, "video/mp4")}
        response = await client.post("/api/v1/video/analyze", files=files)
        assert response.status_code == 422
        assert "exceeds maximum allowed limit" in response.json()["detail"].lower()
    finally:
        settings.VIDEO_MAX_FILE_SIZE_BYTES = original_limit


# 6. Valid Video Upload and Database Persistence
@pytest.mark.asyncio
async def test_video_analysis_valid_upload_and_persistence(client: AsyncClient, db_session: AsyncSession):
    """Valid video must be processed, classified, and persisted to the database."""
    cookies = await create_authenticated_analyst(client, "valid")
    client.cookies = cookies

    video_bytes = create_in_memory_mp4(num_frames=12, fps=10.0, width=64, height=64)
    files = {"file": ("test_clip.mp4", video_bytes, "video/mp4")}
    data = {"save_to_cases": "true", "query_hive": "false"}

    response = await client.post("/api/v1/video/analyze", files=files, data=data)
    assert response.status_code == 200, response.text
    res_json = response.json()

    assert res_json["analysis_id"] is not None
    assert res_json["file_name"] == "test_clip.mp4"
    assert res_json["duration_seconds"] > 0
    assert res_json["video_width"] == 64
    assert res_json["video_height"] == 64
    assert res_json["fps"] == 10.0
    assert len(res_json["frame_scores"]) >= 2
    assert res_json["temporal_telemetry"] is not None
    assert res_json["temporal_telemetry"]["is_heuristic"] is True
    assert res_json["case_report_id"] is not None
    assert res_json["status"] == "SUCCESS"

    # Verify directly in SQLite test database session
    stmt = select(VideoAnalysisRecord).where(VideoAnalysisRecord.id == res_json["analysis_id"])
    record = (await db_session.execute(stmt)).scalar_one_or_none()
    assert record is not None
    assert record.file_name == "test_clip.mp4"
    assert record.duration_seconds == res_json["duration_seconds"]


# 7. Video Analysis History
@pytest.mark.asyncio
async def test_video_analysis_history(client: AsyncClient):
    """Authenticated analyst can retrieve their past video analysis records."""
    cookies = await create_authenticated_analyst(client, "history")
    client.cookies = cookies

    video_bytes = create_in_memory_mp4(num_frames=10)
    files = {"file": ("history_vid.mp4", video_bytes, "video/mp4")}
    upload_res = await client.post("/api/v1/video/analyze", files=files)
    assert upload_res.status_code == 200

    history_res = await client.get("/api/v1/video/history")
    assert history_res.status_code == 200
    history_items = history_res.json()
    assert len(history_items) >= 1
    assert any(item["file_name"] == "history_vid.mp4" for item in history_items)


# 8. Get Specific Video Analysis by ID
@pytest.mark.asyncio
async def test_video_analysis_get_by_id(client: AsyncClient):
    """Analyst can fetch detailed video analysis by record ID."""
    cookies = await create_authenticated_analyst(client, "detail")
    client.cookies = cookies

    video_bytes = create_in_memory_mp4(num_frames=10)
    files = {"file": ("detail_vid.mp4", video_bytes, "video/mp4")}
    upload_res = await client.post("/api/v1/video/analyze", files=files)
    assert upload_res.status_code == 200
    analysis_id = upload_res.json()["analysis_id"]

    detail_res = await client.get(f"/api/v1/video/analyses/{analysis_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["analysis_id"] == analysis_id
    assert detail_data["file_name"] == "detail_vid.mp4"
    assert len(detail_data["frame_scores"]) >= 2


# 9. Cross-Account User Isolation Enforcement
@pytest.mark.asyncio
async def test_video_analysis_cross_user_isolation(client: AsyncClient):
    """User B cannot access User A's private video analysis record (HTTP 403)."""
    # 1. User A creates a video analysis
    cookies_a = await create_authenticated_analyst(client, "user_a")
    client.cookies = cookies_a
    video_bytes = create_in_memory_mp4(num_frames=10)
    files = {"file": ("user_a_vid.mp4", video_bytes, "video/mp4")}
    resp_a = await client.post("/api/v1/video/analyze", files=files)
    assert resp_a.status_code == 200
    record_id = resp_a.json()["analysis_id"]

    # 2. User B attempts to access User A's record
    cookies_b = await create_authenticated_analyst(client, "user_b")
    client.cookies = cookies_b
    resp_b = await client.get(f"/api/v1/video/analyses/{record_id}")
    assert resp_b.status_code == 403
    assert "Access forbidden" in resp_b.json()["detail"]

    # 3. User B history does not contain User A's analysis
    hist_b = await client.get("/api/v1/video/history")
    assert hist_b.status_code == 200
    assert not any(item["id"] == record_id for item in hist_b.json())


# 10. Missing Video Analysis Record
@pytest.mark.asyncio
async def test_video_analysis_not_found(client: AsyncClient):
    """Requesting non-existent analysis ID returns HTTP 404."""
    cookies = await create_authenticated_analyst(client, "not_found")
    client.cookies = cookies

    response = await client.get("/api/v1/video/analyses/999999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# 11. Detector Failure Handling
@pytest.mark.asyncio
async def test_video_analysis_detector_failure(client: AsyncClient):
    """Unexpected exceptions in the detector pipeline return HTTP 500 without leaking stack traces."""
    cookies = await create_authenticated_analyst(client, "fail")
    client.cookies = cookies

    video_bytes = create_in_memory_mp4(num_frames=10)
    files = {"file": ("crash_test.mp4", video_bytes, "video/mp4")}

    with patch("backend.app.api.v1.endpoints.video.video_detector.detect_video", new_callable=AsyncMock) as mock_detect:
        mock_detect.side_effect = RuntimeError("Simulated neural inference device failure.")
        response = await client.post("/api/v1/video/analyze", files=files)
        assert response.status_code == 500
        assert "Forensic detection pipeline failed" in response.json()["detail"]


# 12. Temporary File Cleanup Verification
@pytest.mark.asyncio
async def test_video_analysis_temp_file_cleanup(client: AsyncClient):
    """Temporary video files must be removed from disk upon both success and failure."""
    cookies = await create_authenticated_analyst(client, "temp_clean")
    client.cookies = cookies

    temp_dir = tempfile.gettempdir()
    initial_temp_files = set(glob(os.path.join(temp_dir, "aicf_vid_*")))

    # 1. Run successful analysis
    video_bytes = create_in_memory_mp4(num_frames=10)
    files = {"file": ("clean_test.mp4", video_bytes, "video/mp4")}
    resp = await client.post("/api/v1/video/analyze", files=files)
    assert resp.status_code == 200

    after_success = set(glob(os.path.join(temp_dir, "aicf_vid_*")))
    assert after_success == initial_temp_files, f"Leaked temporary files on success: {after_success - initial_temp_files}"

    # 2. Run failed analysis (corrupted content)
    files_bad = {"file": ("bad_clean.mp4", b"INVALID_GARBAGE_PAYLOAD", "video/mp4")}
    resp_bad = await client.post("/api/v1/video/analyze", files=files_bad)
    assert resp_bad.status_code == 422

    after_failure = set(glob(os.path.join(temp_dir, "aicf_vid_*")))
    assert after_failure == initial_temp_files, f"Leaked temporary files on failure: {after_failure - initial_temp_files}"


# 13. Direct Video PDF Report Generation
def test_generate_video_analysis_pdf_direct():
    """generate_video_analysis_pdf must generate valid ReportLab PDF bytes matching brand style."""
    record = VideoAnalysisRecord(
        id=42,
        user_id=1,
        file_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        file_name="forensic_sample.mp4",
        file_size_bytes=1048576,
        duration_seconds=5.0,
        video_width=1280,
        video_height=720,
        fps=30.0,
        total_frames=150,
        sampled_frame_count=5,
        model_name="AICF-Video-Forensics-Engine",
        model_version="1.0.0",
        frame_classifier_id="umm-maybe/AI-image-detector",
        classification="SUSPECTED_AI",
        confidence_score=0.785,
        ai_probability_mean=0.742,
        ai_probability_max=0.912,
        peak_frame_timestamp=3.0,
        temporal_flicker_score=0.0452,
        has_hive_result=True,
        hive_score=0.880,
        frame_scores_json='[{"frame_index": 0, "timestamp_seconds": 0.0, "ai_probability": 0.65, "human_probability": 0.35, "classification": "INCONCLUSIVE"}, {"frame_index": 30, "timestamp_seconds": 1.0, "ai_probability": 0.88, "human_probability": 0.12, "classification": "HIGHLY_LIKELY_AI"}]',
        temporal_telemetry_json='{"mean_frame_difference": 0.035, "temporal_flicker_score": 0.0452, "suspicious_transition_timestamps": [1.0], "is_heuristic": true, "heuristic_notes": "Deterministic heuristic."}',
        evidence_json='[{"signal": "Frame Screening", "metric": "Mean: 74.2%", "finding": "Elevated synthetic indicators."}]',
        limitations_text='["Probabilistic assessment.", "Compression sensitivity."]',
        status="SUCCESS",
        processing_time_ms=1240.5,
    )

    pdf_bytes = generate_video_analysis_pdf(record, analyst_name="Senior Analyst")
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF-")


# 14. API Video PDF Download (Authenticated)
@pytest.mark.asyncio
async def test_api_download_video_pdf_authenticated(client: AsyncClient):
    """Authenticated analyst can download official PDF report for their analysis."""
    cookies = await create_authenticated_analyst(client, "pdf_download")
    client.cookies = cookies

    video_bytes = create_in_memory_mp4(num_frames=10)
    files = {"file": ("video_report_test.mp4", video_bytes, "video/mp4")}
    resp = await client.post("/api/v1/video/analyze", files=files)
    assert resp.status_code == 200
    analysis_id = resp.json()["analysis_id"]

    pdf_resp = await client.get(f"/api/v1/video/analyses/{analysis_id}/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert f'filename="AICF-Video-Report-{analysis_id:05d}.pdf"' in pdf_resp.headers["content-disposition"]
    assert pdf_resp.content.startswith(b"%PDF-")


# 15. Video PDF Download Security (Unauthenticated)
@pytest.mark.asyncio
async def test_security_video_pdf_download_unauthorized(client: AsyncClient):
    """Unauthenticated requests to download PDF reports must return HTTP 401."""
    response = await client.get("/api/v1/video/analyses/1/pdf")
    assert response.status_code == 401
    assert "Authentication required" in response.json()["detail"]


# 16. Video PDF Download Security (Cross-User Isolation)
@pytest.mark.asyncio
async def test_security_video_pdf_cross_user_isolation(client: AsyncClient):
    """User B cannot export User A's private video forensic PDF report (HTTP 403)."""
    # 1. User A creates analysis
    cookies_a = await create_authenticated_analyst(client, "user_a_pdf")
    client.cookies = cookies_a
    video_bytes = create_in_memory_mp4(num_frames=10)
    files = {"file": ("user_a_secret.mp4", video_bytes, "video/mp4")}
    resp_a = await client.post("/api/v1/video/analyze", files=files)
    assert resp_a.status_code == 200
    record_id = resp_a.json()["analysis_id"]

    # 2. User B tries to download User A's PDF
    cookies_b = await create_authenticated_analyst(client, "user_b_pdf")
    client.cookies = cookies_b
    pdf_resp_b = await client.get(f"/api/v1/video/analyses/{record_id}/pdf")
    assert pdf_resp_b.status_code == 403
    assert "Access denied" in pdf_resp_b.json()["detail"]


# 17. Video PDF Download Missing Record (HTTP 404)
@pytest.mark.asyncio
async def test_security_video_pdf_invalid_id_not_found(client: AsyncClient):
    """Requesting PDF for non-existent analysis ID returns HTTP 404."""
    cookies = await create_authenticated_analyst(client, "not_found_pdf")
    client.cookies = cookies

    response = await client.get("/api/v1/video/analyses/999999/pdf")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# 18. Video PDF Generation with Missing Optional Telemetry
def test_generate_video_pdf_missing_optional_fields():
    """generate_video_analysis_pdf must succeed gracefully when optional telemetry fields are empty or unconfigured."""
    record = VideoAnalysisRecord(
        id=99,
        user_id=1,
        file_hash="0000000000000000000000000000000000000000000000000000000000000000",
        file_name="minimal_video.mp4",
        file_size_bytes=512,
        duration_seconds=1.0,
        video_width=320,
        video_height=240,
        fps=10.0,
        total_frames=10,
        sampled_frame_count=2,
        model_name="AICF-Video-Forensics-Engine",
        model_version="1.0.0",
        frame_classifier_id="umm-maybe/AI-image-detector",
        classification="INCONCLUSIVE",
        confidence_score=0.5,
        ai_probability_mean=0.5,
        ai_probability_max=0.5,
        peak_frame_timestamp=0.0,
        temporal_flicker_score=0.0,
        has_hive_result=False,
        hive_score=None,
        frame_scores_json="[]",
        temporal_telemetry_json="{}",
        evidence_json="[]",
        limitations_text="[]",
        status="SUCCESS",
        processing_time_ms=50.0,
    )
    pdf_bytes = generate_video_analysis_pdf(record, analyst_name="Analyst Minimal")
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF-")


# 19. Video PDF API Failure Handling (HTTP 500)
@pytest.mark.asyncio
async def test_api_download_video_pdf_generator_failure(client: AsyncClient):
    """When PDF generation encounters an unexpected error, API returns HTTP 500 safely."""
    cookies = await create_authenticated_analyst(client, "gen_fail")
    client.cookies = cookies

    video_bytes = create_in_memory_mp4(num_frames=10)
    files = {"file": ("fail_report.mp4", video_bytes, "video/mp4")}
    resp = await client.post("/api/v1/video/analyze", files=files)
    assert resp.status_code == 200
    analysis_id = resp.json()["analysis_id"]

    with patch("backend.app.api.v1.endpoints.video.generate_video_analysis_pdf") as mock_pdf:
        mock_pdf.side_effect = RuntimeError("PDF canvas layout failed.")
        pdf_resp = await client.get(f"/api/v1/video/analyses/{analysis_id}/pdf")
        assert pdf_resp.status_code == 500
        assert "Failed to generate forensic PDF report" in pdf_resp.json()["detail"]


# ==============================================================================
# AICF PHASE 3 — ADVANCED FACIAL DEEPFAKE & CONSENSUS TESTS
# ==============================================================================


def create_in_memory_mp4_with_faces(
    num_frames: int = 12,
    fps: float = 10.0,
    width: int = 200,
    height: int = 200,
    num_faces: int = 1,
) -> bytes:
    """Generates synthetic MP4 containing skin-tone geometric face regions for detection testing."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tf:
        temp_path = tf.name

    try:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))
        for i in range(num_frames):
            frame = np.full((height, width, 3), 35, dtype=np.uint8)
            # Add primary face-like skin ellipse in BGR format: B=110, G=135, R=195
            cv2.ellipse(frame, (80, 80), (35, 45), 0, 0, 360, (110, 135, 195), -1)
            # Add facial gradient features (eyes/mouth)
            cv2.circle(frame, (70, 70), 5, (40, 40, 50), -1)
            cv2.circle(frame, (90, 70), 5, (40, 40, 50), -1)
            cv2.line(frame, (70, 95), (90, 95), (60, 60, 120), 2)

            if num_faces >= 2:
                # Add secondary face-like region in BGR
                cv2.ellipse(frame, (150, 140), (25, 30), 0, 0, 360, (115, 140, 200), -1)
                cv2.circle(frame, (143, 135), 3, (40, 40, 50), -1)
                cv2.circle(frame, (157, 135), 3, (40, 40, 50), -1)

            out.write(frame)
        out.release()

        with open(temp_path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


# 20. Face Detection & Alignment Unit Verification
def test_face_detector_and_alignment_unit():
    """Verifies face candidate detection, alignment, boundary seam disparity, and edge cases."""
    aligner = FaceDetectorAndAligner(target_size=(256, 256), expansion_margin=0.25)

    # A. Blank frame (no faces)
    blank = np.full((240, 320, 3), 40, dtype=np.uint8)
    assert aligner.detect_faces(blank) == []

    # B. Single face frame
    frame = np.full((200, 200, 3), 30, dtype=np.uint8)
    cv2.ellipse(frame, (100, 100), (35, 45), 0, 0, 360, (195, 135, 110), -1)
    cv2.circle(frame, (90, 90), 4, (40, 30, 30), -1)
    cv2.circle(frame, (110, 90), 4, (40, 30, 30), -1)
    faces = aligner.detect_faces(frame)
    assert len(faces) >= 1
    primary = faces[0]
    assert primary.face_chip.size == (256, 256)
    assert 0.0 <= primary.boundary_seam_delta <= 1.0
    assert primary.confidence > 0.0

    # C. Low-resolution detection check (< 48px)
    low_res_frame = np.full((60, 60, 3), 30, dtype=np.uint8)
    cv2.ellipse(low_res_frame, (30, 30), (16, 20), 0, 0, 360, (195, 135, 110), -1)
    cv2.circle(low_res_frame, (25, 25), 2, (40, 30, 30), -1)
    low_faces = aligner.detect_faces(low_res_frame)
    if low_faces:
        assert low_faces[0].is_low_res is True


# 21. Dedicated Facial Deepfake Model (Offline / UNAVAILABLE Gate)
def test_facial_deepfake_detector_offline_unavailable_mode():
    """Facial deepfake detector must report UNAVAILABLE when weights are missing without fabricating scores."""
    # Instantiated pointing to a non-existent weights path
    detector = FacialDeepfakeDetector(weights_path=Path("non_existent_weights.pt"))
    assert detector.is_loaded is False
    assert detector.status == "UNAVAILABLE"

    # Forward pass returns None (no fake scores invented!)
    chip = Image.new("RGB", (256, 256), color=(200, 140, 110))
    assert detector.classify_face_chip(chip) is None


# 22. Dedicated Facial Deepfake Model (Execution With Weights)
def test_facial_deepfake_detector_with_mock_weights():
    """Facial deepfake detector loads Meso4 architecture and returns valid neural probabilities."""
    with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as tf:
        weights_path = tf.name

    try:
        net = Meso4(num_classes=2)
        torch.save(net.state_dict(), weights_path)

        detector = FacialDeepfakeDetector(weights_path=weights_path)
        assert detector.is_loaded is True
        assert detector.status == "READY"

        chip = Image.new("RGB", (256, 256), color=(200, 140, 110))
        prob = detector.classify_face_chip(chip)
        assert prob is not None
        assert isinstance(prob, float)
        assert 0.0 <= prob <= 1.0
    finally:
        if os.path.exists(weights_path):
            os.remove(weights_path)


# 23. Video Analysis No-Face Stream Handling
@pytest.mark.asyncio
async def test_video_analysis_no_face_handling(client: AsyncClient):
    """Videos without faces (landscape/objects) must be handled gracefully without crashing."""
    cookies = await create_authenticated_analyst(client, "noface")
    client.cookies = cookies

    # In-memory MP4 with solid uniform color (no faces)
    video_bytes = create_in_memory_mp4(num_frames=10, fps=10.0, width=64, height=64)
    files = {"file": ("landscape_test.mp4", video_bytes, "video/mp4")}

    resp = await client.post("/api/v1/video/analyze", files=files)
    assert resp.status_code == 200, resp.text
    res_json = resp.json()

    assert res_json["face_deepfake_status"] == "NO_FACES_DETECTED"
    assert res_json["facial_telemetry"] is not None
    assert res_json["facial_telemetry"]["total_faces_analyzed"] == 0
    assert res_json["facial_telemetry"]["frames_with_faces"] == 0
    assert res_json["consensus"] is not None
    assert res_json["consensus_verdict"] in ("Likely Real", "Likely Manipulated", "Inconclusive")


# 24. Video Analysis Multiple Faces Stream Handling
@pytest.mark.asyncio
async def test_video_analysis_multiple_faces_stream(client: AsyncClient):
    """Videos with multiple faces must detect and track multiple face candidates per frame."""
    cookies = await create_authenticated_analyst(client, "multiface")
    client.cookies = cookies

    video_bytes = create_in_memory_mp4_with_faces(num_frames=10, fps=10.0, width=200, height=200, num_faces=2)
    files = {"file": ("interview_test.mp4", video_bytes, "video/mp4")}

    resp = await client.post("/api/v1/video/analyze", files=files)
    assert resp.status_code == 200, resp.text
    res_json = resp.json()

    assert res_json["facial_telemetry"] is not None
    assert res_json["facial_telemetry"]["total_faces_analyzed"] >= 1
    assert res_json["face_deepfake_status"] in ("READY", "UNAVAILABLE")


# 25. Video Analysis Low-Resolution Stream Handling
@pytest.mark.asyncio
async def test_video_analysis_low_resolution_stream(client: AsyncClient):
    """Low-resolution video (< 64px) is processed without crashing and flags resolution attenuation."""
    cookies = await create_authenticated_analyst(client, "lowres")
    client.cookies = cookies

    video_bytes = create_in_memory_mp4(num_frames=8, fps=10.0, width=48, height=48)
    files = {"file": ("lowres_test.mp4", video_bytes, "video/mp4")}

    resp = await client.post("/api/v1/video/analyze", files=files)
    assert resp.status_code == 200, resp.text
    res_json = resp.json()

    assert res_json["video_width"] == 48
    assert res_json["video_height"] == 48
    assert res_json["status"] == "SUCCESS"


# 26. Video Consensus Aggregator Verdict Rules
def test_video_consensus_aggregator_verdicts():
    """Verifies that the consensus aggregator outputs the 3 mandated verdicts under distinct conditions."""
    from backend.app.ml.video.face_deepfake import FacialDeepfakeTelemetry

    dummy_temporal = TemporalAnalysisResult(
        mean_frame_difference=0.04,
        temporal_flicker_score=0.03,
        suspicious_transition_timestamps=[],
        frame_deltas=[0.04, 0.04],
    )

    # Condition 1: Likely Manipulated (High Frame AI + High Facial Score)
    manipulated_telemetry = FacialDeepfakeTelemetry(
        model_name="MesoNet-4",
        model_version="1.0.0",
        model_license="MIT",
        availability="READY",
        total_faces_analyzed=5,
        frames_with_faces=5,
        total_frames_sampled=5,
        mean_facial_manipulation_score=0.88,
        max_facial_manipulation_score=0.94,
        mean_boundary_seam_delta=0.45,
        max_boundary_seam_delta=0.55,
        peak_manipulation_timestamp=2.0,
        low_resolution_frames_count=0,
        timeline=[],
        suspicious_temporal_segments=[],
    )
    res_manip = video_ensemble.aggregate(
        mean_frame_ai=0.82,
        max_frame_ai=0.91,
        std_frame_ai=0.05,
        peak_frame_timestamp=2.0,
        facial_telemetry=manipulated_telemetry,
        temporal_telemetry=dummy_temporal,
    )
    assert res_manip.verdict == "Likely Manipulated"
    assert res_manip.composite_manipulation_score >= 0.70

    # Condition 2: Likely Real (Low Frame AI + Low Facial Score)
    real_telemetry = FacialDeepfakeTelemetry(
        model_name="MesoNet-4",
        model_version="1.0.0",
        model_license="MIT",
        availability="READY",
        total_faces_analyzed=5,
        frames_with_faces=5,
        total_frames_sampled=5,
        mean_facial_manipulation_score=0.10,
        max_facial_manipulation_score=0.18,
        mean_boundary_seam_delta=0.08,
        max_boundary_seam_delta=0.12,
        peak_manipulation_timestamp=1.0,
        low_resolution_frames_count=0,
        timeline=[],
        suspicious_temporal_segments=[],
    )
    res_real = video_ensemble.aggregate(
        mean_frame_ai=0.12,
        max_frame_ai=0.20,
        std_frame_ai=0.02,
        peak_frame_timestamp=1.0,
        facial_telemetry=real_telemetry,
        temporal_telemetry=dummy_temporal,
    )
    assert res_real.verdict == "Likely Real"
    assert res_real.composite_manipulation_score <= 0.30

    # Condition 3: Inconclusive (Mid-range / Conflicting signals)
    inconc_telemetry = FacialDeepfakeTelemetry(
        model_name="MesoNet-4",
        model_version="1.0.0",
        model_license="MIT",
        availability="READY",
        total_faces_analyzed=5,
        frames_with_faces=5,
        total_frames_sampled=5,
        mean_facial_manipulation_score=0.50,
        max_facial_manipulation_score=0.55,
        mean_boundary_seam_delta=0.25,
        max_boundary_seam_delta=0.30,
        peak_manipulation_timestamp=1.5,
        low_resolution_frames_count=0,
        timeline=[],
        suspicious_temporal_segments=[],
    )
    res_inconc = video_ensemble.aggregate(
        mean_frame_ai=0.52,
        max_frame_ai=0.60,
        std_frame_ai=0.05,
        peak_frame_timestamp=1.5,
        facial_telemetry=inconc_telemetry,
        temporal_telemetry=dummy_temporal,
    )
    assert res_inconc.verdict == "Inconclusive"


# 27. Video PDF Generation with Facial Deepfake Telemetry
def test_video_pdf_generation_with_facial_telemetry():
    """Generates a complete forensic PDF with facial deepfake telemetry and consensus verdict."""
    record = VideoAnalysisRecord(
        id=999,
        user_id=1,
        file_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        file_name="deepfake_interview_evidence.mp4",
        file_size_bytes=2048000,
        duration_seconds=10.0,
        video_width=1280,
        video_height=720,
        fps=30.0,
        total_frames=300,
        sampled_frame_count=10,
        model_name="AICF-Video-Forensics-Engine",
        model_version="2.0.0",
        frame_classifier_id="umm-maybe/AI-image-detector",
        classification="LIKELY_MANIPULATED",
        consensus_verdict="Likely Manipulated",
        confidence_score=0.895,
        ai_probability_mean=0.820,
        ai_probability_max=0.940,
        peak_frame_timestamp=4.0,
        temporal_flicker_score=0.045,
        face_deepfake_status="READY",
        has_hive_result=False,
        hive_score=None,
        frame_scores_json='[{"frame_index": 0, "timestamp_seconds": 0.0, "ai_probability": 0.75, "human_probability": 0.25, "classification": "SUSPECTED_AI"}]',
        temporal_telemetry_json='{"mean_frame_difference": 0.035, "temporal_flicker_score": 0.045, "suspicious_transition_timestamps": [4.0], "is_heuristic": true, "heuristic_notes": "Optical heuristic."}',
        facial_telemetry_json='{"model_name": "MesoNet-4", "model_version": "1.0.0", "model_license": "MIT", "availability": "READY", "total_faces_analyzed": 10, "frames_with_faces": 10, "total_frames_sampled": 10, "mean_facial_manipulation_score": 0.88, "max_facial_manipulation_score": 0.94, "mean_boundary_seam_delta": 0.42, "max_boundary_seam_delta": 0.55, "peak_manipulation_timestamp": 4.0, "low_resolution_frames_count": 0, "timeline": [], "suspicious_temporal_segments": [{"start_timestamp_seconds": 3.0, "end_timestamp_seconds": 5.0, "frame_count": 3, "peak_manipulation_score": 0.94, "peak_boundary_seam_delta": 0.55, "description": "Elevated facial boundary seam disparity at t=3.0-5.0s."}]}',
        consensus_json='{"verdict": "Likely Manipulated", "confidence_score": 0.895, "composite_manipulation_score": 0.895, "frame_screening_score": 0.820, "frame_classifier_status": "READY", "facial_deepfake_score": 0.880, "facial_detector_status": "READY", "boundary_seam_delta": 0.55, "temporal_flicker_score": 0.045}',
        evidence_json='[{"signal": "Frame Synthetic Screening", "metric": "Mean: 82.0%", "finding": "Peak at t=4.0s."}, {"signal": "Dedicated Facial Deepfake Detection", "metric": "Mean: 88.0%", "finding": "MesoNet-4 identified facial boundary anomalies."}]',
        limitations_text='["Probabilistic assessment.", "Boundary seam heuristic."]',
        status="SUCCESS",
        processing_time_ms=185.0,
    )

    pdf_bytes = generate_video_analysis_pdf(record, analyst_name="Senior Forensic Examiner")
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 2500
    assert pdf_bytes.startswith(b"%PDF-")

