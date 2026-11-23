"""Multi-signal Video Forensics Consensus and Aggregation Engine.

Combines:
1. Whole-frame generative Vision Transformer screening (Swin ViT).
2. Dedicated facial deepfake detection (MesoNet-4) on aligned facial crops.
3. Facial boundary seam gradient disparity telemetry.
4. Deterministic inter-frame motion and temporal flicker heuristics.
5. Optional third-party Hive AI cloud verification.

Produces calibrated verdicts:
- Likely Manipulated
- Likely Real
- Inconclusive

Adheres strictly to AICF epistemic honesty: zero fabricated metrics, no 100% certainty claims,
and transparent demarcation between neural models and heuristic signal measurements.
"""

from dataclasses import asdict, dataclass
import logging
from typing import Any

import numpy as np

from backend.app.ml.video.face_deepfake import FacialDeepfakeTelemetry
from backend.app.ml.video.hive_adapter import HiveDetectionResult
from backend.app.ml.video.temporal import TemporalAnalysisResult

logger = logging.getLogger("aicf.ml.video.ensemble")

VIDEO_ENSEMBLE_LIMITATIONS: list[str] = [
    (
        "Probabilistic Framework: Video consensus scores represent multi-signal statistical estimations "
        "and do not constitute definitive legal proof of authentic or synthetic origin."
    ),
    (
        "Modal Separation: Whole-frame screening detects generative diffusion/autoregressive synthesis "
        "(e.g., Sora, Runway, Pika), whereas the facial model targets face-swap and reenactment seams "
        "(e.g., DeepFaceLab, FaceForensics++)."
    ),
    (
        "Heuristic Physical Telemetry: Inter-frame pixel deltas, temporal flicker, and seam disparity "
        "are deterministic mathematical signal measurements, NOT trained neural representations."
    ),
    (
        "Compression and Transcoding Degradation: High-compression video encodings (e.g., social media "
        "re-encoding, H.264 macroblocking) attenuate facial boundary gradients and reduce detection confidence."
    ),
    (
        "No-Face Stream Scope: For videos lacking human subjects, facial deepfake analysis is deactivated, "
        "and determination relies solely on whole-frame generative screening."
    ),
]


@dataclass
class VideoConsensusBreakdown:
    """Detailed consensus score and telemetry breakdown returned by VideoEnsembleAggregator."""

    verdict: str  # "Likely Manipulated" | "Likely Real" | "Inconclusive"
    confidence_score: float  # [0.0, 1.0]
    composite_manipulation_score: float  # [0.0, 1.0]

    # Detector signals
    frame_screening_score: float
    frame_classifier_status: str  # "READY"
    facial_deepfake_score: float | None
    facial_detector_status: str  # "READY" | "UNAVAILABLE" | "NO_FACES_DETECTED"
    boundary_seam_delta: float
    temporal_flicker_score: float

    # Evidence and timeline
    evidence: list[dict[str, Any]]
    limitations: list[str]
    suspicious_temporal_segments: list[dict[str, Any]]


