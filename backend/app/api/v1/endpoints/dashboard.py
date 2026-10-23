from datetime import UTC, datetime

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.report import ForensicReport
from backend.app.models.session import UserSession
from backend.app.models.user import User
from backend.app.schemas.dashboard import DashboardStatsResponse
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get(
    "/stats",
    response_model=DashboardStatsResponse,
    summary="Analyst Dashboard Statistics",
    description="Returns real aggregation metrics from PostgreSQL for the authenticated analyst.",
)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardStatsResponse:
    now = datetime.now(UTC)

    # 1. Total reports for this user
    total_q = select(func.count(ForensicReport.id)).where(ForensicReport.user_id == current_user.id)
    total_reports: int = (await db.execute(total_q)).scalar_one() or 0

    # 2. Modality counts
    text_q = select(func.count(ForensicReport.id)).where(
        ForensicReport.user_id == current_user.id,
        ForensicReport.media_type == "text",
    )
    text_reports: int = (await db.execute(text_q)).scalar_one() or 0

    image_q = select(func.count(ForensicReport.id)).where(
        ForensicReport.user_id == current_user.id,
        ForensicReport.media_type == "image",
    )
    image_reports: int = (await db.execute(image_q)).scalar_one() or 0

    video_q = select(func.count(ForensicReport.id)).where(
        ForensicReport.user_id == current_user.id,
        ForensicReport.media_type == "video",
    )
    video_reports: int = (await db.execute(video_q)).scalar_one() or 0

    audio_q = select(func.count(ForensicReport.id)).where(
        ForensicReport.user_id == current_user.id,
        ForensicReport.media_type == "audio",
    )
    audio_reports: int = (await db.execute(audio_q)).scalar_one() or 0

    # 3. Active sessions for this user
    sessions_q = select(func.count(UserSession.id)).where(
        UserSession.user_id == current_user.id,
        UserSession.expires_at > now,
    )
    active_sessions: int = (await db.execute(sessions_q)).scalar_one() or 0

    return DashboardStatsResponse(
        total_reports=total_reports,
        text_reports=text_reports,
        image_reports=image_reports,
        video_reports=video_reports,
        audio_reports=audio_reports,
        active_sessions=max(1, active_sessions),
    )
