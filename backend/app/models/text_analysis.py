from datetime import datetime
from typing import TYPE_CHECKING

from backend.app.db.base import Base
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from backend.app.models.user import User


class TextAnalysisRecord(Base):
    """Database model for recorded AI text forensic investigations.

    Stores cryptographic input hash and telemetry without retaining raw user text by default.
    """

    __tablename__ = "text_analysis_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    input_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    text_snippet: Mapped[str] = mapped_column(String(255), nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False)
    character_count: Mapped[int] = mapped_column(Integer, nullable=False)

    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    classification: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)

    # Computed Explainable Features
    perplexity_score: Mapped[float] = mapped_column(Float, nullable=False)
    burstiness_score: Mapped[float] = mapped_column(Float, nullable=False)
    token_entropy: Mapped[float] = mapped_column(Float, nullable=False)
    type_token_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    repeated_ngram_ratio: Mapped[float] = mapped_column(Float, nullable=False)

    evidence_json: Mapped[str] = mapped_column(Text, nullable=False)
    limitations_text: Mapped[str] = mapped_column(Text, nullable=False)
    ensemble_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(32), default="SUCCESS", nullable=False)
    processing_time_ms: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="text_analyses")
