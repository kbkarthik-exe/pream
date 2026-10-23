from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.report import ForensicReport
from backend.app.models.user import User
from backend.app.schemas.report import ReportCreate, ReportResponse
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get(
    "",
    response_model=list[ReportResponse],
    summary="List Analyst Reports",
    description="Returns all forensic reports created by the authenticated analyst.",
)
async def list_reports(
    media_type: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ReportResponse]:
    stmt = select(ForensicReport).where(ForensicReport.user_id == current_user.id)
    if media_type:
        stmt = stmt.where(ForensicReport.media_type == media_type)
    stmt = stmt.order_by(ForensicReport.created_at.desc())
    results = (await db.execute(stmt)).scalars().all()
    return [ReportResponse.model_validate(r) for r in results]


@router.post(
    "",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Forensic Report",
    description="Creates a new forensic investigation report linked to the authenticated analyst.",
)
async def create_report(
    payload: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    report = ForensicReport(
        user_id=current_user.id,
        title=payload.title,
        media_type=payload.media_type,
        summary=payload.summary,
        is_private=payload.is_private,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return ReportResponse.model_validate(report)


@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    summary="Get Specific Report",
    description="Retrieves a report with strict server-side owner authorization checks.",
)
async def get_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    report = await db.get(ForensicReport, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Forensic report #{report_id} not found.",
        )

    # Server-side authorization check: prevents horizontal privilege escalation
    if report.user_id != current_user.id and report.is_private:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You cannot access another user's private forensic report.",
        )

    return ReportResponse.model_validate(report)
