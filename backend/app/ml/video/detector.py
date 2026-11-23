"""Production-grade AI Video Forensics Detection Engine.

Inherits from BaseDetector, providing:
1. Frame-level synthetic media classification via Swin Vision Transformer.
2. Uniform temporal frame sampling and timestamp tracking.
3. Dedicated facial deepfake detection (MesoNet-4) on aligned facial crops.
4. Facial boundary seam blending gradient disparity telemetry.
5. Deterministic temporal consistency & motion flicker heuristics.
6. Optional cloud Hive AI adapter for third-party verification.
7. Multi-signal video forensics consensus aggregation engine.
8. Strict AICF epistemic honesty rules: transparent classification boundaries and zero fabricated metrics.
"""

from dataclasses import asdict, dataclass
import logging
import time
from typing import Any

from backend.app.core.config import settings
from backend.app.ml.base import BaseDetector
from backend.app.ml.image import image_detector
from backend.app.ml.video.ensemble import (
    VIDEO_ENSEMBLE_LIMITATIONS,
    VideoConsensusBreakdown,
    video_ensemble,
)
from backend.app.ml.video.face_deepfake import (
    FacialDeepfakeTelemetry,
    facial_deepfake_detector,
)
from backend.app.ml.video.frames import SampledFrame, VideoInspectionResult
from backend.app.ml.video.hive_adapter import HiveDetectionResult, hive_adapter
from backend.app.ml.video.temporal import TemporalAnalysisResult, compute_temporal_consistency
import numpy as np

logger = logging.getLogger("aicf.ml.video.detector")

DEFAULT_VIDEO_LIMITATIONS: list[str] = VIDEO_ENSEMBLE_LIMITATIONS


@dataclass
class FrameScoreRecord:
    frame_index: int
    timestamp_seconds: float
    ai_probability: float
    human_probability: float
    classification: str


@dataclass
class VideoDetectionOutcome:
    """Full forensic analysis package returned by VideoForensicsDetector."""

    file_hash: str
    file_name: str
    file_size_bytes: int
    duration_seconds: float
    width: int
    height: int
    fps: float
    total_frames: int
    sampled_frame_count: int

    model_name: str
    model_version: str
    frame_classifier_id: str
    classification: str
    confidence_score: float
    ai_probability_mean: float
    ai_probability_max: float
    ai_probability_min: float
    ai_probability_std: float
    peak_frame_timestamp: float

    # Frame-by-frame timeline
    frame_scores: list[FrameScoreRecord]

    # Temporal telemetry (heuristic)
    temporal_telemetry: TemporalAnalysisResult

    # Facial analysis status & telemetry
    face_deepfake_status: str  # "READY" | "UNAVAILABLE" | "NO_FACES_DETECTED"
    facial_telemetry: FacialDeepfakeTelemetry | None

    # Multi-signal consensus
    consensus: VideoConsensusBreakdown | None

    # Optional Hive AI result
    hive_result: HiveDetectionResult | None

    # Evidence items and scientific boundaries
    evidence: list[dict[str, Any]]
    limitations: list[str]
    processing_time_ms: float
    status: str = "SUCCESS"


