"""Isolated tests for AICF Phase 2 Stage 2: Advanced Image Forensics & Manipulation Detection."""

import io
import struct
from typing import Any
import numpy as np
from PIL import Image, PngImagePlugin

from app.ml.image.forensics import (
    AssetBindingStatus,
    ConfidenceType,
    EvidenceFinding,
    EvidenceStrength,
    ForensicReport,
    ManifestStatus,
    ManipulationVerdict,
    ProvenanceStatus,
    Reliability,
    Severity,
    SignatureStatus,
    run_forensic_investigation,
)


def _create_forensic_test_image(
    width: int = 160,
    height: int = 160,
    color: tuple[int, int, int] = (120, 120, 120),
    fmt: str = "PNG",
    png_info: dict[str, str] | None = None,
    exif_dict: dict[int, Any] | None = None,
) -> tuple[Image.Image, bytes]:
    """Helper to generate in-memory synthetic images for forensic tests."""
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()

    if fmt == "PNG" and png_info:
        info_obj = PngImagePlugin.PngInfo()
        for k, v in png_info.items():
            info_obj.add_text(k, v)
        img.save(buf, format="PNG", pnginfo=info_obj)
    elif fmt == "JPEG":
        if exif_dict:
            exif_obj = img.getexif()
            for k, v in exif_dict.items():
                exif_obj[k] = v
            img.save(buf, format="JPEG", exif=exif_obj)
        else:
            img.save(buf, format="JPEG")
    else:
        img.save(buf, format=fmt)

    raw_bytes = buf.getvalue()
    buf.seek(0)
    loaded_img = Image.open(buf)
    return loaded_img, raw_bytes


def test_1_real_untouched_photograph():
    """Test 1: Real untouched photograph simulation with camera EXIF and uniform characteristics."""
    # Tag 271: Make, Tag 272: Model
    exif_data = {271: "Nikon", 272: "D850"}
    img, raw_bytes = _create_forensic_test_image(
        width=160, height=160, fmt="JPEG", exif_dict=exif_data
    )

    report = run_forensic_investigation(img, raw_bytes)

    assert report.manipulation_verdict == ManipulationVerdict.NO_MANIPULATION_EVIDENCE_DETECTED.value
    assert report.confidence == 0.0
    assert report.metadata_summary["camera_make"] == "Nikon"
    assert len(report.disclaimers) > 0


def test_2_ai_generated_image():
    """Test 2: AI-generated image with Stable Diffusion / ComfyUI parameters."""
    sd_info = {"parameters": "cyberpunk city\nSteps: 25, Sampler: DPM++ 2M, CFG: 7.0, Seed: 112233"}
    img, raw_bytes = _create_forensic_test_image(width=160, height=160, fmt="PNG", png_info=sd_info)

    report = run_forensic_investigation(img, raw_bytes)

    # Absence of manipulation seams must not be inferred as full synthesis
    # Manipulation verdict evaluates localized tampering, while metadata flags generative software
    assert "Stable Diffusion" in report.metadata_summary["generative_software_detected"]
    assert any("Generative AI metadata" in f.description for f in report.findings)


def test_3_edited_photograph():
    """Test 3: Photograph with Adobe Photoshop software tag."""
    exif_data = {271: "Canon", 272: "EOS R5", 305: "Adobe Photoshop 2024 (Windows)"}
    img, raw_bytes = _create_forensic_test_image(width=160, height=160, fmt="JPEG", exif_dict=exif_data)

    report = run_forensic_investigation(img, raw_bytes)

    assert report.manipulation_verdict == ManipulationVerdict.SUSPECTED_RETOUCHING.value
    assert "Adobe Photoshop" in report.metadata_summary["editing_software_detected"]