class VideoEnsembleAggregator:
    """Aggregates and calibrates multi-modal signals for AI video forensics."""

    def __init__(
        self,
        manipulated_threshold: float = 0.70,
        real_threshold: float = 0.30,
        temperature: float = 1.15,
    ) -> None:
        self.manipulated_threshold = manipulated_threshold
        self.real_threshold = real_threshold
        self.temperature = temperature

    def aggregate(
        self,
        mean_frame_ai: float,
        max_frame_ai: float,
        std_frame_ai: float,
        peak_frame_timestamp: float,
        facial_telemetry: FacialDeepfakeTelemetry,
        temporal_telemetry: TemporalAnalysisResult,
        hive_result: HiveDetectionResult | None = None,
    ) -> VideoConsensusBreakdown:
        """Calculates multi-signal video forensic consensus verdict."""
        # 1. Temperature scaling on whole-frame screening probability
        eps = 1e-6
        clipped_frame = float(np.clip(mean_frame_ai, eps, 1.0 - eps))
        logit = np.log(clipped_frame / (1.0 - clipped_frame))
        scaled_frame_ai = float(1.0 / (1.0 + np.exp(-logit / self.temperature)))

        has_faces = facial_telemetry.frames_with_faces > 0
        facial_model_ready = facial_telemetry.availability == "READY"
        facial_score = facial_telemetry.mean_facial_manipulation_score

        # 2. Multi-Signal Weighting
        if has_faces and facial_model_ready and facial_score is not None:
            # Neural facial model available and faces detected
            # Weights: 45% Frame Screening + 40% Facial Deepfake + 15% Boundary Seam Disparity
            seam_factor = float(np.clip(facial_telemetry.max_boundary_seam_delta, 0.0, 1.0))
            composite_score = (
                0.45 * scaled_frame_ai + 0.40 * facial_score + 0.15 * seam_factor
            )
        elif has_faces:
            # Faces detected, but neural facial weights not loaded (heuristic seam fallback)
            # Weights: 75% Frame Screening + 25% Boundary Seam Disparity
            seam_factor = float(np.clip(facial_telemetry.max_boundary_seam_delta * 1.5, 0.0, 1.0))
            composite_score = 0.75 * scaled_frame_ai + 0.25 * seam_factor
        else:
            # No faces in stream (landscape/object generative video)
            composite_score = scaled_frame_ai

        composite_score = float(np.clip(composite_score, 0.0, 1.0))

        # 3. Determine Final Verdict
        # High confidence manipulation
        if composite_score >= self.manipulated_threshold or (
            facial_score is not None and facial_score >= 0.85
        ) or (max_frame_ai >= 0.90 and scaled_frame_ai >= 0.65):
            verdict = "Likely Manipulated"
            confidence = composite_score
        elif composite_score <= self.real_threshold and max_frame_ai < 0.35 and (
            facial_score is None or facial_score < 0.30
        ):
            verdict = "Likely Real"
            confidence = 1.0 - composite_score
        else:
            verdict = "Inconclusive"
            confidence = float(max(composite_score, 1.0 - composite_score))

        # 4. Synthesize Explainable Forensic Evidence Items
        evidence: list[dict[str, Any]] = []

        # Signal 1: Whole-Frame Vision Transformer Screening
        evidence.append(
            {
                "signal": "Frame Synthetic Screening (Swin ViT)",
                "metric": f"Mean AI: {mean_frame_ai:.1%}, Peak: {max_frame_ai:.1%}",
                "finding": (
                    f"Sampled {facial_telemetry.total_frames_sampled} keyframes. "
                    f"Peak generative synthesis indicator observed at t={peak_frame_timestamp:.1f}s."
                ),
            }
        )

        # Signal 2: Dedicated Facial Deepfake Detection
        if not has_faces:
            facial_finding = "No human facial subjects identified in sampled video keyframes."
            facial_metric = "Status: NO_FACES_DETECTED"
        elif facial_model_ready and facial_score is not None:
            facial_metric = f"Mean Facial Fake: {facial_score:.1%}, Max: {facial_telemetry.max_facial_manipulation_score:.1%}"
            facial_finding = (
                f"Analyzed {facial_telemetry.total_faces_analyzed} face instance(s) across "
                f"{facial_telemetry.frames_with_faces} frame(s). "
                f"Peak manipulation observed at t={facial_telemetry.peak_manipulation_timestamp or 0.0:.1f}s."
            )
        else:
            facial_metric = "Status: UNAVAILABLE (Weights offline)"
            facial_finding = (
                f"Identified {facial_telemetry.total_faces_analyzed} face instance(s). "
                "Local neural facial weights offline; boundary seam telemetry active."
            )

        evidence.append(
            {
                "signal": "Dedicated Facial Deepfake Detection (MesoNet-4)",
                "metric": facial_metric,
                "finding": facial_finding,
            }
        )

        # Signal 3: Facial Boundary Seam Gradient Disparity
        if has_faces:
            evidence.append(
                {
                    "signal": "Facial Boundary Seam Telemetry",
                    "metric": f"Mean Seam: {facial_telemetry.mean_boundary_seam_delta:.3f}, Max: {facial_telemetry.max_boundary_seam_delta:.3f}",
                    "finding": (
                        f"Evaluated hairline and jawline compositing boundaries. "
                        f"{'Elevated seam disparity detected (potential boundary splicing).' if facial_telemetry.max_boundary_seam_delta >= 0.40 else 'Boundary gradients consistent with natural lighting.'}"
                    ),
                }
            )

        # Signal 4: Temporal Motion & Flicker Telemetry (Deterministic Heuristic)
        evidence.append(
            {
                "signal": "Temporal Motion & Flicker Telemetry",
                "metric": f"Flicker Score: {temporal_telemetry.temporal_flicker_score:.4f}, Mean Delta: {temporal_telemetry.mean_frame_difference:.4f}",
                "finding": (
                    f"Measured inter-frame optical consistency across consecutive frames. "
                    f"{len(temporal_telemetry.suspicious_transition_timestamps)} anomalous transition spike(s) detected. "
                    "(Deterministic optical heuristic, non-neural)."
                ),
            }
        )

        # Signal 5: Optional Third-Party Cloud Verification
        if hive_result and hive_result.is_configured and hive_result.status == "SUCCESS":
            evidence.append(
                {
                    "signal": "Hive AI Cloud Verification",
                    "metric": (
                        f"AI Gen: {hive_result.ai_generated_score:.1%}"
                        if hive_result.ai_generated_score is not None
                        else "N/A"
                    ),
                    "finding": (
                        f"Third-party Hive cloud corroboration received. "
                        f"Deepfake score: {hive_result.deepfake_score if hive_result.deepfake_score is not None else 'N/A'}."
                    ),
                }
            )

        return VideoConsensusBreakdown(
            verdict=verdict,
            confidence_score=round(confidence, 4),
            composite_manipulation_score=round(composite_score, 4),
            frame_screening_score=round(mean_frame_ai, 4),
            frame_classifier_status="READY",
            facial_deepfake_score=facial_score,
            facial_detector_status=facial_telemetry.availability,
            boundary_seam_delta=facial_telemetry.max_boundary_seam_delta,
            temporal_flicker_score=temporal_telemetry.temporal_flicker_score,
            evidence=evidence,
            limitations=VIDEO_ENSEMBLE_LIMITATIONS,
            suspicious_temporal_segments=facial_telemetry.suspicious_temporal_segments,
        )


video_ensemble = VideoEnsembleAggregator()
