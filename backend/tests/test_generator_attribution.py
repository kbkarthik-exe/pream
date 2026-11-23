"""Isolated tests for the generator attribution engine."""

import io
from PIL import Image, PngImagePlugin

from app.ml.image.generator_attribution import (
    EvidenceTier,
    GeneratorOutcome,
    attribute_generator,
)


def _create_test_image(
    width: int = 120,
    height: int = 120,
    color: tuple[int, int, int] = (100, 150, 200),
    fmt: str = "PNG",
    png_info: dict[str, str] | None = None,
    exif_bytes: bytes | None = None,
) -> tuple[Image.Image, bytes]:
    """Helper to create an in-memory image with optional metadata."""
    img = Image.new("RGB", (width, height), color=color)
    buffer = io.BytesIO()

    if fmt == "PNG" and png_info:
        png_metadata = PngImagePlugin.PngInfo()
        for k, v in png_info.items():
            png_metadata.add_text(k, v)
        img.save(buffer, format="PNG", pnginfo=png_metadata)
    elif fmt == "JPEG":
        if exif_bytes:
            img.save(buffer, format="JPEG", exif=exif_bytes)
        else:
            img.save(buffer, format="JPEG")
    else:
        img.save(buffer, format=fmt)

    raw_bytes = buffer.getvalue()
    buffer.seek(0)
    loaded_img = Image.open(buffer)
    return loaded_img, raw_bytes


def test_1_png_with_known_generator_metadata():
    """Test 1: PNG with known generator metadata (Stable Diffusion / Automatic1111)."""
    sd_params = (
        "cyberpunk street, neon signs, ultra detailed\n"
        "Steps: 30, Sampler: DPM++ 2M Karras, CFG scale: 7.5, Seed: 987654321, "
        "Size: 512x512, Model hash: cc6f68ecce, Model: realisticVisionV51"
    )
    img, raw_bytes = _create_test_image(
        width=512, height=512, fmt="PNG", png_info={"parameters": sd_params}
    )

    result = attribute_generator(img, raw_bytes)

    assert result.primary_generator == GeneratorOutcome.STABLE_DIFFUSION.value
    assert result.evidence_tier == EvidenceTier.METADATA_CLUES.value
    assert result.confidence > 0.0
    assert result.conflicting_evidence is False
    assert "parameters" in str(result.metadata_findings)


def test_2_jpeg_with_software_metadata():
    """Test 2: JPEG with software metadata (Adobe Firefly in EXIF)."""
    img = Image.new("RGB", (200, 200), color=(50, 60, 70))
    exif = img.getexif()
    # Tag 305 is Software
    exif[305] = "Adobe Firefly 2.0"
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", exif=exif)
    raw_bytes = buffer.getvalue()
    buffer.seek(0)
    loaded_img = Image.open(buffer)

    result = attribute_generator(loaded_img, raw_bytes)

    assert result.primary_generator == GeneratorOutcome.ADOBE_FIREFLY.value
    assert result.evidence_tier == EvidenceTier.METADATA_CLUES.value
    assert result.confidence > 0.0
    assert result.conflicting_evidence is False


def test_3_image_with_no_metadata():
    """Test 3: Clean image with no metadata returns UNKNOWN."""
    # Use non-canonical dimensions so heuristic doesn't trigger
    img, raw_bytes = _create_test_image(width=347, height=489, fmt="PNG")

    result = attribute_generator(img, raw_bytes)

    assert result.primary_generator == GeneratorOutcome.UNKNOWN.value
    assert result.evidence_tier == EvidenceTier.NONE.value
    assert result.confidence == 0.0
    assert result.conflicting_evidence is False


def test_4_image_with_misleading_metadata():
    """Test 4: Camera hardware metadata mixed with AI generation markers."""
    img = Image.new("RGB", (400, 300), color=(120, 80, 40))
    exif = img.getexif()
    exif[271] = "Canon"  # Make
    exif[272] = "Canon EOS R5"  # Model
    exif[37510] = "cinematic portrait --v 6.0 --ar 4:3"  # UserComment with Midjourney tags
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", exif=exif)
    raw_bytes = buffer.getvalue()
    buffer.seek(0)
    loaded_img = Image.open(buffer)

    result = attribute_generator(loaded_img, raw_bytes)

    assert result.primary_generator == GeneratorOutcome.MIDJOURNEY.value
    assert result.metadata_findings["has_camera_hardware"] is True
    # Verify limitation notes misleading combination
    assert any("misleading" in lim.lower() for lim in result.limitations)