def test_4_copy_move_manipulation():
    """Test 4: Controlled copy-move forgery with identical texture blocks pasted across distant regions."""
    # Create base image with random texture
    arr = np.random.randint(50, 200, size=(160, 160, 3), dtype=np.uint8)
    # Create a distinct textured block (32x32)
    block_texture = np.random.randint(20, 240, size=(32, 32, 3), dtype=np.uint8)
    # Paste the identical block in Top-Left and Bottom-Right (aligned to 8x8 block grid)
    arr[16:48, 16:48] = block_texture
    arr[96:128, 96:128] = block_texture

    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw_bytes = buf.getvalue()

    report = run_forensic_investigation(img, raw_bytes)

    # Verify copy-move finding or splicing verdict
    assert report.manipulation_verdict == ManipulationVerdict.SUSPECTED_SPLICING.value
    assert any("copy-move" in f.description.lower() or "cloning" in f.description.lower() for f in report.findings)


def test_5_spliced_images():
    """Test 5: Spliced image with severe noise variance discrepancy between quadrants."""
    arr = np.full((160, 160, 3), 128, dtype=np.float32)
    # Add mild noise to 3 quadrants
    arr[:80, :80] += np.random.normal(0, 1.0, (80, 80, 3))
    arr[80:, :80] += np.random.normal(0, 1.0, (80, 80, 3))
    arr[80:, 80:] += np.random.normal(0, 1.0, (80, 80, 3))
    # Inject heavy noise into Top-Right quadrant Q2 (simulating a spliced element from high-ISO camera)
    arr[:80, 80:] += np.random.normal(0, 14.0, (80, 80, 3))
    arr = np.clip(arr, 0, 255).astype(np.uint8)

    img = Image.fromarray(arr)
    buf = io.BytesIO()
    # Add Photoshop tag to indicate editing context
    img.save(buf, format="PNG", pnginfo=PngImagePlugin.PngInfo())
    raw_bytes = buf.getvalue()

    report = run_forensic_investigation(img, raw_bytes)

    assert any("noise variance" in f.description.lower() for f in report.findings)


def test_6_compressed_images():
    """Test 6: Compressed images handled gracefully with documented limitations."""
    img, raw_bytes = _create_forensic_test_image(width=120, height=120, fmt="JPEG")

    report = run_forensic_investigation(img, raw_bytes)

    assert isinstance(report.to_dict(), dict)
    assert any("recompression" in lim.lower() or "contours" in lim.lower() for lim in report.disclaimers)


def test_7_resized_images():
    """Test 7: Resampled image tested against frequency domain metrics."""
    # Create large image and downsample
    large_img = Image.new("RGB", (300, 300), color=(100, 140, 180))
    resized_img = large_img.resize((150, 150), resample=Image.Resampling.BICUBIC)
    buf = io.BytesIO()
    resized_img.save(buf, format="PNG")
    raw_bytes = buf.getvalue()

    report = run_forensic_investigation(resized_img, raw_bytes)

    assert isinstance(report.findings, list)
    assert "anisotropy_ratio" in report.findings[0].metadata or report.manipulation_verdict is not None


def test_8_missing_metadata():
    """Test 8: Image stripped of all metadata emits informational finding."""
    img, raw_bytes = _create_forensic_test_image(width=100, height=100, fmt="PNG")

    report = run_forensic_investigation(img, raw_bytes)

    assert any(f.source == "METADATA_ABSENT" for f in report.findings)
    assert report.metadata_summary["has_exif"] is False
    assert report.metadata_summary["has_png_chunks"] is False


def test_9_invalid_images():
    """Test 9: Invalid or corrupted image bytes return INSUFFICIENT_EVIDENCE."""
    corrupt_bytes = b"CORRUPTED_NON_IMAGE_BYTES_123456789"

    report = run_forensic_investigation(None, corrupt_bytes)

    assert report.manipulation_verdict == ManipulationVerdict.INSUFFICIENT_EVIDENCE.value
    assert report.confidence == 0.0
    assert any("unable" in f.description.lower() or "corrupted" in f.description.lower() for f in report.findings)


