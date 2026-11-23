"""Focused security tests for AICF Phase 3 Stage 3.1: Secure Image Ingestion Gate.

Covers pre-decode sniffing, decompression bomb rejection, boundary limits,
format validation, leak prevention, and mock-isolated detector gating.
"""

from __future__ import annotations

import io
import re
import struct
import tempfile
from unittest.mock import patch

import numpy as np
import pytest
from httpx import AsyncClient
from PIL import Image

from backend.app.core.config import settings
from backend.app.ml.image import image_detector
from backend.app.ml.image.forensics.security_hardening import (
    DEFAULT_MAX_DIMENSION,
    DEFAULT_MAX_PIXELS,
    sniff_image_dimensions_pre_decode,
    validate_image_security,
)


def create_minimal_image(width: int = 64, height: int = 64, fmt: str = "JPEG") -> bytes:
    """Generate in-memory valid image bytes for testing."""
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


MOCK_DETECTOR_SUCCESS = {
    "file_hash": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    "file_name": "test.jpg",
    "file_size_bytes": 1024,
    "image_width": 64,
    "image_height": 64,
    "image_format": "JPEG",
    "model_name": "Swin-B+ViT",
    "model_version": "2.0.0",
    "classification": "LIKELY HUMAN",
    "confidence_score": 0.95,
    "ai_probability": 0.05,
    "human_probability": 0.95,
    "raw_score": 0.05,
    "status": "SUCCESS",
    "processing_time_ms": 1.25,
    "evidence": [{"signal": "NOISE", "finding": "Natural sensor pattern", "metric": "0.10"}],
    "provenance": {"has_exif": False, "has_ai_metadata": False, "has_c2pa": False},
    "fft_features": {"high_freq_ratio": 0.15, "spectral_anisotropy": 0.05},
    "noise_features": {"noise_variance": 12.0},
    "detector_scores": [],
    "ensemble": None,
    "heatmap": None,
    "limitations": ["Mocked test response for security gate isolation"],
}


async def get_analyst_cookies(client: AsyncClient, suffix: str = "sec") -> dict[str, str]:
    """Register and authenticate an analyst session for security testing."""
    payload = {
        "email": f"sec_analyst_{suffix}@aicf.internal",
        "username": f"sec_analyst_{suffix}",
        "password": "SecurePassword123!",
        "full_name": f"Security Analyst {suffix}",
    }
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201
    return {settings.COOKIE_NAME: resp.cookies[settings.COOKIE_NAME]}


# -------------------------------------------------------------------------
# 1. Valid Image Ingestion & Detector Gating Tests
# -------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_01_valid_jpeg_ingestion_reaches_detector(client: AsyncClient):
    """Test 1: Valid JPEG passes security gate and invokes detector."""
    cookies = await get_analyst_cookies(client, "01")
    client.cookies = cookies
    img_bytes = create_minimal_image(64, 64, "JPEG")

    with patch.object(image_detector, "analyze_image_bytes", return_value=MOCK_DETECTOR_SUCCESS) as mock_det:
        resp = await client.post(
            "/api/v1/image/analyze",
            files={"file": ("test.jpg", img_bytes, "image/jpeg")},
        )
        assert resp.status_code == 200
        mock_det.assert_called_once()


@pytest.mark.asyncio
async def test_02_valid_png_ingestion_reaches_detector(client: AsyncClient):
    """Test 2: Valid PNG passes security gate and invokes detector."""
    cookies = await get_analyst_cookies(client, "02")
    client.cookies = cookies
    img_bytes = create_minimal_image(64, 64, "PNG")

    with patch.object(image_detector, "analyze_image_bytes", return_value=MOCK_DETECTOR_SUCCESS) as mock_det:
        resp = await client.post(
            "/api/v1/image/analyze",
            files={"file": ("test.png", img_bytes, "image/png")},
        )
        assert resp.status_code == 200
        mock_det.assert_called_once()


@pytest.mark.asyncio
async def test_03_valid_webp_reaches_detector(client: AsyncClient):
    """Test 3: Valid WebP passes security gate and invokes detector."""
    cookies = await get_analyst_cookies(client, "03")
    client.cookies = cookies
    img_bytes = create_minimal_image(64, 64, "WEBP")

    with patch.object(image_detector, "analyze_image_bytes", return_value=MOCK_DETECTOR_SUCCESS) as mock_det:
        resp = await client.post(
            "/api/v1/image/analyze",
            files={"file": ("test.webp", img_bytes, "image/webp")},
        )
        assert resp.status_code == 200
        mock_det.assert_called_once()


