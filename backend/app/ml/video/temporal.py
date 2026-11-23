"""Temporal consistency and inter-frame motion telemetry for video forensics.

CRITICAL EPISTEMIC NOTICE:
The metrics computed here are deterministic heuristic measures of inter-frame pixel differences,
optical displacement, and high-frequency temporal flicker. They are NOT trained neural deepfake
representations and must NEVER be presented as standalone neural predictions.
"""

import logging
from dataclasses import dataclass

import cv2
import numpy as np
from backend.app.ml.video.frames import SampledFrame

logger = logging.getLogger("aicf.ml.video.temporal")


@dataclass
class TemporalAnalysisResult:
    """Heuristic temporal telemetry computed across consecutive sampled frames."""

    mean_frame_difference: float
    temporal_flicker_score: float
    suspicious_transition_timestamps: list[float]
    frame_deltas: list[float]
    inter_frame_variance_ratio: float = 0.0
    motion_stability_score: float = 1.0
    is_heuristic: bool = True
    heuristic_notes: str = (
        "Deterministic optical telemetry: physical/pixel difference and luminance flicker measurements. "
        "These are heuristic signal measurements, NOT trained neural deepfake representations."
    )


def compute_temporal_consistency(
    sampled_frames: list[SampledFrame],
) -> TemporalAnalysisResult:
    """Computes inter-frame differences, temporal flicker, and motion stability across sampled frames.

    Uses normalized grayscale L1/L2 distance between adjacent downsampled frames.
    """
    if len(sampled_frames) < 2:
        return TemporalAnalysisResult(
            mean_frame_difference=0.0,
            temporal_flicker_score=0.0,
            suspicious_transition_timestamps=[],
            frame_deltas=[],
            inter_frame_variance_ratio=0.0,
            motion_stability_score=1.0,
        )

    # Downsample frames to a fixed 128x128 grayscale representation for fast, stable delta calculation
    target_dim = (128, 128)
    gray_frames: list[np.ndarray] = []
    for f in sampled_frames:
        resized = cv2.resize(f.image_rgb, target_dim, interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(resized, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
        gray_frames.append(gray)

    # Compute absolute differences between consecutive frames
    deltas: list[float] = []
    for i in range(len(gray_frames) - 1):
        diff = np.abs(gray_frames[i + 1] - gray_frames[i])
        mean_diff = float(np.mean(diff))
        deltas.append(round(mean_diff, 4))

    mean_delta = float(np.mean(deltas)) if deltas else 0.0
    std_delta = float(np.std(deltas)) if deltas else 0.0
    median_delta = float(np.median(deltas)) if deltas else 0.0
    max_delta = float(np.max(deltas)) if deltas else 0.0

    # Inter-frame variance ratio (max delta relative to baseline median)
    variance_ratio = round(max_delta / (median_delta + 1e-4), 3) if deltas else 0.0

    # Motion stability: 1.0 is perfectly stable smooth video; decreases with irregular flicker
    stability = float(np.clip(1.0 - (std_delta * 3.5), 0.0, 1.0))

    # Identify anomalous spikes: transitions where delta exceeds mean + 2.5 * std (or absolute threshold > 0.35)
    suspicious_timestamps: list[float] = []
    threshold = max(0.35, mean_delta + 2.5 * std_delta)
    for i, delta in enumerate(deltas):
        if delta > threshold:
            # Timestamp of the transition frame
            suspicious_timestamps.append(round(sampled_frames[i + 1].timestamp_seconds, 3))

    return TemporalAnalysisResult(
        mean_frame_difference=round(mean_delta, 4),
        temporal_flicker_score=round(std_delta, 4),
        suspicious_transition_timestamps=suspicious_timestamps,
        frame_deltas=deltas,
        inter_frame_variance_ratio=variance_ratio,
        motion_stability_score=round(stability, 4),
    )
