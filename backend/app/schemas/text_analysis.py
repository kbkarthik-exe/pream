from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TextAnalysisRequest(BaseModel):
    """Payload for text forensics analysis."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=15000,
        description="Text content to analyze for synthetic vs. human authorship signals.",
    )
    save_to_cases: bool = Field(
        default=False,
        description="Optionally create a linked ForensicReport case record in the archive.",
    )


class EvidenceItem(BaseModel):
    signal: str
    metric: str | None = None
    finding: str


class SentenceAnalysisItem(BaseModel):
    sentence_idx: int = 0
    sentence_index: int = 0
    text: str = ""
    word_count: int = 0
    char_count: int = 0
    character_count: int = 0
    relative_cadence: str | float = "BALANCED"
    cadence_ratio: float = 1.0
    punct_count: int = 0
    punctuation_count: int = 0
    has_transitional_opening: bool = False
    has_transitional_marker: bool = False

    model_config = ConfigDict(extra="ignore")


class ParagraphAnalysisItem(BaseModel):
    paragraph_idx: int = 0
    paragraph_index: int = 0
    text_snippet: str = ""
    word_count: int = 0
    sentence_count: int = 0
    avg_sentence_len: float = 0.0
    avg_sentence_length: float = 0.0
    type_token_ratio: float = 0.0

    model_config = ConfigDict(extra="ignore")


class PunctuationMetrics(BaseModel):
    comma_count: int = 0
    commas: int = 0
    period_count: int = 0
    periods: int = 0
    semicolon_count: int = 0
    semicolons: int = 0
    colon_count: int = 0
    colons: int = 0
    exclamation_count: int = 0
    exclamations: int = 0
    question_count: int = 0
    questions: int = 0
    hyphen_count: int = 0
    hyphens: int = 0
    total_punctuation_count: int = 0
    punctuation_density: float = 0.0

    model_config = ConfigDict(extra="ignore")


class DetectorScore(BaseModel):
    """Individual model telemetry in multi-detector architecture."""

    model_name: str
    model_version: str = "1.0.0"
    status: str
    status_detail: str | None = None
    ai_probability: float | None = None
    human_probability: float | None = None
    confidence_score: float | None = None
    latency_ms: float = 0.0
    raw_output: dict[str, Any] | None = None

    model_config = ConfigDict(extra="ignore")


class EnsembleBreakdown(BaseModel):
    """Consensus aggregation and calibration metadata."""

    ensemble_method: str
    calibration_method: str
    detectors: dict[str, DetectorScore] = Field(default_factory=dict)
    active_detector_count: int = 1
    total_detector_count: int = 3
    agreement_score: float | None = None
    uncertainty_margin: float | None = None
    disagreement_analysis: str | None = None
    evidence_strength: str | None = None
    reasons_for_uncertainty: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class TextAnalysisResponse(BaseModel):
    """Forensic verification response with real computed signals and calibrated confidence."""

    analysis_id: int
    user_id: int
    input_hash: str
    text_snippet: str
    word_count: int
    character_count: int

    model_name: str
    model_version: str
    status: str
    classification: str
    confidence_score: float | None = None
    ai_probability: float | None = None
    human_probability: float | None = None

    # Deterministic Linguistic Features
    perplexity_score: float = 0.0
    burstiness_score: float = 0.0
    token_entropy: float = 0.0
    type_token_ratio: float = 0.0
    repeated_ngram_ratio: float = 0.0

    # Multi-Detector Ensemble Data
    detector_scores: dict[str, DetectorScore] = Field(default_factory=dict)
    ensemble: EnsembleBreakdown | None = None

    # Granular Forensic Telemetry
    sentence_analysis: list[SentenceAnalysisItem] = Field(default_factory=list)
    paragraph_analysis: list[ParagraphAnalysisItem] = Field(default_factory=list)
    punctuation_metrics: PunctuationMetrics | None = None
    sentence_length_distribution: dict[str, float] = Field(default_factory=dict)
    syntactic_repetition: dict[str, Any] = Field(default_factory=dict)
    language_warning: str | None = None

    evidence: list[EvidenceItem] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)

    processing_time_ms: float
    created_at: datetime
    case_report_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class TextAnalysisHistoryItem(BaseModel):
    id: int
    input_hash: str
    text_snippet: str
    word_count: int
    character_count: int
    model_name: str
    model_version: str
    classification: str
    confidence_score: float | None = None
    status: str
    processing_time_ms: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
