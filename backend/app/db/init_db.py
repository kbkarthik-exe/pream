from backend.app.db.base import Base
from backend.app.db.session import engine
from sqlalchemy import text

# Import all models to ensure they are registered with Base.metadata
from backend.app.models import (  # noqa: F401
    ForensicReport,
    ImageAnalysisRecord,
    TextAnalysisRecord,
    User,
    UserCloudCredential,
    UserSession,
    VideoAnalysisRecord,
)


async def init_db() -> None:
    """Initialize database tables and apply non-destructive schema migrations."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Non-destructive additive column migration for text ensemble telemetry
        try:
            await conn.execute(text("ALTER TABLE text_analysis_records ADD COLUMN ensemble_json TEXT;"))
        except Exception:
            pass
        # Non-destructive additive column migrations for image ensemble telemetry
        try:
            await conn.execute(text("ALTER TABLE image_analysis_records ADD COLUMN ensemble_json TEXT;"))
        except Exception:
            pass
        try:
            await conn.execute(text("ALTER TABLE image_analysis_records ADD COLUMN heatmap_json TEXT;"))
        except Exception:
            pass
        # Non-destructive additive column migrations for video facial deepfake & consensus telemetry
        try:
            await conn.execute(
                text("ALTER TABLE video_analysis_records ADD COLUMN face_deepfake_status VARCHAR(32) DEFAULT 'UNAVAILABLE';")
            )
        except Exception:
            pass
        try:
            await conn.execute(
                text("ALTER TABLE video_analysis_records ADD COLUMN consensus_verdict VARCHAR(64);")
            )
        except Exception:
            pass
        try:
            await conn.execute(
                text("ALTER TABLE video_analysis_records ADD COLUMN facial_telemetry_json TEXT;")
            )
        except Exception:
            pass
        try:
            await conn.execute(
                text("ALTER TABLE video_analysis_records ADD COLUMN consensus_json TEXT;")
            )
        except Exception:
            pass
