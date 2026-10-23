from backend.app.db.base import Base
from backend.app.db.session import engine

# Import all models to ensure they are registered with Base.metadata
from backend.app.models import (  # noqa: F401
    ForensicReport,
    ImageAnalysisRecord,
    TextAnalysisRecord,
    User,
    UserSession,
)


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