# -------------------------------------------------------------------------
# 2. File Signature & Container Bypass Rejection Tests
# -------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_04_empty_file_rejected_before_detector(client: AsyncClient):
    """Test 4: Empty byte stream is rejected at security gate without invoking detector."""
    cookies = await get_analyst_cookies(client, "04")
    client.cookies = cookies

    with patch.object(image_detector, "analyze_image_bytes") as mock_det:
        resp = await client.post(
            "/api/v1/image/analyze",
            files={"file": ("empty.jpg", b"", "image/jpeg")},
        )
        assert resp.status_code == 422
        assert "empty" in resp.json()["detail"].lower()
        mock_det.assert_not_called()


@pytest.mark.asyncio
async def test_05_oversized_upload_rejected_before_detector(client: AsyncClient, monkeypatch):
    """Test 5: Oversized file stream is rejected before decoding or inference."""
    cookies = await get_analyst_cookies(client, "05")
    client.cookies = cookies
    monkeypatch.setattr(settings, "IMAGE_MAX_SIZE_BYTES", 500)
    img_bytes = create_minimal_image(64, 64, "JPEG")  # > 500 bytes

    with patch.object(image_detector, "analyze_image_bytes") as mock_det:
        resp = await client.post(
            "/api/v1/image/analyze",
            files={"file": ("large.jpg", img_bytes, "image/jpeg")},
        )
        assert resp.status_code == 422
        assert "exceeds maximum" in resp.json()["detail"].lower()
        mock_det.assert_not_called()


@pytest.mark.asyncio
async def test_06_fake_jpeg_disguised_text_rejected(client: AsyncClient):
    """Test 6: Plain text file named as JPEG is rejected without invoking detector."""
    cookies = await get_analyst_cookies(client, "06")
    client.cookies = cookies
    fake_bytes = b"This is not a real image, it is a shell script disguised as JPEG."

    with patch.object(image_detector, "analyze_image_bytes") as mock_det:
        resp = await client.post(
            "/api/v1/image/analyze",
            files={"file": ("payload.jpg", fake_bytes, "image/jpeg")},
        )
        assert resp.status_code == 422
        assert "corrupted" in resp.json()["detail"].lower() or "not a recognized image" in resp.json()["detail"].lower()
        mock_det.assert_not_called()


@pytest.mark.asyncio
async def test_07_fake_png_disguised_garbage_rejected(client: AsyncClient):
    """Test 7: Arbitrary binary garbage named as PNG is rejected safely."""
    cookies = await get_analyst_cookies(client, "07")
    client.cookies = cookies
    garbage_bytes = b"\x00\x01\x02\x03\x04\x05\x06\x07" * 32

    with patch.object(image_detector, "analyze_image_bytes") as mock_det:
        resp = await client.post(
            "/api/v1/image/analyze",
            files={"file": ("exploit.png", garbage_bytes, "image/png")},
        )
        assert resp.status_code == 422
        mock_det.assert_not_called()


@pytest.mark.asyncio
async def test_08_mime_type_mismatch_validated_by_content(client: AsyncClient):
    """Test 8: Client specifies incorrect MIME type (claims PNG, sends JPEG); real content is validated."""
    cookies = await get_analyst_cookies(client, "08")
    client.cookies = cookies
    real_jpeg = create_minimal_image(64, 64, "JPEG")

    with patch.object(image_detector, "analyze_image_bytes", return_value=MOCK_DETECTOR_SUCCESS) as mock_det:
        resp = await client.post(
            "/api/v1/image/analyze",
            files={"file": ("mismatched.jpg", real_jpeg, "image/png")},
        )
        assert resp.status_code == 200
        mock_det.assert_called_once()


@pytest.mark.asyncio
async def test_09_extension_mismatch_validated_by_content(client: AsyncClient):
    """Test 9: File extension says .jpg but payload is valid PNG; validated safely."""
    cookies = await get_analyst_cookies(client, "09")
    client.cookies = cookies
    real_png = create_minimal_image(64, 64, "PNG")

    with patch.object(image_detector, "analyze_image_bytes", return_value=MOCK_DETECTOR_SUCCESS) as mock_det:
        resp = await client.post(
            "/api/v1/image/analyze",
            files={"file": ("disguised.jpg", real_png, "image/jpeg")},
        )
        assert resp.status_code == 200
        mock_det.assert_called_once()


