from datetime import UTC, datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="healthy", description="Overall service status")
    service: str = Field(..., description="Service identifier")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Current UTC timestamp",
    )
    environment: str = Field(..., description="Runtime environment")
    disclaimer: str = Field(
        default=(
            "Forensic AI outputs are probabilistic indicators, not definitive proof of authorship."
        ),
        description="Legal and scientific disclaimer",
    )