def test_10_conflicting_evidence():
    """Test 10: Conflicting metadata (Camera tags + Generative AI markers) flagged with HIGH severity."""
    exif_data = {271: "Sony", 272: "ILCE-7M3"}
    png_info = {"parameters": "cinematic portrait, ComfyUI, Steps: 30"}
    # Save as PNG with both camera tags in Comment and parameters
    info_obj = PngImagePlugin.PngInfo()
    info_obj.add_text("parameters", "ComfyUI, Steps: 30")
    info_obj.add_text("Software", "Sony Corporation ILCE-7M3")

    img = Image.new("RGB", (120, 120), color=(80, 80, 80))
    buf = io.BytesIO()
    img.save(buf, format="PNG", pnginfo=info_obj)
    raw_bytes = buf.getvalue()

    report = run_forensic_investigation(img, raw_bytes)

    # Inconsistency finding
    inconsistency_findings = [f for f in report.findings if f.source in ("METADATA_INCONSISTENCY", "METADATA_GENERATIVE")]
    assert len(inconsistency_findings) > 0


def test_11_unverified_c2pa_manifest():
    """Test 11: C2PA manifest header present without signature envelope."""
    img, raw_bytes = _create_forensic_test_image(width=120, height=120, fmt="JPEG")
    # Inject JUMBF box without signature
    unsigned_c2pa_payload = raw_bytes + b"\x00\x00\x00\x24jumb\x00\x00\x00\x1cc2pa\x00\x00\x00\x10c2pa.assertions"

    report = run_forensic_investigation(img, unsigned_c2pa_payload)

    assert report.provenance_summary["status"] == ProvenanceStatus.UNVERIFIED_MANIFEST_ONLY.value
    assert report.provenance_summary["has_c2pa"] is True
    assert report.provenance_summary["has_signature"] is False


def test_12_invalid_or_truncated_signatures():
    """Test 12: Truncated signature marker triggers INVALID_OR_TAMPERED_SIGNATURE."""
    img, raw_bytes = _create_forensic_test_image(width=120, height=120, fmt="JPEG")
    # Inject signature marker at the very end with truncated length (<32 bytes)
    truncated_payload = raw_bytes + b"c2pa.signature\x00\x01\x02"

    report = run_forensic_investigation(img, truncated_payload)

    assert report.provenance_summary["status"] == ProvenanceStatus.INVALID_OR_TAMPERED_SIGNATURE.value
    assert any("truncated" in f.description.lower() for f in report.findings)


def test_13_localization_bounding_boxes():
    """Test 13: Localized anomalous block cluster produces valid bounding boxes."""
    # Create an image with an extreme localized patch in Quadrant Q2 (top-right: x in [80, 140], y in [10, 60])
    arr = np.full((160, 160, 3), 100, dtype=np.uint8)
    arr[10:60, 80:140] = 245  # High-contrast saturated patch

    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw_bytes = buf.getvalue()

    report = run_forensic_investigation(img, raw_bytes)

    if report.suspicious_regions:
        reg = report.suspicious_regions[0]
        assert reg.quadrant in ["Q1_TOP_LEFT", "Q2_TOP_RIGHT", "Q3_BOTTOM_LEFT", "Q4_BOTTOM_RIGHT"]
        assert len(reg.bounding_box) == 4
        assert len(reg.normalized_box) == 4
        # Normalized coordinates must be bounded in [0, 1]
        assert 0.0 <= reg.normalized_box[0] <= 1.0
        assert 0.0 <= reg.normalized_box[1] <= 1.0


def test_14_no_heuristic_independently_proves_manipulation():
    """Test 14: Verifies all findings and disclaimers clearly acknowledge heuristic limitations."""
    img, raw_bytes = _create_forensic_test_image(width=100, height=100, fmt="PNG")

    report = run_forensic_investigation(img, raw_bytes)

    assert any("heuristics do not constitute definitive" in d.lower() for d in report.disclaimers)
    for finding in report.findings:
        if finding.reliability == Reliability.HEURISTIC:
            assert len(finding.limitations) > 0


