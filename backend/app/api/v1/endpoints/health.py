from backend.app.core.config import settings
from backend.app.schemas.health import HealthResponse
from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description=(
        "Returns platform operational health status, version metadata, and legal disclaimers."
    ),
)
async def check_health() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
    )
