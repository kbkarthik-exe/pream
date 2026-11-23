"""FastAPI router endpoints for the Cloud Verification Hub."""

import logging

from backend.app.api.deps import get_current_user
from backend.app.core.rate_limiter import rate_limiter
from backend.app.db.session import get_db
from backend.app.ml.cloud.manager import cloud_manager
from backend.app.models.user import User
from backend.app.schemas.cloud import (
    CloudOperationResponse,
    CloudProviderResultItem,
    CloudProviderStatusResponse,
    CloudTextVerificationRequest,
    CloudTextVerificationResponse,
    SaveCloudCredentialRequest,
    TestCloudConnectionRequest,
)
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("aicf.api.cloud")

router = APIRouter()


@router.get(
    "/providers",
    response_model=list[CloudProviderStatusResponse],
    summary="List Cloud Providers & Configuration Status",
    description="Returns public status cards for all authorized cloud verification providers with safe masked credentials.",
)
async def list_cloud_providers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CloudProviderStatusResponse]:
    statuses = await cloud_manager.get_all_provider_statuses(current_user.id, db)
    return [
        CloudProviderStatusResponse(
            provider=s.provider,
            name=s.name,
            description=s.description,
            supported_types=s.supported_types,
            is_configured=s.is_configured,
            source=s.source,
            masked_key=s.masked_key,
            api_connection_status=s.api_connection_status,
            last_tested_at=s.last_tested_at,
            last_test_status=s.last_test_status,
            last_test_message=s.last_test_message,
            doc_url=s.doc_url,
        )
        for s in statuses
    ]


@router.post(
    "/credentials",
    response_model=CloudOperationResponse,
    summary="Store User Cloud API Key",
    description="Encrypts and stores a third-party cloud API key in the user's isolated credential vault.",
)
async def save_cloud_credential(
    request: Request,
    payload: SaveCloudCredentialRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CloudOperationResponse:
    rate_limiter.check(
        request=request,
        action="cloud_credential_save",
        max_requests=10,
        window_seconds=60,
    )

    success, msg = await cloud_manager.save_user_credential(
        user_id=current_user.id,
        provider=payload.provider,
        api_key=payload.api_key,
        db=db,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg,
        )

    return CloudOperationResponse(
        success=True,
        message=msg,
        provider=payload.provider,
    )


@router.delete(
    "/credentials/{provider}",
    response_model=CloudOperationResponse,
    summary="Delete User Cloud API Key",
    description="Permanently deletes an analyst's stored cloud API key.",
)
async def delete_cloud_credential(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CloudOperationResponse:
    success, msg = await cloud_manager.delete_user_credential(
        user_id=current_user.id,
        provider=provider,
        db=db,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=msg,
        )

    return CloudOperationResponse(
        success=True,
        message=msg,
        provider=provider,
    )


@router.post(
    "/test-connection",
    response_model=CloudOperationResponse,
    summary="Test Third-Party API Connection",
    description="Tests connectivity and authorization for a configured or custom cloud API key.",
)
async def test_cloud_connection(
    request: Request,
    payload: TestCloudConnectionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CloudOperationResponse:
    rate_limiter.check(
        request=request,
        action="cloud_test_connection",
        max_requests=8,
        window_seconds=60,
    )

    success, msg = await cloud_manager.test_provider_connection(
        user_id=current_user.id,
        provider=payload.provider,
        custom_key=payload.api_key,
        db=db,
    )

    return CloudOperationResponse(
        success=success,
        message=msg,
        provider=payload.provider,
    )


@router.post(
    "/verify-text",
    response_model=CloudTextVerificationResponse,
    summary="Execute Optional Cloud Text Verification",
    description="Transmits text payload to external cloud providers strictly after explicit user consent is verified.",
)
async def verify_text_cloud(
    request: Request,
    payload: CloudTextVerificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CloudTextVerificationResponse:
    rate_limiter.check(
        request=request,
        action="cloud_verify_text",
        max_requests=10,
        window_seconds=60,
    )

    if not payload.user_consent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Explicit analyst consent is required before transmitting media to external third-party servers.",
        )

    res = await cloud_manager.verify_text(
        text=payload.text,
        user_id=current_user.id,
        user_consent=payload.user_consent,
        db=db,
        providers=payload.providers,
    )

    raw_results = res.get("results", {})
    item_results: dict[str, CloudProviderResultItem] = {}
    for p_name, r in raw_results.items():
        item_results[p_name] = CloudProviderResultItem(
            is_configured=r.get("is_configured", False),
            status=r.get("status", "PROVIDER_ERROR"),
            ai_score=r.get("ai_score"),
            human_score=r.get("human_score"),
            error_message=r.get("error_message"),
        )

    return CloudTextVerificationResponse(
        consent_granted=True,
        results=item_results,
        error=res.get("error"),
    )
