from backend.app.api.v1.endpoints import (
    auth,
    cloud,
    dashboard,
    evaluation,
    health,
    image,
    reports,
    text,
    video,
)
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(text.router, prefix="/text", tags=["Text Forensics"])
api_router.include_router(image.router, prefix="/image", tags=["Image Forensics"])
api_router.include_router(video.router, prefix="/video", tags=["Video Forensics"])
api_router.include_router(cloud.router, prefix="/cloud", tags=["Cloud Verification Hub"])
api_router.include_router(reports.router, prefix="/reports", tags=["Forensic Reports"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(
    evaluation.router,
    prefix="/evaluation",
    tags=["Model Evaluation & Benchmarking"],
)