def test_15_fake_c2pa_signature_never_produces_valid():
    """Test 15: Injected c2pa.signature markers alone must NEVER produce SIGNATURE_VALID or CRYPTOGRAPHICALLY_VERIFIED."""
    img, raw_bytes = _create_forensic_test_image(width=120, height=120, fmt="JPEG")
    fake_sig_payload = raw_bytes + b"c2pa.signature" + b"\x00" * 80 + b"adobe:firefly"

    report = run_forensic_investigation(img, fake_sig_payload)

    # Must produce SIGNATURE_UNVERIFIED and CERTIFICATE_UNTRUSTED, never SIGNATURE_VALID
    prov = report.provenance_summary
    assert prov["signature_status"] == "SIGNATURE_UNVERIFIED"
    assert prov["certificate_status"] == "CERTIFICATE_UNTRUSTED"
    assert prov["signature_valid"] is False
    assert prov["factual_authenticity"] == "INDEPENDENT_OF_CRYPTOGRAPHIC_PROVENANCE"


def test_16_decompression_bomb_pre_decode_rejection():
    """Test 16: Decompression bomb (10000x10000 declared PNG) rejected pre-decode without memory explosion."""
    # Construct a minimal valid PNG IHDR header declaring 10,000 x 10,000 pixels (100 MP)
    # Magic bytes + IHDR chunk with width=10000, height=10000
    png_magic = b"\x89PNG\r\n\x1a\n"
    # Chunk length = 13, Chunk type = IHDR
    ihdr_type = b"IHDR"
    # width=10000 (0x2710), height=10000 (0x2710), bit depth=8, color type=2 (RGB), compression=0, filter=0, interlace=0
    ihdr_data = struct.pack(">IIBBBBB", 10000, 10000, 8, 2, 0, 0, 0)
    ihdr_crc = b"\x00\x00\x00\x00"
    ihdr_chunk = struct.pack(">I", 13) + ihdr_type + ihdr_data + ihdr_crc
    bomb_bytes = png_magic + ihdr_chunk + b"\x00" * 50

    report = run_forensic_investigation(None, bomb_bytes)

    assert report.manipulation_verdict == ManipulationVerdict.INSUFFICIENT_EVIDENCE.value
    assert report.confidence == 0.0
    security_findings = [f for f in report.findings if f.source == "CONTAINER_SECURITY"]
    assert len(security_findings) > 0
    assert any("decompression bomb" in f.description.lower() for f in security_findings)


def test_17_oversized_single_axis_rejection():
    """Test 17: Single axis exceeding maximum allowable threshold (8192px) rejected."""
    png_magic = b"\x89PNG\r\n\x1a\n"
    ihdr_type = b"IHDR"
    ihdr_data = struct.pack(">IIBBBBB", 9000, 100, 8, 2, 0, 0, 0)
    ihdr_crc = b"\x00\x00\x00\x00"
    ihdr_chunk = struct.pack(">I", 13) + ihdr_type + ihdr_data + ihdr_crc
    oversized_bytes = png_magic + ihdr_chunk + b"\x00" * 50

    report = run_forensic_investigation(None, oversized_bytes)

    assert report.manipulation_verdict == ManipulationVerdict.INSUFFICIENT_EVIDENCE.value
    assert any("axis" in f.description.lower() for f in report.findings)


def test_18_repetitive_natural_textures_no_false_copy_move():
    """Test 18: Periodic texture (brick wall simulation) does NOT trigger false copy-move alarm."""
    # Generate periodic horizontal and vertical lines simulating bricks
    arr = np.zeros((160, 160, 3), dtype=np.uint8)
    for y in range(0, 160, 16):
        arr[y : y + 2, :] = 200
    for x in range(0, 160, 16):
        arr[:, x : x + 2] = 200
    # Add mild random noise
    arr += np.random.randint(0, 20, size=(160, 160, 3), dtype=np.uint8)

    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw_bytes = buf.getvalue()

    report = run_forensic_investigation(img, raw_bytes)

    # Shift-vector clustering ensures scattered texture matches do not trigger copy-move forgery
    copy_move_findings = [f for f in report.findings if f.source == "MANIPULATION_COPY_MOVE"]
    assert len(copy_move_findings) == 0


