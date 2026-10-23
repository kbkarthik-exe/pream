"""Database model for recorded AI image forensic investigations."""

from datetime import datetime
from typing import TYPE_CHECKING

from backend.app.db.base import Base
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from backend.app.models.user import User


class ImageAnalysisRecord(Base):
    """Database model for recorded AI image forensic investigations.

    Stores cryptographic SHA-256 hash, image metrics, model telemetry, and provenance
    findings without permanently persisting the raw uploaded image file.
    """

    __tablename__ = "image_analysis_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    file_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    image_width: Mapped[int] = mapped_column(Integer, nullable=False)
    image_height: Mapped[int] = mapped_column(Integer, nullable=False)
    image_format: Mapped[str] = mapped_column(String(16), nullable=False)

    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    classification: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    ai_probability: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    human_probability: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Computed Explainable Features
    fft_high_freq_ratio: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    spectral_anisotropy: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    noise_variance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    has_ai_metadata: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_c2pa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    evidence_json: Mapped[str] = mapped_column(Text, nullable=False)
    provenance_json: Mapped[str] = mapped_column(Text, nullable=False)
    limitations_text: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(String(32), default="SUCCESS", nullable=False)
    processing_time_ms: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="image_analyses")
