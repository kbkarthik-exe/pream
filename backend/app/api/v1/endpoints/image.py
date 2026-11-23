"""FastAPI router endpoints for AI Image Forensics."""

import io
import json
import logging

from backend.app.api.deps import get_current_user
from backend.app.core.config import settings
from backend.app.core.rate_limiter import rate_limiter
from backend.app.db.session import get_db
from backend.app.ml.image import image_detector
from backend.app.ml.image.forensics.security_hardening import validate_image_security
from backend.app.models.image_analysis import ImageAnalysisRecord
from backend.app.models.report import ForensicReport
from backend.app.models.user import User
from backend.app.schemas.image_analysis import (
    ImageAnalysisHistoryItem,
    ImageAnalysisResponse,
    ImageDetectorScore,
    ImageEnsembleBreakdown,
    ImageEvidenceItem,
    ImageHeatmapData,
    ProvenanceInfo,
)
from backend.app.services.pdf_generator import generate_image_analysis_pdf
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("aicf.api.image")

router = APIRouter()

SUPPORTED_FORMATS = {"JPEG", "JPG", "PNG", "WEBP"}


@router.post(
    "/analyze",
    response_model=ImageAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze Image Forensics",
    description=(
        "Executes fine-tuned Swin Transformer classification, 2D Fourier frequency domain "
        "analysis, Laplacian noise residuals, and provenance telemetry on uploaded images."
    ),
)
async def analyze_image(
    request: Request,
    file: UploadFile = File(...),
    save_to_cases: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ImageAnalysisResponse:
    # 1. Rate limiting check per client IP
    rate_limiter.check(
        request=request,
        action="image_analysis",
        max_requests=settings.RATE_LIMIT_IMAGE_MAX,
        window_seconds=settings.RATE_LIMIT_IMAGE_WINDOW,
    )

    # 2. Read bytes and validate file size
    try:
        file_bytes = await file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {exc}",
        ) from exc

    file_size = len(file_bytes)
    file_name = file.filename or "uploaded_image"

    # 3. Server-side Pre-decode Security Gate (Decompression bomb, dimension sniff, format validation)
    is_safe, rejection_reason, security_telemetry = validate_image_security(
        raw_bytes=file_bytes,
        max_pixels=settings.IMAGE_MAX_PIXELS,
        max_dimension=8192,
        max_file_bytes=settings.IMAGE_MAX_SIZE_BYTES,
    )
    if not is_safe:
        sec_status = security_telemetry.get("status", "UNKNOWN")
        logger.warning(
            "Security gate rejected upload '%s' [status=%s]: %s",
            file_name,
            sec_status,
            rejection_reason,
        )

        # Formulate safe, structured error responses adhering to API conventions without leaking internal info
        if sec_status == "EMPTY_STREAM":
            detail = "Uploaded file is empty (0 bytes). Please upload a valid image file."
        elif sec_status == "OVERSIZED_STREAM":
            max_mb = settings.IMAGE_MAX_SIZE_BYTES / (1024 * 1024)
            file_mb = file_size / (1024 * 1024)
            detail = f"File size ({file_mb:.1f} MB) exceeds maximum allowed limit of {max_mb:.0f} MB."
        elif sec_status in ("DECOMPRESSION_BOMB_DETECTED", "DECOMPRESSION_BOMB_TRIGGERED"):
            w = security_telemetry.get("width")
            h = security_telemetry.get("height")
            tot = security_telemetry.get("total_pixels")
            if w and h and tot:
                detail = (
                    f"Image resolution ({w}x{h} = {tot:,} pixels) exceeds "
                    f"maximum platform safety limit of {settings.IMAGE_MAX_PIXELS:,} pixels."
                )
            else:
                detail = (
                    f"Decompression bomb blocked: Image resolution exceeds "
                    f"maximum platform safety limit of {settings.IMAGE_MAX_PIXELS:,} pixels."
                )
        elif sec_status == "AXIS_LIMIT_EXCEEDED":
            w = security_telemetry.get("width", "unknown")
            h = security_telemetry.get("height", "unknown")
            detail = f"Image dimensions ({w}x{h}) exceed maximum allowable axis threshold of 8192px."
        elif sec_status == "UNSUPPORTED_FORMAT":
            fmt = security_telemetry.get("format", "UNKNOWN")
            detail = (
                f"Unsupported image format '{fmt}'. "
                f"Supported formats are: JPEG, PNG, and WebP."
            )
        elif sec_status == "MALFORMED_HEADER":
            detail = (
                "File content is not a recognized image or is corrupted. "
                "Only JPEG, PNG, and WebP are supported."
            )
        else:
            detail = "Uploaded file failed security validation checks."

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )

    # 4. Execute forensics engine analysis
    result = image_detector.analyze_image_bytes(file_bytes, file_name=file_name)

    evidence_items = [
        ImageEvidenceItem(
            signal=item["signal"],
            metric=item.get("metric"),
            finding=item["finding"],
        )
        for item in result.get("evidence", [])
    ]

    provenance_data = result.get("provenance", {})
    provenance_obj = (
        ProvenanceInfo(
            has_exif=provenance_data.get("has_exif", False),
            exif_summary=provenance_data.get("exif_summary", {}),
            has_ai_metadata=provenance_data.get("has_ai_metadata", False),
            ai_prompt_snippet=provenance_data.get("ai_prompt_snippet"),
            has_c2pa=provenance_data.get("has_c2pa", False),
            c2pa_finding=provenance_data.get("c2pa_finding", ""),
            provenance_summary=provenance_data.get("provenance_summary", ""),
        )
        if provenance_data
        else None
    )

    fft_features = result.get("fft_features", {})
    noise_features = result.get("noise_features", {})
    detector_scores_data = result.get("detector_scores", [])
    detector_scores = [ImageDetectorScore(**d) for d in detector_scores_data]
    ensemble_data = result.get("ensemble")
    ensemble_obj = ImageEnsembleBreakdown(**ensemble_data) if ensemble_data else None
    heatmap_data = result.get("heatmap")
    heatmap_obj = ImageHeatmapData(**heatmap_data) if heatmap_data else None

    # 5. Persist analysis record (with strict user isolation and privacy protection)
    record = ImageAnalysisRecord(
        user_id=current_user.id,
        file_hash=result["file_hash"],
        file_name=result["file_name"],
        file_size_bytes=result["file_size_bytes"],
        image_width=result["image_width"],
        image_height=result["image_height"],
        image_format=result["image_format"],
        model_name=result["model_name"],
        model_version=result["model_version"],
        classification=result["classification"],
        confidence_score=(
            result["confidence_score"] if result["confidence_score"] is not None else 0.0
        ),
        ai_probability=result.get("ai_probability") or 0.0,
        human_probability=result.get("human_probability") or 0.0,
        fft_high_freq_ratio=fft_features.get("high_freq_ratio", 0.0),
        spectral_anisotropy=fft_features.get("spectral_anisotropy", 0.0),
        noise_variance=noise_features.get("noise_variance", 0.0),
        has_ai_metadata=provenance_data.get("has_ai_metadata", False),
        has_c2pa=provenance_data.get("has_c2pa", False),
        evidence_json=json.dumps([item.model_dump() for item in evidence_items]),
        provenance_json=json.dumps(provenance_data),
        limitations_text=json.dumps(result.get("limitations", [])),
        ensemble_json=json.dumps(ensemble_data) if ensemble_data else None,
        heatmap_json=json.dumps(heatmap_data) if heatmap_data else None,
        status=result["status"],
        processing_time_ms=result["processing_time_ms"],
    )
    db.add(record)
    await db.flush()

    # 6. Optionally create linked case report in the forensic cases archive
    case_report_id: int | None = None
    if save_to_cases:
        score_display = (
            f"{(result['confidence_score'] * 100):.1f}%"
            if result["confidence_score"] is not None
            else "N/A"
        )
        summary_text = (
            f"Classification: {result['classification']} (Confidence: {score_display}). "
            f"File: {file_name} ({result['image_width']}x{result['image_height']}). "
            f"SHA-256: {result['file_hash'][:12]}... | "
            f"FFT Anisotropy: {fft_features.get('spectral_anisotropy', 0.0):.2f}, "
            f"Noise Var: {noise_features.get('noise_variance', 0.0):.1f}."
        )
        report = ForensicReport(
            user_id=current_user.id,
            title=f"Image Forensics: {file_name}",
            media_type="image",
            summary=summary_text,
            is_private=True,
        )
        db.add(report)
        await db.flush()
        case_report_id = report.id

    await db.commit()
    await db.refresh(record)

    return ImageAnalysisResponse(
        analysis_id=record.id,
        user_id=record.user_id,
        file_hash=record.file_hash,
        file_name=record.file_name,
        file_size_bytes=record.file_size_bytes,
        image_width=record.image_width,
        image_height=record.image_height,
        image_format=record.image_format,
        model_name=record.model_name,
        model_version=record.model_version,
        status=record.status,
        classification=record.classification,
        confidence_score=result["confidence_score"],
        ai_probability=result.get("ai_probability"),
        human_probability=result.get("human_probability"),
        raw_score=result.get("raw_score"),
        fft_high_freq_ratio=record.fft_high_freq_ratio,
        spectral_anisotropy=record.spectral_anisotropy,
        noise_variance=record.noise_variance,
        has_ai_metadata=record.has_ai_metadata,
        has_c2pa=record.has_c2pa,
        provenance=provenance_obj,
        evidence=evidence_items,
        limitations=result.get("limitations", []),
        detector_scores=detector_scores,
        ensemble=ensemble_obj,
        heatmap=heatmap_obj,
        processing_time_ms=record.processing_time_ms,
        created_at=record.created_at,
        case_report_id=case_report_id,
    )


