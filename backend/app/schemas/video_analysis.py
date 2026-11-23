"""Pydantic schemas for AI video forensic investigations."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FrameScoreItem(BaseModel):
    """Forensic score for an individual sampled video frame."""

    frame_index: int
    timestamp_seconds: float
    ai_probability: float
    human_probability: float
    classification: str


class TemporalTelemetryInfo(BaseModel):
    """Deterministic inter-frame motion and flicker telemetry."""

    mean_frame_difference: float = 0.0
    temporal_flicker_score: float = 0.0
    suspicious_transition_timestamps: list[float] = Field(default_factory=list)
    inter_frame_variance_ratio: float = 0.0
    motion_stability_score: float = 1.0
    is_heuristic: bool = True
    heuristic_notes: str = ""


class HiveAnalysisInfo(BaseModel):
    """Outcome from optional Hive AI cloud verification adapter."""

    is_configured: bool = False
    status: str = "CONFIGURATION_REQUIRED"
    provider_name: str = "Hive AI"
    model_version: str | None = None
    ai_generated_score: float | None = None
    deepfake_score: float | None = None
    classes_detected: list[dict[str, Any]] | None = None
    raw_response_summary: str | None = None
    error_message: str | None = None


class VideoEvidenceItem(BaseModel):
    """Explainable finding or signal indicator."""

    signal: str
    metric: str | None = None
    finding: str


class FacialFrameRecordItem(BaseModel):
    """Timestamp-based forensic record for faces detected in a single sampled frame."""

    frame_index: int
    timestamp_seconds: float
    face_count: int
    face_detected: bool
    primary_bbox: list[int] | None = None
    face_manipulation_score: float | None = None
    boundary_seam_delta: float | None = None
    is_low_res: bool = False
    verdict: str = "NO_FACE"


class SuspiciousSegmentItem(BaseModel):
    """Cluster of consecutive timestamps exhibiting anomalous facial manipulation signals."""

    start_timestamp_seconds: float
    end_timestamp_seconds: float
    frame_count: int
    peak_manipulation_score: float | None = None
    peak_boundary_seam_delta: float = 0.0
    description: str


class FacialDeepfakeTelemetryInfo(BaseModel):
    """Comprehensive facial deepfake and boundary seam telemetry."""

    model_name: str = "MesoNet-4 Facial Forensics Head"
    model_version: str = "1.0.0"
    model_license: str = "MIT / Research (Dari et al., WIFS 2018)"
    availability: str = "UNAVAILABLE"
    total_faces_analyzed: int = 0
    frames_with_faces: int = 0
    total_frames_sampled: int = 0
    mean_facial_manipulation_score: float | None = None
    max_facial_manipulation_score: float | None = None
    mean_boundary_seam_delta: float = 0.0
    max_boundary_seam_delta: float = 0.0
    peak_manipulation_timestamp: float | None = None
    low_resolution_frames_count: int = 0
    timeline: list[FacialFrameRecordItem] = Field(default_factory=list)
    suspicious_temporal_segments: list[SuspiciousSegmentItem] = Field(default_factory=list)
    error_message: str | None = None


class VideoConsensusBreakdownInfo(BaseModel):
    """Consensus score and multi-signal breakdown."""

    verdict: str  # "Likely Manipulated" | "Likely Real" | "Inconclusive"
    confidence_score: float
    composite_manipulation_score: float
    frame_screening_score: float
    frame_classifier_status: str = "READY"
    facial_deepfake_score: float | None = None
    facial_detector_status: str = "UNAVAILABLE"
    boundary_seam_delta: float = 0.0
    temporal_flicker_score: float = 0.0


class VideoAnalysisResponse(BaseModel):
    """Structured response returned by the video forensics engine."""

    analysis_id: int
    user_id: int
    file_hash: str
    file_name: str
    file_size_bytes: int
    duration_seconds: float
    video_width: int
    video_height: int
    fps: float
    total_frames: int
    sampled_frame_count: int

    model_name: str
    model_version: str
    frame_classifier_id: str
    status: str
    classification: str
    confidence_score: float
    ai_probability_mean: float
    ai_probability_max: float
    peak_frame_timestamp: float
    temporal_flicker_score: float
    face_deepfake_status: str = "UNAVAILABLE"
    consensus_verdict: str | None = None

    frame_scores: list[FrameScoreItem] = Field(default_factory=list)
    temporal_telemetry: TemporalTelemetryInfo | None = None
    facial_telemetry: FacialDeepfakeTelemetryInfo | None = None
    consensus: VideoConsensusBreakdownInfo | None = None
    hive_result: HiveAnalysisInfo | None = None
    evidence: list[VideoEvidenceItem] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)

    processing_time_ms: float
    created_at: datetime
    case_report_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class VideoAnalysisHistoryItem(BaseModel):
    """Summary item for authenticated user's video investigation history."""

    id: int
    file_hash: str
    file_name: str
    file_size_bytes: int
    duration_seconds: float
    video_width: int
    video_height: int
    fps: float
    total_frames: int
    sampled_frame_count: int
    model_name: str
    model_version: str
    classification: str
    consensus_verdict: str | None = None
    confidence_score: float
    ai_probability_mean: float
    ai_probability_max: float
    peak_frame_timestamp: float
    temporal_flicker_score: float
    face_deepfake_status: str = "UNAVAILABLE"
    status: str
    processing_time_ms: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
