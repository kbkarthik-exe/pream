"""Pydantic schemas for AI image forensic investigations."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ImageEvidenceItem(BaseModel):
    signal: str
    metric: str | None = None
    finding: str


class ProvenanceInfo(BaseModel):
    has_exif: bool = False
    exif_summary: dict[str, Any] = Field(default_factory=dict)
    has_ai_metadata: bool = False
    ai_prompt_snippet: str | None = None
    has_c2pa: bool = False
    c2pa_finding: str = ""
    provenance_summary: str = ""


class ImageDetectorScore(BaseModel):
    detector_id: str
    model_name: str
    status: str  # "READY", "RESOURCE_CONSTRAINED", "UNAVAILABLE", "CONFIGURATION_REQUIRED", "ERROR"
    raw_probability: float | None = None
    calibrated_score: float | None = None
    latency_ms: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class ImageHeatmapData(BaseModel):
    method: str
    ela_mean_error: float = 0.0
    ela_max_error: float = 0.0
    ela_discontinuity_score: float = 0.0
    heatmap_data_url: str | None = None
    noise_residual_data_url: str | None = None
    explanation: str = ""


class ImageEnsembleBreakdown(BaseModel):
    consensus_score: float
    confidence: float
    classification: str
    temperature_applied: float
    covariance_penalty: float
    spectral_prior_weight: float
    active_detectors_count: int
    notes: list[str] = Field(default_factory=list)


class ImageAnalysisResponse(BaseModel):
    """Structured result returned by the image forensics engine."""

    analysis_id: int
    user_id: int
    file_hash: str
    file_name: str
    file_size_bytes: int
    image_width: int
    image_height: int
    image_format: str

    model_name: str
    model_version: str
    status: str
    classification: str
    confidence_score: float | None = None
    ai_probability: float | None = None
    human_probability: float | None = None
    raw_score: float | None = None

    # Deterministic Telemetry
    fft_high_freq_ratio: float = 0.0
    spectral_anisotropy: float = 0.0
    noise_variance: float = 0.0
    has_ai_metadata: bool = False
    has_c2pa: bool = False

    provenance: ProvenanceInfo | None = None
    evidence: list[ImageEvidenceItem] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)

    # Multi-Detector Ensemble & Heatmaps
    detector_scores: list[ImageDetectorScore] = Field(default_factory=list)
    ensemble: ImageEnsembleBreakdown | None = None
    heatmap: ImageHeatmapData | None = None

    processing_time_ms: float
    created_at: datetime
    case_report_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class ImageAnalysisHistoryItem(BaseModel):
    id: int
    file_hash: str
    file_name: str
    file_size_bytes: int
    image_width: int
    image_height: int
    image_format: str
    model_name: str
    model_version: str
    classification: str
    confidence_score: float | None = None
    status: str
    processing_time_ms: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