# -------------------------------------------------------------------------
# 3. Truncation, Corruption, & Decompression Bomb Tests
# -------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_10_truncated_jpeg_stream_rejected(client: AsyncClient):
    """Test 10: Truncated JPEG stream (SOI without frames) rejected safely."""
    cookies = await get_analyst_cookies(client, "10")
    client.cookies = cookies
    truncated_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01"

    with patch.object(image_detector, "analyze_image_bytes") as mock_det:
        resp = await client.post(
            "/api/v1/image/analyze",
            files={"file": ("truncated.jpg", truncated_bytes, "image/jpeg")},
        )
        assert resp.status_code == 422
        mock_det.assert_not_called()


@pytest.mark.asyncio
async def test_11_corrupted_raster_body_rejected(client: AsyncClient):
    """Test 11: Valid header with corrupted body rejected safely."""
    cookies = await get_analyst_cookies(client, "11")
    client.cookies = cookies
    corrupted_bytes = b"\xff\xd8\xff\xe0" + b"\xde\xad\xbe\xef" * 64

    with patch.object(image_detector, "analyze_image_bytes") as mock_det:
        resp = await client.post(
            "/api/v1/image/analyze",
            files={"file": ("corrupt.jpg", corrupted_bytes, "image/jpeg")},
        )
        assert resp.status_code == 422
        mock_det.assert_not_called()


@pytest.mark.asyncio
async def test_12_decompression_bomb_pre_decode_ihdr_rejected(client: AsyncClient):
    """Test 12: Crafted 10,000x10,000 PNG IHDR is rejected before raster decode."""
    cookies = await get_analyst_cookies(client, "12")
    client.cookies = cookies
    bomb_bytes = create_crafted_png_ihdr(10000, 10000)

    with patch.object(image_detector, "analyze_image_bytes") as mock_det:
        resp = await client.post(
            "/api/v1/image/analyze",
            files={"file": ("bomb.png", bomb_bytes, "image/png")},
        )
        assert resp.status_code == 422
        detail = resp.json()["detail"].lower()
        assert "decompression bomb" in detail or "exceeds" in detail
        mock_det.assert_not_called()


@pytest.mark.asyncio
async def test_13_excessive_single_axis_width_rejected(client: AsyncClient):
    """Test 13: Single axis width exceeding 8192px rejected at security gate."""
    cookies = await get_analyst_cookies(client, "13")
    client.cookies = cookies
    oversized_bytes = create_crafted_png_ihdr(9000, 100)

    with patch.object(image_detector, "analyze_image_bytes") as mock_det:
        resp = await client.post(
            "/api/v1/image/analyze",
            files={"file": ("wide.png", oversized_bytes, "image/png")},
        )
        assert resp.status_code == 422
        detail = resp.json()["detail"].lower()
        assert "axis" in detail or "exceeds" in detail
        mock_det.assert_not_called()


@pytest.mark.asyncio
async def test_14_excessive_single_axis_height_rejected(client: AsyncClient):
    """Test 14: Single axis height exceeding 8192px rejected at security gate."""
    cookies = await get_analyst_cookies(client, "14")
    client.cookies = cookies
    tall_bytes = create_crafted_png_ihdr(100, 9000)

    with patch.object(image_detector, "analyze_image_bytes") as mock_det:
        resp = await client.post(
            "/api/v1/image/analyze",
            files={"file": ("tall.png", tall_bytes, "image/png")},
        )
        assert resp.status_code == 422
        mock_det.assert_not_called()


# -------------------------------------------------------------------------
# 4. Security Leaks & Information Exposure Defenses
# -------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_15_rejection_responses_contain_no_memory_addresses(client: AsyncClient):
    """Test 15: Error responses must never leak Python memory addresses (0x...)."""
    cookies = await get_analyst_cookies(client, "15")
    client.cookies = cookies
    bad_bytes = b"NotAnImageBytes"

    resp = await client.post(
        "/api/v1/image/analyze",
        files={"file": ("bad.jpg", bad_bytes, "image/jpeg")},
    )
    assert resp.status_code == 422
    body = resp.text
    # Verify no hex memory pointers like 0x0000024384DDC770
    assert not re.search(r"0x[0-9a-fA-F]{6,16}", body)
    assert "_io.BytesIO" not in body


