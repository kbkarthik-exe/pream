"""Pre-decode image security hardening: dimension limits, decompression bomb defenses, and header validation."""

from __future__ import annotations

import io
import struct
from typing import Any

from PIL import Image

# Enforce strict maximum resource limits
DEFAULT_MAX_PIXELS = 16_777_216  # 4096 x 4096 pixels (approx 16.7 MP)
DEFAULT_MAX_DIMENSION = 8192      # Absolute single-axis limit
DEFAULT_MAX_FILE_BYTES = 10_485_760  # 10 MB file stream limit

# Ensure Pillow security limits are strictly active (never disabled)
if hasattr(Image, "MAX_IMAGE_PIXELS"):
    Image.MAX_IMAGE_PIXELS = DEFAULT_MAX_PIXELS


class ImageSecurityException(ValueError):
    """Raised when an image payload violates security or resource constraints."""


def sniff_image_dimensions_pre_decode(raw_bytes: bytes) -> tuple[int, int, str] | None:
    """Extract width, height, and format from container headers without decompressing full raster pixels.

    Supports JPEG, PNG, and WebP pre-decode inspection.
    Returns (width, height, format) if parseable, or None.
    """
    if len(raw_bytes) < 30:
        return None

    # 1. PNG Header (IHDR chunk at fixed offset)
    if raw_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        if len(raw_bytes) >= 24 and raw_bytes[12:16] == b"IHDR":
            w, h = struct.unpack(">II", raw_bytes[16:24])
            return w, h, "PNG"

    # 2. JPEG Markers (SOF0, SOF2 markers containing height and width)
    if raw_bytes[:2] == b"\xff\xd8":
        idx = 2
        length = len(raw_bytes)
        while idx < length - 9:
            marker_start = raw_bytes.find(b"\xff", idx)
            if marker_start == -1 or marker_start >= length - 1:
                break
            marker = raw_bytes[marker_start + 1]
            idx = marker_start + 2

            # Baseline or Progressive DCT frame markers (SOF0 = 0xc0, SOF2 = 0xc2)
            if marker in (0xC0, 0xC1, 0xC2, 0xC3):
                if idx + 7 <= length:
                    h, w = struct.unpack(">HH", raw_bytes[idx + 3 : idx + 7])
                    return w, h, "JPEG"
                break
            elif marker in (0xD9, 0xDA):  # EOI or SOS (start of scan)
                break
            else:
                # Skip marker segment
                if idx + 2 <= length:
                    seg_len = struct.unpack(">H", raw_bytes[idx : idx + 2])[0]
                    idx += seg_len
                else:
                    break

    # 3. WebP Header (RIFF....WEBPVP8)
    if raw_bytes[:4] == b"RIFF" and raw_bytes[8:12] == b"WEBP":
        vp8_chunk = raw_bytes[12:16]
        if vp8_chunk == b"VP8 " and len(raw_bytes) >= 30:
            # VP8 lossy: 14-bit width and height at bytes 26..29
            w = struct.unpack("<H", raw_bytes[26:28])[0] & 0x3FFF
            h = struct.unpack("<H", raw_bytes[28:30])[0] & 0x3FFF
            return w, h, "WEBP"
        elif vp8_chunk == b"VP8L" and len(raw_bytes) >= 25:
            # VP8L lossless
            b0, b1, b2, b3 = raw_bytes[21:25]
            w = 1 + (((b1 & 0x3F) << 8) | b0)
            h = 1 + (((b3 & 0xF) << 10) | (b2 << 2) | ((b1 & 0xC0) >> 6))
            return w, h, "WEBP"

    return None


def validate_image_security(
    raw_bytes: bytes,
    max_pixels: int = DEFAULT_MAX_PIXELS,
    max_dimension: int = DEFAULT_MAX_DIMENSION,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
) -> tuple[bool, str | None, dict[str, Any]]:
    """Validate image stream against decompression bombs, resource exhaustion, and malformed headers.

    Returns:
        tuple of (is_safe: bool, rejection_reason: str | None, telemetry: dict)
    """
    if not raw_bytes or len(raw_bytes) == 0:
        return False, "Input byte stream is empty.", {"status": "EMPTY_STREAM"}

    if len(raw_bytes) > max_file_bytes:
        return False, f"File size ({len(raw_bytes)} bytes) exceeds maximum allowable limit ({max_file_bytes} bytes).", {
            "status": "OVERSIZED_STREAM",
            "file_size": len(raw_bytes),
            "max_file_bytes": max_file_bytes,
        }

    # Pre-decode dimension sniffing
    pre_decode_dims = sniff_image_dimensions_pre_decode(raw_bytes)
    if pre_decode_dims is not None:
        sniff_w, sniff_h, sniff_fmt = pre_decode_dims
        total_pixels = sniff_w * sniff_h

        # 1. Decompression bomb check: excessive pixel count
        if total_pixels > max_pixels:
            return False, (
                f"Potential decompression bomb rejected: Declared raster resolution ({sniff_w}x{sniff_h} = {total_pixels:,} pixels) "
                f"exceeds safe limit ({max_pixels:,} pixels)."
            ), {
                "status": "DECOMPRESSION_BOMB_DETECTED",
                "width": sniff_w,
                "height": sniff_h,
                "total_pixels": total_pixels,
            }

        # 2. Maximum single-axis dimension check
        if sniff_w > max_dimension or sniff_h > max_dimension:
            return False, (
                f"Image dimensions ({sniff_w}x{sniff_h}) exceed maximum allowable axis threshold ({max_dimension}px)."
            ), {
                "status": "AXIS_LIMIT_EXCEEDED",
                "width": sniff_w,
                "height": sniff_h,
                "max_dimension": max_dimension,
            }

    # Attempt safe Pillow open with resource bounds
    try:
        bio = io.BytesIO(raw_bytes)
        img = Image.open(bio)
        w, h = img.size
        img_format = (img.format or "UNKNOWN").upper()

        # Re-check actual parsed dimensions
        actual_pixels = w * h
        if actual_pixels > max_pixels:
            return False, (
                f"Decompression bomb blocked by decoder: {w}x{h} ({actual_pixels:,} pixels) exceeds {max_pixels:,}."
            ), {"status": "DECOMPRESSION_BOMB_DETECTED", "width": w, "height": h}

        if w > max_dimension or h > max_dimension:
            return False, f"Image axis ({w}x{h}) exceeds {max_dimension}px.", {
                "status": "AXIS_LIMIT_EXCEEDED",
                "width": w,
                "height": h,
            }

        if img_format not in ("JPEG", "PNG", "WEBP", "MPO"):
            return False, f"Unsupported image format '{img_format}'. Only JPEG, PNG, and WebP are permitted.", {
                "status": "UNSUPPORTED_FORMAT",
                "format": img_format,
            }

        return True, None, {
            "status": "SAFE",
            "width": w,
            "height": h,
            "format": img_format,
            "file_size_bytes": len(raw_bytes),
            "total_pixels": actual_pixels,
        }

    except Image.DecompressionBombError as e:
        return False, f"Pillow DecompressionBombError: {e}", {"status": "DECOMPRESSION_BOMB_TRIGGERED"}
    except Exception as e:
        return False, f"Corrupted or invalid image header: {e}", {"status": "MALFORMED_HEADER"}

