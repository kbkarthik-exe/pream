from pydantic import BaseModel, Field


class DashboardStatsResponse(BaseModel):
    total_reports: int = Field(default=0, description="Total investigations recorded by analyst")
    text_reports: int = Field(default=0, description="Text forensic investigations")
    image_reports: int = Field(default=0, description="Image forensic investigations")
    video_reports: int = Field(default=0, description="Video forensic investigations")
    audio_reports: int = Field(default=0, description="Audio forensic investigations")
    active_sessions: int = Field(default=1, description="Active user sessions")