@pytest.mark.asyncio
async def test_16_rejection_responses_contain_no_internal_paths(client: AsyncClient):
    """Test 16: Error responses must never leak server file paths or code traces."""
    cookies = await get_analyst_cookies(client, "16")
    client.cookies = cookies
    bad_bytes = b"\xff\xd8\xff" + b"Corrupted"

    resp = await client.post(
        "/api/v1/image/analyze",
        files={"file": ("leak_check.jpg", bad_bytes, "image/jpeg")},
    )
    assert resp.status_code == 422
    body = resp.text
    assert "Traceback" not in body
    assert "site-packages" not in body
    assert "backend/app" not in body
    assert "C:\\" not in body


@pytest.mark.asyncio
async def test_17_no_temp_file_leakage_after_rejection(client: AsyncClient):
    """Test 17: Rejected uploads must not leave lingering temporary files."""
    cookies = await get_analyst_cookies(client, "17")
    client.cookies = cookies
    bad_bytes = b"CorruptedBytes" * 20

    temp_dir = tempfile.gettempdir()
    import os
    before_files = set(os.listdir(temp_dir))

    resp = await client.post(
        "/api/v1/image/analyze",
        files={"file": ("temp_check.jpg", bad_bytes, "image/jpeg")},
    )
    assert resp.status_code == 422

    after_files = set(os.listdir(temp_dir))
    new_files = [f for f in (after_files - before_files) if "aicf" in f.lower()]
    assert len(new_files) == 0


# -------------------------------------------------------------------------
# 5. Direct Unit Tests on Security Hardening Engine
# -------------------------------------------------------------------------

def test_18_unit_pre_decode_dimension_sniffing():
    """Test 18: Dimension sniffer correctly parses PNG, JPEG, and WebP containers."""
    png_bytes = create_crafted_png_ihdr(640, 480)
    res_png = sniff_image_dimensions_pre_decode(png_bytes)
    assert res_png is not None
    assert res_png == (640, 480, "PNG")

    jpeg_bytes = create_minimal_image(320, 240, "JPEG")
    res_jpeg = sniff_image_dimensions_pre_decode(jpeg_bytes)
    assert res_jpeg is not None
    assert res_jpeg == (320, 240, "JPEG")

    short_bytes = b"\x00" * 10
    assert sniff_image_dimensions_pre_decode(short_bytes) is None


def test_19_unit_validate_image_security_telemetry_statuses():
    """Test 19: Direct telemetry status codes for various inputs."""
    # Safe image
    safe_bytes = create_minimal_image(64, 64, "PNG")
    is_safe, reason, tel = validate_image_security(safe_bytes)
    assert is_safe is True
    assert reason is None
    assert tel["status"] == "SAFE"

    # Empty stream
    is_safe, reason, tel = validate_image_security(b"")
    assert is_safe is False
    assert tel["status"] == "EMPTY_STREAM"

    # Decompression bomb
    bomb_bytes = create_crafted_png_ihdr(10000, 10000)
    is_safe, reason, tel = validate_image_security(bomb_bytes)
    assert is_safe is False
    assert tel["status"] == "DECOMPRESSION_BOMB_DETECTED"

    # Axis limit
    axis_bytes = create_crafted_png_ihdr(9000, 100)
    is_safe, reason, tel = validate_image_security(axis_bytes)
    assert is_safe is False
    assert tel["status"] == "AXIS_LIMIT_EXCEEDED"

    # Malformed header
    is_safe, reason, tel = validate_image_security(b"garbage" * 10)
    assert is_safe is False
    assert tel["status"] == "MALFORMED_HEADER"


def test_20_unit_unsupported_format_rejection():
    """Test 20: Formats other than JPEG, PNG, WEBP are cleanly flagged as UNSUPPORTED_FORMAT."""
    arr = np.zeros((32, 32), dtype=np.uint8)
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="GIF")
    gif_bytes = buf.getvalue()

    is_safe, reason, tel = validate_image_security(gif_bytes)
    assert is_safe is False
    assert tel["status"] == "UNSUPPORTED_FORMAT"
    assert "unsupported" in reason.lower()