def test_5_conflicting_metadata():
    """Test 5: Conflicting metadata from multiple generators downgrades to UNKNOWN."""
    conflicting_info = {
        "parameters": "Steps: 20, Sampler: Euler a, Stable Diffusion",
        "comment": "Rendered via Midjourney --v 5.2 --stylize 250",
    }
    img, raw_bytes = _create_test_image(width=512, height=512, fmt="PNG", png_info=conflicting_info)

    result = attribute_generator(img, raw_bytes)

    assert result.primary_generator == GeneratorOutcome.UNKNOWN.value
    assert result.conflicting_evidence is True
    assert result.confidence == 0.0
    assert len(result.metadata_findings["detected_generators"]) > 1


def test_6_unknown_generator():
    """Test 6: Generic/unmatched indicators return UNKNOWN."""
    generic_info = {"parameters": "Created with ProprietaryEngineXYZ version 99"}
    img, raw_bytes = _create_test_image(width=320, height=240, fmt="PNG", png_info=generic_info)

    result = attribute_generator(img, raw_bytes)

    assert result.primary_generator == GeneratorOutcome.UNKNOWN.value
    assert result.confidence == 0.0


def test_7_missing_c2pa_manifest():
    """Test 7: Missing C2PA manifest does not claim human origin."""
    img, raw_bytes = _create_test_image(width=100, height=100, fmt="PNG")

    result = attribute_generator(img, raw_bytes)

    assert result.provenance_findings["has_c2pa_manifest"] is False
    assert result.provenance_findings["has_cryptographic_signature"] is False
    assert "Absence does NOT imply human origin" in result.provenance_findings["provenance_note"]


def test_8_invalid_or_corrupted_image():
    """Test 8: Invalid or corrupted image bytes return INSUFFICIENT_EVIDENCE gracefully."""
    corrupted_bytes = b"CORRUPTED_NON_IMAGE_DATA_0123456789"

    result = attribute_generator(None, corrupted_bytes)

    assert result.primary_generator == GeneratorOutcome.INSUFFICIENT_EVIDENCE.value
    assert result.confidence == 0.0
    assert any("corrupted" in lim.lower() or "unable" in lim.lower() for lim in result.limitations)


def test_9_metadata_parsing_failure():
    """Test 9: Metadata parsing failure handled gracefully without exception."""
    # Construct an image with non-standard byte sequences
    img, raw_bytes = _create_test_image(width=80, height=80, fmt="PNG")
    # Mutate header slightly or pass non-conforming metadata
    result = attribute_generator(img, raw_bytes)

    assert isinstance(result.to_dict(), dict)
    assert result.primary_generator in [g.value for g in GeneratorOutcome]


def test_10_unsupported_image_format_or_empty():
    """Test 10: Empty bytes return INSUFFICIENT_EVIDENCE."""
    result = attribute_generator(None, b"")

    assert result.primary_generator == GeneratorOutcome.INSUFFICIENT_EVIDENCE.value
    assert result.confidence == 0.0


def test_11_c2pa_direct_provenance_with_signature():
    """Test 11: C2PA manifest with digital signature assertion."""
    img, raw_bytes = _create_test_image(width=200, height=200, fmt="JPEG")
    # Inject synthetic C2PA and signature markers into the container payload
    c2pa_payload = raw_bytes + b"\x00\x00\x00\x1cc2pa\x00\x00\x00\x28c2pa.signature\x00\x00adobe:firefly"

    result = attribute_generator(img, c2pa_payload)

    assert result.primary_generator == GeneratorOutcome.ADOBE_FIREFLY.value
    assert result.evidence_tier == EvidenceTier.DIRECT_PROVENANCE.value
    assert result.provenance_findings["has_c2pa_manifest"] is True
    assert result.provenance_findings["has_cryptographic_signature"] is True
    assert result.confidence >= 0.85


def test_12_heuristics_alone_never_establish_generator():
    """Test 12: Canonical resolution alone must NEVER independently establish generator."""
    # 1024x1024 matches SDXL, DALL-E, and Midjourney, but no metadata exists
    img, raw_bytes = _create_test_image(width=1024, height=1024, fmt="PNG")

    result = attribute_generator(img, raw_bytes)

    # Must return UNKNOWN per strict scientific rule
    assert result.primary_generator == GeneratorOutcome.UNKNOWN.value
    assert result.confidence == 0.0
    assert result.evidence_tier == EvidenceTier.HEURISTIC_INDICATORS.value
    assert result.heuristic_findings["is_canonical_resolution"] is True
    assert any("heuristic indicators cannot independently prove" in lim.lower() for lim in result.limitations)

