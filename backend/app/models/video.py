"""Database model for recorded AI video forensic investigations."""

from datetime import datetime
from typing import TYPE_CHECKING

from backend.app.db.base import Base
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from backend.app.models.user import User


class VideoAnalysisRecord(Base):
    """Database model for recorded AI video forensic investigations.

    Stores cryptographic SHA-256 hash, container stream metrics, frame timeline telemetry,
    facial deepfake telemetry, consensus breakdown, and limitations without persisting the raw video stream.
    """

    __tablename__ = "video_analysis_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    file_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    video_width: Mapped[int] = mapped_column(Integer, nullable=False)
    video_height: Mapped[int] = mapped_column(Integer, nullable=False)
    fps: Mapped[float] = mapped_column(Float, nullable=False)
    total_frames: Mapped[int] = mapped_column(Integer, nullable=False)
    sampled_frame_count: Mapped[int] = mapped_column(Integer, nullable=False)

    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    frame_classifier_id: Mapped[str] = mapped_column(String(128), nullable=False)

    classification: Mapped[str] = mapped_column(String(32), nullable=False)
    consensus_verdict: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    ai_probability_mean: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    ai_probability_max: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    peak_frame_timestamp: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    temporal_flicker_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    face_deepfake_status: Mapped[str] = mapped_column(String(32), nullable=False, default="UNAVAILABLE")

    # Optional Hive Cloud Adapter outcome
    has_hive_result: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    hive_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # JSON Serialized Telemetry
    frame_scores_json: Mapped[str] = mapped_column(Text, nullable=False)
    temporal_telemetry_json: Mapped[str] = mapped_column(Text, nullable=False)
    facial_telemetry_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    consensus_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_json: Mapped[str] = mapped_column(Text, nullable=False)
    limitations_text: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(String(32), default="SUCCESS", nullable=False)
    processing_time_ms: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="video_analyses")
