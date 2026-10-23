from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReportCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Investigation title")
    media_type: str = Field(
        ...,
        pattern="^(text|image|video|audio)$",
        description="Analyzed modality: text, image, video, audio",
    )
    summary: str = Field(..., min_length=1, description="Forensic telemetry notes and findings")
    is_private: bool = Field(default=True, description="Strictly restricted to report owner")


class ReportResponse(BaseModel):
    id: int
    user_id: int
    title: str
    media_type: str
    summary: str
    is_private: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