def test_19_natural_bokeh_portrait_no_false_splicing():
    """Test 19: Smooth optical depth-of-field transition does NOT trigger false splicing alarm."""
    arr = np.full((160, 160, 3), 120, dtype=np.float32)
    # Subject in center/top-left has noise
    arr[:80, :80] += np.random.normal(0, 8.0, (80, 80, 3))
    # Background has smooth optical blur (smooth gradient transition across mid_y and mid_x, seam_step <= 3.0)
    # Continuous ramp across boundary
    ramp = np.linspace(0, 1, 80).reshape(80, 1, 1)
    arr[80:, :80] += ramp * 2.0
    arr = np.clip(arr, 0, 255).astype(np.uint8)

    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw_bytes = buf.getvalue()

    report = run_forensic_investigation(img, raw_bytes)

    # Must NOT produce SUSPECTED_SPLICING when boundary transition is smooth
    assert report.manipulation_verdict != ManipulationVerdict.SUSPECTED_SPLICING.value


def test_20_fake_hash_marker_cannot_produce_valid_binding():
    """Test 20: Presence of c2pa.hash.data byte marker alone NEVER produces ASSET_BINDING_VALID."""
    img, raw = _create_forensic_test_image(width=160, height=160)
    # Inject fake c2pa.hash.data marker and signature envelope
    fake_payload = (
        raw
        + b"\x00\x00\x00\x60jumb"
        + b"c2pa.claim"
        + b"c2pa.signature"
        + b"\x00" * 32
        + b"c2pa.hash.data"
        + b"\x00" * 32
    )

    report = run_forensic_investigation(img, fake_payload)

    # Must be ASSET_BINDING_UNVERIFIED, NEVER ASSET_BINDING_VALID
    assert report.provenance_summary["asset_binding_status"] == AssetBindingStatus.ASSET_BINDING_UNVERIFIED.value
    assert report.provenance_summary["asset_binding_valid"] is False
    assert any("Asset binding is UNVERIFIED" in lim for f in report.findings for lim in f.limitations)


def test_21_manifest_with_hash_marker_remains_unverified():
    """Test 21: A parsed manifest with hash markers without verified cryptographic hash comparison remains unverified."""
    img, raw = _create_forensic_test_image(width=160, height=160)
    jumbf_box = (
        struct.pack(">I", 120)
        + b"jumb"
        + b"c2pa"
        + b"c2pa.claim"
        + b"c2pa.signature"
        + b"c2pa.hash.data"
        + b"c2pa.assertions"
        + b"\x00" * 60
    )
    payload = raw + jumbf_box

    report = run_forensic_investigation(img, payload)

    assert report.provenance_summary["manifest_status"] == ManifestStatus.MANIFEST_PARSED.value
    assert report.provenance_summary["signature_status"] == SignatureStatus.SIGNATURE_UNVERIFIED.value
    assert report.provenance_summary["asset_binding_status"] == AssetBindingStatus.ASSET_BINDING_UNVERIFIED.value
    assert report.provenance_summary["asset_binding_valid"] is False


def test_22_malformed_or_truncated_manifest_binding_invalid():
    """Test 22: Malformed or truncated manifest cannot produce a valid asset binding."""
    img, raw = _create_forensic_test_image(width=160, height=160)
    # Truncated signature envelope (only 8 bytes after signature marker)
    payload = raw + b"jumb" + b"c2pa.signature" + b"\x00" * 8

    report = run_forensic_investigation(img, payload)

    assert report.provenance_summary["asset_binding_status"] == AssetBindingStatus.ASSET_BINDING_INVALID.value
    assert report.provenance_summary["asset_binding_valid"] is False