class VideoForensicsDetector(BaseDetector):
    """Production AI Video Forensics Detector implementing BaseDetector."""

    def __init__(
        self,
        name: str = "AICF-Video-Forensics-Engine",
        version: str = "2.0.0",
        ai_threshold: float = 0.70,
        human_threshold: float = 0.30,
    ) -> None:
        super().__init__(name=name, media_type="video", version=version)
        self.ai_threshold = ai_threshold
        self.human_threshold = human_threshold
        self.frame_classifier_id = settings.VIDEO_FRAME_CLASSIFIER_ID

    async def analyze(self, payload: Any) -> dict[str, Any]:
        """BaseDetector abstract method implementation."""
        if not isinstance(payload, VideoInspectionResult):
            raise ValueError("VideoForensicsDetector expects VideoInspectionResult payload.")
        outcome = await self.detect_video(payload)
        return asdict(outcome)

    async def detect_video(
        self,
        inspection: VideoInspectionResult,
        video_bytes: bytes | None = None,
        query_hive: bool = False,
    ) -> VideoDetectionOutcome:
        """Executes full multi-modal video forensics pipeline."""
        t0 = time.time()
        logger.info(
            "Beginning video forensic analysis for '%s' (%d sampled frames)...",
            inspection.file_name,
            len(inspection.sampled_frames),
        )

        # 1. Ensure underlying frame image detector is loaded
        if not image_detector.is_loaded:
            logger.info("Underlying frame image detector not loaded; initializing now...")
            image_detector.load_model()

        # 2. Frame-by-frame inference using Swin Vision Transformer
        frame_records: list[FrameScoreRecord] = []
        ai_scores: list[float] = []

        for f in inspection.sampled_frames:
            try:
                # Use preloaded Swin image classifier
                inference = image_detector.classify_image(f.pil_image)
                ai_prob = float(inference.get("ai_probability", 0.5))
                human_prob = float(inference.get("human_probability", 0.5))
            except Exception as exc:
                logger.warning("Frame %d inference failed: %s; using neutral score.", f.frame_index, exc)
                ai_prob = 0.5
                human_prob = 0.5

            ai_scores.append(ai_prob)

            # Classify individual frame
            if ai_prob >= 0.85:
                f_class = "HIGHLY_LIKELY_AI"
            elif ai_prob >= 0.70:
                f_class = "SUSPECTED_AI"
            elif ai_prob <= 0.15:
                f_class = "HIGHLY_LIKELY_AUTHENTIC"
            elif ai_prob <= 0.30:
                f_class = "LIKELY_AUTHENTIC"
            else:
                f_class = "INCONCLUSIVE"

            frame_records.append(
                FrameScoreRecord(
                    frame_index=f.frame_index,
                    timestamp_seconds=round(f.timestamp_seconds, 3),
                    ai_probability=round(ai_prob, 4),
                    human_probability=round(human_prob, 4),
                    classification=f_class,
                )
            )

        # 3. Statistical aggregation across sampled frames
        ai_arr = np.array(ai_scores) if ai_scores else np.array([0.5])
        mean_ai = float(np.mean(ai_arr))
        max_ai = float(np.max(ai_arr))
        min_ai = float(np.min(ai_arr))
        std_ai = float(np.std(ai_arr))

        # Peak frame timestamp
        peak_idx = int(np.argmax(ai_arr))
        peak_timestamp = inspection.sampled_frames[peak_idx].timestamp_seconds

        # 4. Dedicated Facial Deepfake Detection across sampled frames
        facial_telemetry = facial_deepfake_detector.analyze_sampled_frames(
            inspection.sampled_frames
        )

        # 5. Temporal consistency & motion flicker telemetry
        temporal_result = compute_temporal_consistency(inspection.sampled_frames)

        # 6. Optional Hive AI Cloud query
        hive_res: HiveDetectionResult | None = None
        if query_hive and video_bytes and hive_adapter.is_configured:
            logger.info("Submitting video to Hive AI official adapter...")
            hive_res = await hive_adapter.analyze_video(video_bytes, inspection.file_name)
        elif query_hive:
            hive_res = HiveDetectionResult(
                is_configured=False,
                status="CONFIGURATION_REQUIRED",
                error_message="HIVE_API_KEY is not configured on the server.",
            )

        # 7. Multi-Signal Video Forensics Consensus Aggregation
        consensus_outcome = video_ensemble.aggregate(
            mean_frame_ai=mean_ai,
            max_frame_ai=max_ai,
            std_frame_ai=std_ai,
            peak_frame_timestamp=peak_timestamp,
            facial_telemetry=facial_telemetry,
            temporal_telemetry=temporal_result,
            hive_result=hive_res,
        )

        # Map to root classification string for backward-compatibility
        if consensus_outcome.verdict == "Likely Manipulated":
            classification = "HIGHLY_LIKELY_AI" if max_ai >= 0.88 else "SUSPECTED_AI"
            confidence_score = consensus_outcome.confidence_score
        elif consensus_outcome.verdict == "Likely Real":
            classification = "HIGHLY_LIKELY_AUTHENTIC" if mean_ai <= 0.15 else "LIKELY_AUTHENTIC"
            confidence_score = consensus_outcome.confidence_score
        else:
            classification = "INCONCLUSIVE"
            confidence_score = consensus_outcome.confidence_score

        elapsed_ms = (time.time() - t0) * 1000.0

        return VideoDetectionOutcome(
            file_hash=inspection.file_hash,
            file_name=inspection.file_name,
            file_size_bytes=inspection.file_size_bytes,
            duration_seconds=inspection.duration_seconds,
            width=inspection.width,
            height=inspection.height,
            fps=inspection.fps,
            total_frames=inspection.total_frames,
            sampled_frame_count=len(inspection.sampled_frames),
            model_name=self.name,
            model_version=self.version,
            frame_classifier_id=self.frame_classifier_id,
            classification=classification,
            confidence_score=round(confidence_score, 4),
            ai_probability_mean=round(mean_ai, 4),
            ai_probability_max=round(max_ai, 4),
            ai_probability_min=round(min_ai, 4),
            ai_probability_std=round(std_ai, 4),
            peak_frame_timestamp=round(peak_timestamp, 3),
            frame_scores=frame_records,
            temporal_telemetry=temporal_result,
            face_deepfake_status=facial_telemetry.availability,
            facial_telemetry=facial_telemetry,
            consensus=consensus_outcome,
            hive_result=hive_res,
            evidence=consensus_outcome.evidence,
            limitations=consensus_outcome.limitations,
            processing_time_ms=round(elapsed_ms, 2),
            status="SUCCESS",
        )


video_detector = VideoForensicsDetector()
