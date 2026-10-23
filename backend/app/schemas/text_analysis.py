from datetime import datetime

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
