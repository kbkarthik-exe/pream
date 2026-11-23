"""Modular Video Forensics Engine package."""

from backend.app.ml.video.detector import (
    DEFAULT_VIDEO_LIMITATIONS,
    FrameScoreRecord,
    VideoDetectionOutcome,
    VideoForensicsDetector,
    video_detector,
)
from backend.app.ml.video.ensemble import (
    VIDEO_ENSEMBLE_LIMITATIONS,
    VideoConsensusBreakdown,
    VideoEnsembleAggregator,
    video_ensemble,
)
from backend.app.ml.video.face_deepfake import (
    FacialDeepfakeDetector,
    FacialDeepfakeTelemetry,
    FacialFrameRecord,
    Meso4,
    facial_deepfake_detector,
)
from backend.app.ml.video.face_detector import (
    DetectedFace,
    FaceDetectorAndAligner,
    face_detector,
)
from backend.app.ml.video.frames import (
    SampledFrame,
    VideoInspectionResult,
    extract_video_frames,
    validate_video_magic_bytes,
)
from backend.app.ml.video.hive_adapter import (
    HiveDetectionResult,
    HiveVideoAdapter,
    hive_adapter,
)
from backend.app.ml.video.temporal import (
    TemporalAnalysisResult,
    compute_temporal_consistency,
)

__all__ = [
    "video_detector",
    "VideoForensicsDetector",
    "VideoDetectionOutcome",
    "FrameScoreRecord",
    "DEFAULT_VIDEO_LIMITATIONS",
    "extract_video_frames",
    "validate_video_magic_bytes",
    "SampledFrame",
    "VideoInspectionResult",
    "hive_adapter",
    "HiveVideoAdapter",
    "HiveDetectionResult",
    "compute_temporal_consistency",
    "TemporalAnalysisResult",
    "face_detector",
    "DetectedFace",
    "FaceDetectorAndAligner",
    "facial_deepfake_detector",
    "FacialDeepfakeDetector",
    "FacialDeepfakeTelemetry",
    "FacialFrameRecord",
    "Meso4",
    "video_ensemble",
    "VideoEnsembleAggregator",
    "VideoConsensusBreakdown",
    "VIDEO_ENSEMBLE_LIMITATIONS",
]