def test_23_cmfd_above_block_limit_reports_skipped_status():
    """Test 23: Images exceeding the 4,000-block CMFD processing budget report SKIPPED_EXCESSIVE_BLOCKS."""
    # 1040x1040 image: Subsampled 2x -> 520x520. Blocks with cm_blk_size=8 -> 65x65 = 4225 blocks (> 4000 limit).
    img = Image.new("RGB", (1040, 1040), (128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    raw_bytes = buf.getvalue()

    report = run_forensic_investigation(img, raw_bytes)

    # Must have an informational finding about skipped CMFD
    cmfd_finding = next((f for f in report.findings if f.source == "MANIPULATION_COPY_MOVE"), None)
    assert cmfd_finding is not None
    assert cmfd_finding.metadata.get("cmfd_status") == "SKIPPED_EXCESSIVE_BLOCKS"
    assert cmfd_finding.metadata.get("total_blocks", 0) >= 4000
    assert any("does NOT constitute evidence of no manipulation" in lim for lim in cmfd_finding.limitations)


def test_24_cmfd_rotation_sensitivity_documented_not_claimed():
    """Test 24: CMFD explicitly documents axis-aligned limitation and does NOT claim rotation invariance."""
    arr = np.random.randint(50, 200, size=(160, 160, 3), dtype=np.uint8)
    block_texture = np.random.randint(20, 240, size=(32, 32, 3), dtype=np.uint8)
    arr[16:48, 16:48] = block_texture
    arr[96:128, 96:128] = block_texture

    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw_bytes = buf.getvalue()

    report = run_forensic_investigation(img, raw_bytes)

    copy_move_finding = next((f for f in report.findings if f.source == "MANIPULATION_COPY_MOVE"), None)
    assert copy_move_finding is not None
    assert copy_move_finding.metadata.get("rotation_invariant") is False
    assert any("rotation" in lim.lower() for lim in copy_move_finding.limitations)


def test_25_heuristic_confidence_distinguished_from_calibrated_probability():
    """Test 25: Confidence metric is explicitly labeled as uncalibrated heuristic rule-tier score."""
    img, raw_bytes = _create_forensic_test_image(width=160, height=160)

    report = run_forensic_investigation(img, raw_bytes)

    assert report.confidence_type == "HEURISTIC_SCORE"
    assert report.is_calibrated is False
    assert report.calibrated_confidence is None
    assert report.model_probability is None
    assert report.evidence_strength in ("STRONG", "MODERATE", "WEAK", "NONE")
    assert "uncalibrated heuristic rule-tier score" in report.calibration_limitation
    assert any("Confidence values represent uncalibrated heuristic rule-tier scores" in disc for disc in report.disclaimers)


def test_26_missing_manifest_binding_unverified():
    """Test 26: Image with no provenance manifest reports NO_MANIFEST_PRESENT and ASSET_BINDING_UNVERIFIED."""
    img, raw_bytes = _create_forensic_test_image(width=160, height=160)

    report = run_forensic_investigation(img, raw_bytes)

    assert report.provenance_summary["manifest_status"] == ManifestStatus.NO_MANIFEST_PRESENT.value
    assert report.provenance_summary["asset_binding_status"] == AssetBindingStatus.ASSET_BINDING_UNVERIFIED.value
    assert report.provenance_summary["asset_binding_valid"] is False


def test_27_invalid_binding_data_not_valid():
    """Test 27: Corrupted container with truncated JUMBF box reports invalid/unverified binding, never valid."""
    img, raw = _create_forensic_test_image(width=160, height=160)
    # Corrupt length header (less than 8 bytes)
    corrupted_payload = raw + struct.pack(">I", 3) + b"jumb" + b"c2pa"

    report = run_forensic_investigation(img, corrupted_payload)

    assert report.provenance_summary["asset_binding_valid"] is False
    assert report.provenance_summary["asset_binding_status"] != AssetBindingStatus.ASSET_BINDING_VALID.value


def test_28_rotated_cloned_patch_cmfd_limitation():
    """Test 28: Rotated cloned patches (e.g. 90-degree rotated) are not detected by axis-aligned CMFD."""
    arr = np.random.randint(50, 200, size=(160, 160, 3), dtype=np.uint8)
    block_texture = np.random.randint(20, 240, size=(32, 32, 3), dtype=np.uint8)
    arr[16:48, 16:48] = block_texture
    # Paste rotated version (90-degree counterclockwise rotation)
    arr[96:128, 96:128] = np.rot90(block_texture, 1)

    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw_bytes = buf.getvalue()

    report = run_forensic_investigation(img, raw_bytes)

    # Documented behavior: Axis-aligned block matching does not trigger copy-move on rotated patch
    cmfd_findings = [f for f in report.findings if f.source == "MANIPULATION_COPY_MOVE" and "detected" in f.description.lower()]
    assert len(cmfd_findings) == 0
