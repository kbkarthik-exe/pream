"""Unit and integration tests for AICF Phase 3 Stage 3.2: Unified Image Analysis Pipeline.

All tests utilize mock-isolated detector fixtures to ensure rapid, deterministic
execution in < 1 second without loading large PyTorch vision models.
Verifies multi-dimensional orchestration, single PIL decode reuse, failure isolation,
and strict independence invariants.
"""

from __future__ import annotations

import io
import json
import struct
import hashlib
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PIL import Image

from backend.app.ml.image.detector import ImageForensicsDetector
from backend.app.ml.image.forensics.schemas import ConfidenceType, ManipulationVerdict
from backend.app.ml.image.forensics.security_hardening import ImageSecurityException
from backend.app.ml.image.generator_attribution import GeneratorAttributionResult
from backend.app.ml.image.unified_pipeline import (
    DimensionAResult,
    DimensionBResult,
    AttributionResult,
    UnifiedAnalysisResult,
    UnifiedImagePipeline,
)


def create_test_image(width: int = 64, height: int = 64, fmt: str = "JPEG") -> bytes:
    """Generate in-memory valid image bytes for pipeline testing."""
    arr = np.random.randint(40, 220, (height, width, 3), dtype=np.uint8)
    img = Image.fromarray(arr, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def create_crafted_png_ihdr(width: int, height: int) -> bytes:
    """Create a synthetic PNG stream with specific IHDR width/height without raster payload."""
    png_magic = b"\x89PNG\r\n\x1a\n"
    ihdr_type = b"IHDR"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr_crc = b"\x00\x00\x00\x00"
    ihdr_chunk = struct.pack(">I", 13) + ihdr_type + ihdr_data + ihdr_crc
    return png_magic + ihdr_chunk + b"\x00" * 32


MOCK_DETECTOR_OUTPUT = {
    "status": "SUCCESS",
    "classification": "LIKELY AI-GENERATED",
    "confidence_score": 0.88,
    "ai_probability": 0.88,
    "human_probability": 0.12,
    "raw_score": 0.88,
    "model_name": "Swin-B+ViT",
    "model_version": "2.0.0",
    "detector_scores": [{"detector": "Swin-B", "score": 0.89}, {"detector": "ViT", "score": 0.87}],
    "ensemble": {"consensus_score": 0.88, "confidence": 0.88},
    "heatmap": {"overlay_base64": "data:image/png;base64,mock"},
    "fft_features": {"high_freq_ratio": 0.32, "spectral_anisotropy": 0.18},
    "noise_features": {"noise_variance": 8.5},
    "evidence": [{"signal": "NOISE", "metric": "0.32", "finding": "High-frequency artifacts"}],
    "limitations": ["Mocked test response"],
}


# -------------------------------------------------------------------------
# 1. Pipeline Initialization & Normal Flow
# -------------------------------------------------------------------------

def test_01_orchestrator_initialization_defaults():
    """Test 1: Orchestrator instantiates cleanly with default detector."""
    pipeline = UnifiedImagePipeline()
    assert pipeline.detector is not None


def test_02_orchestrator_successful_valid_jpeg():
    """Test 2: Valid JPEG runs all 3 dimensions successfully."""
    raw_bytes = create_test_image(64, 64, "JPEG")
    mock_det = MagicMock(spec=ImageForensicsDetector)
    mock_det.analyze_image_bytes.return_value = MOCK_DETECTOR_OUTPUT

    pipeline = UnifiedImagePipeline(detector=mock_det)
    result = pipeline.analyze(raw_bytes, file_name="sample.jpg")

    assert isinstance(result, UnifiedAnalysisResult)
    assert result.overall_status == "SUCCESS"
    assert result.image_format == "JPEG"
    assert result.dimension_a.status == "SUCCESS"
    assert result.dimension_a.classification == "LIKELY AI-GENERATED"
    assert result.dimension_a.ai_probability == 0.88
    assert result.attribution.status == "SUCCESS"
    assert result.dimension_b.status == "SUCCESS"
    assert result.total_processing_time_ms > 0.0
    mock_det.analyze_image_bytes.assert_called_once_with(raw_bytes, file_name="sample.jpg")


def test_03_orchestrator_successful_valid_png():
    """Test 3: Valid PNG runs all 3 dimensions successfully."""
    raw_bytes = create_test_image(64, 64, "PNG")
    mock_det = MagicMock(spec=ImageForensicsDetector)
    mock_det.analyze_image_bytes.return_value = MOCK_DETECTOR_OUTPUT

    pipeline = UnifiedImagePipeline(detector=mock_det)
    result = pipeline.analyze(raw_bytes, file_name="sample.png")

    assert result.overall_status == "SUCCESS"
    assert result.image_format == "PNG"
    assert result.dimension_a.status == "SUCCESS"
    assert result.dimension_b.status == "SUCCESS"


def test_04_orchestrator_successful_valid_webp():
    """Test 4: Valid WebP runs all 3 dimensions successfully."""
    raw_bytes = create_test_image(64, 64, "WEBP")
    mock_det = MagicMock(spec=ImageForensicsDetector)
    mock_det.analyze_image_bytes.return_value = MOCK_DETECTOR_OUTPUT

    pipeline = UnifiedImagePipeline(detector=mock_det)
    result = pipeline.analyze(raw_bytes, file_name="sample.webp")

    assert result.overall_status == "SUCCESS"
    assert result.image_format == "WEBP"


# -------------------------------------------------------------------------
# 2. Strict Independence Invariant Tests (Non-Negotiable Rules)
# -------------------------------------------------------------------------

def test_05_dimension_decoupling_splicing_does_not_affect_p_ai():
    """Test 5: Invariant Rule 1 — Dimension B splicing finding CANNOT alter Dimension A P(AI)."""
    raw_bytes = create_test_image(64, 64, "JPEG")
    mock_det = MagicMock(spec=ImageForensicsDetector)
    # Detector reports human image (P(AI) = 0.05)
    human_output = dict(MOCK_DETECTOR_OUTPUT, classification="LIKELY HUMAN", ai_probability=0.05, confidence_score=0.95)
    mock_det.analyze_image_bytes.return_value = human_output

    pipeline = UnifiedImagePipeline(detector=mock_det)

    # Force Dimension B to simulate a massive splicing finding
    with patch("backend.app.ml.image.unified_pipeline.run_forensic_investigation") as mock_forensics:
        mock_report = MagicMock()
        mock_report.manipulation_verdict = ManipulationVerdict.SUSPECTED_SPLICING.value
        mock_report.confidence = 0.99
        mock_report.heuristic_score = 0.99
        mock_report.confidence_type = "HEURISTIC_SCORE"
        mock_report.evidence_strength = "DEFINITIVE"
        mock_report.findings = []
        mock_report.suspicious_regions = []
        mock_report.metadata_summary = ""
        mock_report.provenance_summary = ""
        mock_report.disclaimers = []
        mock_forensics.return_value = mock_report

        result = pipeline.analyze(raw_bytes)

        # Dimension B reports splicing
        assert result.dimension_b.manipulation_verdict == ManipulationVerdict.SUSPECTED_SPLICING.value
        # Invariant check: Dimension A P(AI) remains exactly 0.05, classification remains LIKELY HUMAN
        assert result.dimension_a.ai_probability == 0.05
        assert result.dimension_a.classification == "LIKELY HUMAN"


def test_06_dimension_decoupling_absence_of_seams_does_not_affect_p_ai():
    """Test 6: Invariant Rule 3 — Absence of seams does NOT imply AI synthesis or authentic reality."""
    raw_bytes = create_test_image(64, 64, "JPEG")
    mock_det = MagicMock(spec=ImageForensicsDetector)
    # Detector reports AI generated (P(AI) = 0.92)
    ai_output = dict(MOCK_DETECTOR_OUTPUT, classification="LIKELY AI-GENERATED", ai_probability=0.92)
    mock_det.analyze_image_bytes.return_value = ai_output

    pipeline = UnifiedImagePipeline(detector=mock_det)

    # Forensics reports clean image with zero manipulation seams
    with patch("backend.app.ml.image.unified_pipeline.run_forensic_investigation") as mock_forensics:
        mock_report = MagicMock()
        mock_report.manipulation_verdict = ManipulationVerdict.NO_MANIPULATION_EVIDENCE_DETECTED.value
        mock_report.confidence = 0.85
        mock_report.heuristic_score = 0.85
        mock_report.confidence_type = "HEURISTIC_SCORE"
        mock_report.evidence_strength = "NONE"
        mock_report.findings = []
        mock_report.suspicious_regions = []
        mock_report.metadata_summary = ""
        mock_report.provenance_summary = ""
        mock_report.disclaimers = []
        mock_forensics.return_value = mock_report

        result = pipeline.analyze(raw_bytes)

        assert result.dimension_b.manipulation_verdict == ManipulationVerdict.NO_MANIPULATION_EVIDENCE_DETECTED.value
        # Invariant check: Dimension A P(AI) remains 0.92
        assert result.dimension_a.ai_probability == 0.92
        assert result.dimension_a.classification == "LIKELY AI-GENERATED"


def test_07_dimension_decoupling_attribution_does_not_affect_p_ai():
    """Test 7: Invariant Rule 2 — Generator attribution CANNOT overwrite Dimension A P(AI)."""
    raw_bytes = create_test_image(64, 64, "JPEG")
    mock_det = MagicMock(spec=ImageForensicsDetector)
    # Detector reports inconclusive (P(AI) = 0.50)
    inconclusive_output = dict(MOCK_DETECTOR_OUTPUT, classification="INCONCLUSIVE", ai_probability=0.50, confidence_score=0.50)
    mock_det.analyze_image_bytes.return_value = inconclusive_output

    pipeline = UnifiedImagePipeline(detector=mock_det)

    # Force attribution to find Midjourney
    with patch("backend.app.ml.image.unified_pipeline.attribute_generator") as mock_attr:
        mock_res = GeneratorAttributionResult(
            primary_generator="MIDJOURNEY",
            confidence=0.99,
            evidence_tier="METADATA_CLUES",
            metadata_findings={"software_tag": "Midjourney"},
            limitations=[],
        )
        mock_attr.return_value = mock_res

        result = pipeline.analyze(raw_bytes)

        assert result.attribution.generator_name == "MIDJOURNEY"
        assert result.attribution.primary_generator == "MIDJOURNEY"
        # Invariant check: Dimension A P(AI) is NOT forced to 1.0; remains independently 0.50
        assert result.dimension_a.ai_probability == 0.50
        assert result.dimension_a.classification == "INCONCLUSIVE"


# -------------------------------------------------------------------------
# 3. Image Lifecycle & Sharing
# -------------------------------------------------------------------------

def test_08_single_decode_pil_image_shared_between_attribution_and_forensics():
    """Test 8: Verify attribution and forensics receive the exact same loaded PIL Image instance."""
    raw_bytes = create_test_image(64, 64, "PNG")
    mock_det = MagicMock(spec=ImageForensicsDetector)
    mock_det.analyze_image_bytes.return_value = MOCK_DETECTOR_OUTPUT

    pipeline = UnifiedImagePipeline(detector=mock_det)

    captured_attr_image = []
    captured_forensic_image = []

    def spy_attribute(image, raw_bytes, file_name=None):
        captured_attr_image.append(image)
        return GeneratorAttributionResult(
            primary_generator="UNKNOWN",
            confidence=0.0,
            evidence_tier="NONE",
            limitations=[],
        )

    def spy_forensics(image, raw_bytes):
        captured_forensic_image.append(image)
        mock_rep = MagicMock()
        mock_rep.manipulation_verdict = ManipulationVerdict.NO_MANIPULATION_EVIDENCE_DETECTED.value
        mock_rep.confidence = 0.0
        mock_rep.heuristic_score = 0.0
        mock_rep.confidence_type = "HEURISTIC_SCORE"
        mock_rep.evidence_strength = "NONE"
        mock_rep.findings = []
        mock_rep.suspicious_regions = []
        mock_rep.metadata_summary = ""
        mock_rep.provenance_summary = ""
        mock_rep.disclaimers = []
        return mock_rep

    with patch("backend.app.ml.image.unified_pipeline.attribute_generator", side_effect=spy_attribute), \
         patch("backend.app.ml.image.unified_pipeline.run_forensic_investigation", side_effect=spy_forensics):
        pipeline.analyze(raw_bytes)

    assert len(captured_attr_image) == 1
    assert len(captured_forensic_image) == 1
    assert captured_attr_image[0] is not None
    # Both received the exact same object reference in memory
    assert captured_attr_image[0] is captured_forensic_image[0]


def test_09_c2pa_signed_manifest_does_not_claim_visual_authenticity():
    """Test 9: Invariant Rule 5 — C2PA valid signature cert does NOT certify factual visual truth."""
    raw_bytes = create_test_image(64, 64, "JPEG")
    mock_det = MagicMock(spec=ImageForensicsDetector)
    mock_det.analyze_image_bytes.return_value = MOCK_DETECTOR_OUTPUT

    pipeline = UnifiedImagePipeline(detector=mock_det)

    with patch("backend.app.ml.image.unified_pipeline.run_forensic_investigation") as mock_forensics:
        mock_report = MagicMock()
        mock_report.manipulation_verdict = ManipulationVerdict.NO_MANIPULATION_EVIDENCE_DETECTED.value
        mock_report.confidence = 0.5
        mock_report.heuristic_score = 0.5
        mock_report.confidence_type = "HEURISTIC_SCORE"
        mock_report.evidence_strength = "NONE"
        mock_report.findings = []
        mock_report.suspicious_regions = []
        mock_report.metadata_summary = ""
        mock_report.provenance_summary = ""
        mock_report.disclaimers = [
            "Absence of manipulation seams does NOT prove an image is authentic or fully AI-synthesized.",
            "Confidence values represent uncalibrated heuristic rule-tier scores and are NOT calibrated statistical probabilities.",
        ]
        mock_forensics.return_value = mock_report

        result = pipeline.analyze(raw_bytes)

        # Disclaimers must be preserved
        assert any("probabilities" in d.lower() for d in result.dimension_b.disclaimers)
        assert any("authentic" in d.lower() for d in result.dimension_b.disclaimers)


def test_10_heuristic_score_explicitly_labeled():
    """Test 10: Invariant Rule 4 — Dimension B confidence_type is permanently 'HEURISTIC_SCORE'."""
    raw_bytes = create_test_image(64, 64, "JPEG")
    mock_det = MagicMock(spec=ImageForensicsDetector)
    mock_det.analyze_image_bytes.return_value = MOCK_DETECTOR_OUTPUT

    pipeline = UnifiedImagePipeline(detector=mock_det)
    result = pipeline.analyze(raw_bytes)

    assert result.dimension_b.confidence_type == ConfidenceType.HEURISTIC_SCORE.value
    assert result.dimension_b.confidence_type == "HEURISTIC_SCORE"
    assert result.dimension_b.confidence_type != "CALIBRATED_PROBABILITY"


# -------------------------------------------------------------------------
# 4. Failure Isolation & Degradation Tests
# -------------------------------------------------------------------------

def test_11_dimension_a_failure_graceful_degradation():
    """Test 11: When Dimension A fails, Attribution and Dimension B still execute and return PARTIAL."""
    raw_bytes = create_test_image(64, 64, "JPEG")
    mock_det = MagicMock(spec=ImageForensicsDetector)
    mock_det.analyze_image_bytes.side_effect = RuntimeError("PyTorch GPU OOM or model crash")

    pipeline = UnifiedImagePipeline(detector=mock_det)
    result = pipeline.analyze(raw_bytes)

    # Pipeline does not crash
    assert result.overall_status == "PARTIAL"
    assert result.dimension_a.status == "FAILED"
    assert result.dimension_a.classification == "INCONCLUSIVE"
    assert result.dimension_a.ai_probability is None
    assert "PyTorch GPU OOM" in result.dimension_a.error
    # Attribution and Dimension B succeeded
    assert result.attribution.status == "SUCCESS"
    assert result.dimension_b.status == "SUCCESS"
    assert "dimension_a" in result.skipped_modules


def test_12_attribution_failure_graceful_degradation():
    """Test 12: When Attribution fails, Dimension A and Dimension B still execute and return PARTIAL."""
    raw_bytes = create_test_image(64, 64, "JPEG")
    mock_det = MagicMock(spec=ImageForensicsDetector)
    mock_det.analyze_image_bytes.return_value = MOCK_DETECTOR_OUTPUT

    pipeline = UnifiedImagePipeline(detector=mock_det)

    with patch("backend.app.ml.image.unified_pipeline.attribute_generator", side_effect=ValueError("Corrupted EXIF chunk")):
        result = pipeline.analyze(raw_bytes)

    assert result.overall_status == "PARTIAL"
    assert result.attribution.status == "FAILED"
    assert result.attribution.outcome == "UNKNOWN_OR_NATURAL"
    assert "Corrupted EXIF chunk" in result.attribution.error
    # Dimension A and B succeeded
    assert result.dimension_a.status == "SUCCESS"
    assert result.dimension_b.status == "SUCCESS"
    assert "generator_attribution" in result.skipped_modules


def test_13_dimension_b_failure_graceful_degradation():
    """Test 13: When Dimension B fails, Dimension A and Attribution still execute and return PARTIAL."""
    raw_bytes = create_test_image(64, 64, "JPEG")
    mock_det = MagicMock(spec=ImageForensicsDetector)
    mock_det.analyze_image_bytes.return_value = MOCK_DETECTOR_OUTPUT

    pipeline = UnifiedImagePipeline(detector=mock_det)

    with patch("backend.app.ml.image.unified_pipeline.run_forensic_investigation", side_effect=MemoryError("Array allocation error in CMFD")):
        result = pipeline.analyze(raw_bytes)

    assert result.overall_status == "PARTIAL"
    assert result.dimension_b.status == "FAILED"
    assert result.dimension_b.manipulation_verdict == ManipulationVerdict.INSUFFICIENT_EVIDENCE.value
    assert "Array allocation error" in result.dimension_b.error
    # Dimension A and Attribution succeeded
    assert result.dimension_a.status == "SUCCESS"
    assert result.attribution.status == "SUCCESS"
    assert "dimension_b" in result.skipped_modules


def test_14_combined_failure_all_dimensions_fail():
    """Test 14: When all dimensions fail, pipeline returns overall FAILED without crashing."""
    raw_bytes = create_test_image(64, 64, "JPEG")
    mock_det = MagicMock(spec=ImageForensicsDetector)
    mock_det.analyze_image_bytes.side_effect = RuntimeError("Detector crash")

    pipeline = UnifiedImagePipeline(detector=mock_det)

    with patch("backend.app.ml.image.unified_pipeline.attribute_generator", side_effect=RuntimeError("Attr crash")), \
         patch("backend.app.ml.image.unified_pipeline.run_forensic_investigation", side_effect=RuntimeError("Forensics crash")):
        result = pipeline.analyze(raw_bytes)

    assert result.overall_status == "FAILED"
    assert result.dimension_a.status == "FAILED"
    assert result.attribution.status == "FAILED"
    assert result.dimension_b.status == "FAILED"
    assert len(result.skipped_modules) == 3


# -------------------------------------------------------------------------
# 5. Security Gate Pre-Condition & Rejection
# -------------------------------------------------------------------------

def test_15_empty_bytes_rejected_before_downstream_calls():
    """Test 15: Empty bytes rejected by security gate; downstream modules NEVER invoked."""
    mock_det = MagicMock(spec=ImageForensicsDetector)
    pipeline = UnifiedImagePipeline(detector=mock_det)

    with patch("backend.app.ml.image.unified_pipeline.attribute_generator") as mock_attr, \
         patch("backend.app.ml.image.unified_pipeline.run_forensic_investigation") as mock_forensics:
        with pytest.raises(ImageSecurityException) as exc_info:
            pipeline.analyze(b"", file_name="empty.jpg")

        assert "empty" in str(exc_info.value).lower()
        mock_det.analyze_image_bytes.assert_not_called()
        mock_attr.assert_not_called()
        mock_forensics.assert_not_called()


def test_16_decompression_bomb_rejected_before_downstream_calls():
    """Test 16: Decompression bomb rejected by security gate; downstream modules NEVER invoked."""
    bomb_bytes = create_crafted_png_ihdr(10000, 10000)
    mock_det = MagicMock(spec=ImageForensicsDetector)
    pipeline = UnifiedImagePipeline(detector=mock_det)

    with patch("backend.app.ml.image.unified_pipeline.attribute_generator") as mock_attr, \
         patch("backend.app.ml.image.unified_pipeline.run_forensic_investigation") as mock_forensics:
        with pytest.raises(ImageSecurityException) as exc_info:
            pipeline.analyze(bomb_bytes, file_name="bomb.png")

        assert "decompression bomb" in str(exc_info.value).lower() or "exceeds" in str(exc_info.value).lower()
        mock_det.analyze_image_bytes.assert_not_called()
        mock_attr.assert_not_called()
        mock_forensics.assert_not_called()


# -------------------------------------------------------------------------
# 6. Serialization & SHA-256 Integrity
# -------------------------------------------------------------------------

def test_17_serialization_and_sha256_integrity():
    """Test 17: Result serializes to JSON-compatible dict and computes exact SHA-256."""
    raw_bytes = create_test_image(64, 64, "JPEG")
    expected_hash = hashlib.sha256(raw_bytes).hexdigest()

    mock_det = MagicMock(spec=ImageForensicsDetector)
    mock_det.analyze_image_bytes.return_value = MOCK_DETECTOR_OUTPUT

    pipeline = UnifiedImagePipeline(detector=mock_det)
    result = pipeline.analyze(raw_bytes, file_name="hash_test.jpg")

    assert result.file_hash == expected_hash
    res_dict = result.to_dict()
    assert isinstance(res_dict, dict)
    assert res_dict["file_hash"] == expected_hash

    # Confirm JSON-serializable
    json_str = json.dumps(res_dict)
    assert len(json_str) > 0
    assert "dimension_a" in res_dict
    assert "attribution" in res_dict
    assert "dimension_b" in res_dict