@router.get(
    "/history",
    response_model=list[ImageAnalysisHistoryItem],
    status_code=status.HTTP_200_OK,
    summary="List User Image Analyses",
    description="Returns previous image forensic analyses performed by the authenticated analyst.",
)
async def list_image_analyses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ImageAnalysisHistoryItem]:
    stmt = (
        select(ImageAnalysisRecord)
        .where(ImageAnalysisRecord.user_id == current_user.id)
        .order_by(ImageAnalysisRecord.created_at.desc())
        .limit(50)
    )
    result = await db.execute(stmt)
    records = result.scalars().all()
    return [ImageAnalysisHistoryItem.model_validate(r) for r in records]


@router.get(
    "/{analysis_id}",
    response_model=ImageAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Specific Image Analysis Record",
    description=(
        "Retrieves a specific image analysis record with strict cross-user isolation checks."
    ),
)
async def get_image_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ImageAnalysisResponse:
    stmt = select(ImageAnalysisRecord).where(ImageAnalysisRecord.id == analysis_id)
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image analysis record not found.",
        )

    # Cross-account isolation check
    if record.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You cannot view analysis records created by other analysts.",
        )

    # Parse stored JSON fields
    try:
        evidence_list = json.loads(record.evidence_json)
        evidence_items = [
            ImageEvidenceItem(
                signal=item["signal"],
                metric=item.get("metric"),
                finding=item["finding"],
            )
            for item in evidence_list
        ]
    except Exception:
        evidence_items = []

    try:
        prov_dict = json.loads(record.provenance_json)
        provenance_obj = (
            ProvenanceInfo(
                has_exif=prov_dict.get("has_exif", False),
                exif_summary=prov_dict.get("exif_summary", {}),
                has_ai_metadata=prov_dict.get("has_ai_metadata", False),
                ai_prompt_snippet=prov_dict.get("ai_prompt_snippet"),
                has_c2pa=prov_dict.get("has_c2pa", False),
                c2pa_finding=prov_dict.get("c2pa_finding", ""),
                provenance_summary=prov_dict.get("provenance_summary", ""),
            )
            if prov_dict
            else None
        )
    except Exception:
        provenance_obj = None

    try:
        limitations = json.loads(record.limitations_text)
    except Exception:
        limitations = []

    ensemble_obj: ImageEnsembleBreakdown | None = None
    detector_scores: list[ImageDetectorScore] = []
    if getattr(record, "ensemble_json", None):
        try:
            ens_dict = json.loads(record.ensemble_json)
            if ens_dict:
                scores_data = ens_dict.get("detector_scores", [])
                detector_scores = [ImageDetectorScore(**s) for s in scores_data]
                ensemble_obj = ImageEnsembleBreakdown(
                    consensus_score=ens_dict["consensus_score"],
                    confidence=ens_dict["confidence"],
                    classification=ens_dict["classification"],
                    temperature_applied=ens_dict["temperature_applied"],
                    covariance_penalty=ens_dict["covariance_penalty"],
                    spectral_prior_weight=ens_dict["spectral_prior_weight"],
                    active_detectors_count=ens_dict["active_detectors_count"],
                    notes=ens_dict.get("notes", []),
                )
        except Exception:
            ensemble_obj = None

    heatmap_obj: ImageHeatmapData | None = None
    if getattr(record, "heatmap_json", None):
        try:
            heat_dict = json.loads(record.heatmap_json)
            if heat_dict:
                heatmap_obj = ImageHeatmapData(**heat_dict)
        except Exception:
            heatmap_obj = None

    return ImageAnalysisResponse(
        analysis_id=record.id,
        user_id=record.user_id,
        file_hash=record.file_hash,
        file_name=record.file_name,
        file_size_bytes=record.file_size_bytes,
        image_width=record.image_width,
        image_height=record.image_height,
        image_format=record.image_format,
        model_name=record.model_name,
        model_version=record.model_version,
        status=record.status,
        classification=record.classification,
        confidence_score=record.confidence_score,
        ai_probability=record.ai_probability,
        human_probability=record.human_probability,
        raw_score=record.ai_probability,
        fft_high_freq_ratio=record.fft_high_freq_ratio,
        spectral_anisotropy=record.spectral_anisotropy,
        noise_variance=record.noise_variance,
        has_ai_metadata=record.has_ai_metadata,
        has_c2pa=record.has_c2pa,
        provenance=provenance_obj,
        evidence=evidence_items,
        limitations=limitations,
        detector_scores=detector_scores,
        ensemble=ensemble_obj,
        heatmap=heatmap_obj,
        processing_time_ms=record.processing_time_ms,
        created_at=record.created_at,
        case_report_id=None,
    )


@router.get(
    "/{analysis_id}/pdf",
    summary="Download Image Analysis PDF Report",
    description="Streams an explainable forensic PDF report for a recorded image analysis.",
    response_class=Response,
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Returns the generated forensic examination PDF.",
        }
    },
)
async def download_image_analysis_pdf(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    record = await db.get(ImageAnalysisRecord, analysis_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image analysis record #{analysis_id} not found.",
        )

    if record.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You cannot export another analyst's private forensic analysis.",
        )

    analyst_name = current_user.full_name or current_user.username
    pdf_bytes = generate_image_analysis_pdf(record, analyst_name=analyst_name)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="AICF-Image-Report-{record.id:05d}.pdf"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
        },
    )
