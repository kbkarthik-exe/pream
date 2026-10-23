from datetime import datetime
from typing import TYPE_CHECKING

from backend.app.db.base import Base
from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from backend.app.models.image_analysis import ImageAnalysisRecord
    from backend.app.models.report import ForensicReport
    from backend.app.models.session import UserSession
    from backend.app.models.text_analysis import TextAnalysisRecord


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(512), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    sessions: Mapped[list["UserSession"]] = relationship(
        "UserSession", back_populates="user", cascade="all, delete-orphan"
    )
    reports: Mapped[list["ForensicReport"]] = relationship(
        "ForensicReport", back_populates="user", cascade="all, delete-orphan"
    )
    text_analyses: Mapped[list["TextAnalysisRecord"]] = relationship(
        "TextAnalysisRecord", back_populates="user", cascade="all, delete-orphan"
    )
    image_analyses: Mapped[list["ImageAnalysisRecord"]] = relationship(
        "ImageAnalysisRecord", back_populates="user", cascade="all, delete-orphan"
    )
