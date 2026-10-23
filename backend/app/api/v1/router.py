from backend.app.api.v1.endpoints import auth, dashboard, health, reports, text
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(text.router, prefix="/text", tags=["Text Forensics"])
api_router.include_router(reports.router, prefix="/reports", tags=["Forensic Reports"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
