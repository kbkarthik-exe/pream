"""Secure video ingestion, validation, and uniform temporal frame extraction."""

from dataclasses import dataclass
import hashlib
import logging
import os
from pathlib import Path
import tempfile
from typing import BinaryIO

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger("aicf.ml.video.frames")

SUPPORTED_VIDEO_FORMATS = {"mp4", "webm", "mov"}


@dataclass
class SampledFrame:
    """Container for an individual uniformly sampled video frame."""

    frame_index: int
    timestamp_seconds: float
    image_rgb: np.ndarray  # HxWx3 uint8 RGB array
    pil_image: Image.Image


@dataclass
class VideoInspectionResult:
    """Metadata and extracted keyframes for forensic analysis."""

    file_hash: str
    file_name: str
    file_size_bytes: int
    duration_seconds: float
    width: int
    height: int
    fps: float
    total_frames: int
    sampled_frames: list[SampledFrame]


def validate_video_magic_bytes(header: bytes) -> str:
    """Validate video magic bytes to reject executable and spoofed payloads.

    Returns the detected normalized format string ('mp4', 'webm', 'mov').
    Raises ValueError if format is unrecognized or invalid.
    """
    if len(header) < 12:
        raise ValueError("Video payload too small to contain valid container headers.")

    # 1. EBML header for WebM / Matroska (\x1a\x45\xdf\xa3)
    if header.startswith(b"\x1a\x45\xdf\xa3"):
        return "webm"

    # 2. ISO Base Media File Format (MP4 / MOV) box headers
    # Offset 4..8 usually contains 'ftyp'
    if header[4:8] == b"ftyp":
        brand = header[8:12]
        if brand in (b"isom", b"iso2", b"mp41", b"mp42", b"avc1", b"M4V ", b"M4A "):
            return "mp4"
        if brand in (b"qt  ", b"MSNV"):
            return "mov"
        # Generic compatible brand fallback
        return "mp4"

    # 3. QuickTime classic box headers (moov, wide, mdat at offset 4..8)
    if header[4:8] in (b"moov", b"wide", b"mdat", b"free"):
        return "mov"

    raise ValueError(
        "Invalid video container format. Only standard MP4, WebM, and MOV containers are supported."
    )


def extract_video_frames(
    file_stream: BinaryIO,
    file_name: str,
    max_file_size_bytes: int = 50 * 1024 * 1024,
    max_duration_seconds: float = 120.0,
    max_resolution: int = 3840,
    max_sampled_frames: int = 30,
    sample_interval_seconds: float = 1.0,
) -> VideoInspectionResult:
    """Securely reads, validates, and uniformly samples keyframes from an uploaded video stream.

    Safely uses a temporary file on disk for OpenCV decoding, enforcing complete cleanup
    in all exit scenarios.
    """
    # 1. Compute SHA-256 and read header for magic-byte verification
    sha256 = hashlib.sha256()
    header = file_stream.read(64)
    if not header:
        raise ValueError("Uploaded video file is empty (0 bytes).")

    format_detected = validate_video_magic_bytes(header)
    sha256.update(header)

    # 2. Write safely to a temporary file on disk with strict size checking
    temp_file = tempfile.NamedTemporaryFile(
        delete=False, suffix=f".{format_detected}", prefix="aicf_vid_"
    )
    temp_path = Path(temp_file.name)
    total_bytes = len(header)

    try:
        temp_file.write(header)
        while True:
            chunk = file_stream.read(1024 * 1024)  # 1 MB chunks
            if not chunk:
                break
            total_bytes += len(chunk)
            if total_bytes > max_file_size_bytes:
                raise ValueError(
                    f"Video file exceeds maximum permitted size of "
                    f"{max_file_size_bytes / (1024 * 1024):.1f} MB (uploaded {total_bytes / (1024 * 1024):.1f} MB)."
                )
            sha256.update(chunk)
            temp_file.write(chunk)
        temp_file.flush()
        temp_file.close()

        file_hash = sha256.hexdigest()

        # 3. Open with OpenCV headless
        cap = cv2.VideoCapture(str(temp_path))
        if not cap.isOpened():
            raise ValueError(
                "Unable to decode video stream. The video file may be corrupt or encoded in an unsupported codec."
            )

        try:
            # 4. Extract stream properties
            fps = float(cap.get(cv2.CAP_PROP_FPS))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            if fps <= 0.0 or np.isnan(fps):
                fps = 25.0  # Safe default if container header omits valid FPS

            duration = total_frames / fps if total_frames > 0 else 0.0

            # Guard checks
            if total_frames < 2:
                raise ValueError(
                    f"Video has insufficient frame count ({total_frames} frames). Minimum required is 2."
                )

            if duration > max_duration_seconds:
                raise ValueError(
                    f"Video duration ({duration:.1f}s) exceeds the maximum allowed duration "
                    f"of {max_duration_seconds:.0f}s."
                )

            if max(width, height) > max_resolution:
                raise ValueError(
                    f"Video resolution ({width}x{height}) exceeds maximum permitted dimension "
                    f"of {max_resolution}px."
                )

            # 5. Uniform temporal sampling calculation
            # Determine target timestamps: 1 frame per sample_interval_seconds, up to max_sampled_frames
            if duration <= 0.0:
                target_frame_indices = np.linspace(0, total_frames - 1, num=min(total_frames, max_sampled_frames), dtype=int)
            else:
                num_samples = min(
                    max(2, int(duration / max(0.1, sample_interval_seconds))),
                    max_sampled_frames,
                    total_frames,
                )
                target_frame_indices = np.linspace(0, total_frames - 1, num=num_samples, dtype=int)

            # Deduplicate frame indices while preserving order
            unique_indices = sorted(list(set(int(idx) for idx in target_frame_indices)))

            sampled_frames: list[SampledFrame] = []
            for idx in unique_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, bgr_frame = cap.read()
                if not ret or bgr_frame is None or bgr_frame.size == 0:
                    logger.warning("Corrupted or unreadable frame at index %d; skipping.", idx)
                    continue

                # Convert OpenCV BGR to RGB and PIL Image
                rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb_frame)
                timestamp = idx / fps

                sampled_frames.append(
                    SampledFrame(
                        frame_index=idx,
                        timestamp_seconds=round(timestamp, 3),
                        image_rgb=rgb_frame,
                        pil_image=pil_img,
                    )
                )

            if len(sampled_frames) < 2:
                raise ValueError(
                    f"Insufficient usable frames decoded from video ({len(sampled_frames)} valid frames). "
                    "Minimum required is 2."
                )

            return VideoInspectionResult(
                file_hash=file_hash,
                file_name=file_name,
                file_size_bytes=total_bytes,
                duration_seconds=round(duration, 3),
                width=width,
                height=height,
                fps=round(fps, 2),
                total_frames=total_frames,
                sampled_frames=sampled_frames,
            )

        finally:
            cap.release()

    finally:
        # Guarantee temporary file is deleted from disk
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception as exc:
                logger.warning("Failed to remove temporary video file %s: %s", temp_path, exc)
