"""FastAPI router endpoints for AI Video Forensics."""

import io
import json
import logging
from dataclasses import asdict
from pathlib import Path

from backend.app.api.deps import get_current_user
from backend.app.core.config import settings
from backend.app.core.rate_limiter import rate_limiter
from backend.app.db.session import get_db
from backend.app.ml.video import extract_video_frames, video_detector
from backend.app.models.report import ForensicReport
from backend.app.models.user import User
from backend.app.models.video import VideoAnalysisRecord
from backend.app.schemas.video_analysis import (
    FacialDeepfakeTelemetryInfo,
    FacialFrameRecordItem,
    FrameScoreItem,
    HiveAnalysisInfo,
    SuspiciousSegmentItem,
    TemporalTelemetryInfo,
    VideoAnalysisHistoryItem,
    VideoAnalysisResponse,
    VideoConsensusBreakdownInfo,
    VideoEvidenceItem,
)
from backend.app.services.pdf_generator import generate_video_analysis_pdf
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
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("aicf.api.video")

router = APIRouter()

SUPPORTED_EXTENSIONS = {".mp4", ".webm", ".mov"}


@router.post(
    "/analyze",
    response_model=VideoAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze Video Forensics",
    description=(
        "Executes uniform temporal keyframe extraction, Swin Vision Transformer frame screening, "
        "dedicated MesoNet-4 facial deepfake detection, boundary seam telemetry, and temporal flicker analysis."
    ),
)
async def analyze_video(
    request: Request,
    file: UploadFile = File(...),
    save_to_cases: bool = Form(False),
    query_hive: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VideoAnalysisResponse:
    # 1. Rate limiting check per client IP
    rate_limiter.check(
        request=request,
        action="video_analysis",
        max_requests=settings.RATE_LIMIT_VIDEO_MAX,
        window_seconds=settings.RATE_LIMIT_VIDEO_WINDOW,
    )

    # 2. Read bytes and validate file size
    try:
        file_bytes = await file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded video stream: {exc}",
        ) from exc

    file_size = len(file_bytes)
    file_name = file.filename or "uploaded_video.mp4"

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded video file is empty (0 bytes). Please upload a valid video file.",
        )

    if file_size > settings.VIDEO_MAX_FILE_SIZE_BYTES:
        max_mb = settings.VIDEO_MAX_FILE_SIZE_BYTES / (1024 * 1024)
        file_mb = file_size / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Video file size ({file_mb:.1f} MB) exceeds maximum allowed limit of {max_mb:.0f} MB.",
        )

    # 3. File extension validation
    ext = Path(file_name).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Unsupported video file extension '{ext}'. "
                "Only .mp4, .webm, and .mov video formats are supported."
            ),
        )

    # 4. Safe video ingestion & uniform keyframe sampling via OpenCV headless
    try:
        inspection = extract_video_frames(
            file_stream=io.BytesIO(file_bytes),
            file_name=file_name,
            max_file_size_bytes=settings.VIDEO_MAX_FILE_SIZE_BYTES,
            max_duration_seconds=settings.VIDEO_MAX_DURATION_SECONDS,
            max_resolution=settings.VIDEO_MAX_RESOLUTION,
            max_sampled_frames=settings.VIDEO_MAX_SAMPLED_FRAMES,
            sample_interval_seconds=settings.VIDEO_FRAME_SAMPLE_INTERVAL,
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        ) from val_err
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Unexpected video decoding failure: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Corrupted or unreadable video stream: {exc}",
        ) from exc

    # 5. Execute video detection engine
    try:
        outcome = await video_detector.detect_video(
            inspection=inspection,
            video_bytes=file_bytes,
            query_hive=query_hive,
        )
    except Exception as exc:
        logger.error("Video detection pipeline failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forensic detection pipeline failed during execution: {exc}",
        ) from exc

    # 6. Build schema objects
    frame_scores = [
        FrameScoreItem(
            frame_index=f.frame_index,
            timestamp_seconds=f.timestamp_seconds,
            ai_probability=f.ai_probability,
            human_probability=f.human_probability,
            classification=f.classification,
        )
        for f in outcome.frame_scores
    ]

    temporal_info = TemporalTelemetryInfo(
        mean_frame_difference=outcome.temporal_telemetry.mean_frame_difference,
        temporal_flicker_score=outcome.temporal_telemetry.temporal_flicker_score,
        suspicious_transition_timestamps=outcome.temporal_telemetry.suspicious_transition_timestamps,
        inter_frame_variance_ratio=outcome.temporal_telemetry.inter_frame_variance_ratio,
        motion_stability_score=outcome.temporal_telemetry.motion_stability_score,
        is_heuristic=outcome.temporal_telemetry.is_heuristic,
        heuristic_notes=outcome.temporal_telemetry.heuristic_notes,
    )

    facial_info: FacialDeepfakeTelemetryInfo | None = None
    if outcome.facial_telemetry:
        facial_info = FacialDeepfakeTelemetryInfo(
            model_name=outcome.facial_telemetry.model_name,
            model_version=outcome.facial_telemetry.model_version,
            model_license=outcome.facial_telemetry.model_license,
            availability=outcome.facial_telemetry.availability,
            total_faces_analyzed=outcome.facial_telemetry.total_faces_analyzed,
            frames_with_faces=outcome.facial_telemetry.frames_with_faces,
            total_frames_sampled=outcome.facial_telemetry.total_frames_sampled,
            mean_facial_manipulation_score=outcome.facial_telemetry.mean_facial_manipulation_score,
            max_facial_manipulation_score=outcome.facial_telemetry.max_facial_manipulation_score,
            mean_boundary_seam_delta=outcome.facial_telemetry.mean_boundary_seam_delta,
            max_boundary_seam_delta=outcome.facial_telemetry.max_boundary_seam_delta,
            peak_manipulation_timestamp=outcome.facial_telemetry.peak_manipulation_timestamp,
            low_resolution_frames_count=outcome.facial_telemetry.low_resolution_frames_count,
            timeline=[
                FacialFrameRecordItem(
                    frame_index=r.frame_index,
                    timestamp_seconds=r.timestamp_seconds,
                    face_count=r.face_count,
                    face_detected=r.face_detected,
                    primary_bbox=list(r.primary_bbox) if r.primary_bbox else None,
                    face_manipulation_score=r.face_manipulation_score,
                    boundary_seam_delta=r.boundary_seam_delta,
                    is_low_res=r.is_low_res,
                    verdict=r.verdict,
                )
                for r in outcome.facial_telemetry.timeline
            ],
            suspicious_temporal_segments=[
                SuspiciousSegmentItem(
                    start_timestamp_seconds=seg["start_timestamp_seconds"],
                    end_timestamp_seconds=seg["end_timestamp_seconds"],
                    frame_count=seg["frame_count"],
                    peak_manipulation_score=seg.get("peak_manipulation_score"),
                    peak_boundary_seam_delta=seg.get("peak_boundary_seam_delta", 0.0),
                    description=seg["description"],
                )
                for seg in outcome.facial_telemetry.suspicious_temporal_segments
            ],
            error_message=outcome.facial_telemetry.error_message,
        )

    consensus_info: VideoConsensusBreakdownInfo | None = None
    if outcome.consensus:
        consensus_info = VideoConsensusBreakdownInfo(
            verdict=outcome.consensus.verdict,
            confidence_score=outcome.consensus.confidence_score,
            composite_manipulation_score=outcome.consensus.composite_manipulation_score,
            frame_screening_score=outcome.consensus.frame_screening_score,
            frame_classifier_status=outcome.consensus.frame_classifier_status,
            facial_deepfake_score=outcome.consensus.facial_deepfake_score,
            facial_detector_status=outcome.consensus.facial_detector_status,
            boundary_seam_delta=outcome.consensus.boundary_seam_delta,
            temporal_flicker_score=outcome.consensus.temporal_flicker_score,
        )

    hive_info: HiveAnalysisInfo | None = None
    if outcome.hive_result:
        hive_info = HiveAnalysisInfo(
            is_configured=outcome.hive_result.is_configured,
            status=outcome.hive_result.status,
            provider_name=outcome.hive_result.provider_name,
            model_version=outcome.hive_result.model_version,
            ai_generated_score=outcome.hive_result.ai_generated_score,
            deepfake_score=outcome.hive_result.deepfake_score,
            classes_detected=outcome.hive_result.classes_detected,
            raw_response_summary=outcome.hive_result.raw_response_summary,
            error_message=outcome.hive_result.error_message,
        )

    evidence_items = [
        VideoEvidenceItem(
            signal=ev["signal"],
            metric=ev.get("metric"),
            finding=ev["finding"],
        )
        for ev in outcome.evidence
    ]

    # 7. Persist analysis record to database (with user isolation)
    record = VideoAnalysisRecord(
        user_id=current_user.id,
        file_hash=outcome.file_hash,
        file_name=outcome.file_name,
        file_size_bytes=outcome.file_size_bytes,
        duration_seconds=outcome.duration_seconds,
        video_width=outcome.width,
        video_height=outcome.height,
        fps=outcome.fps,
        total_frames=outcome.total_frames,
        sampled_frame_count=outcome.sampled_frame_count,
        model_name=outcome.model_name,
        model_version=outcome.model_version,
        frame_classifier_id=outcome.frame_classifier_id,
        classification=outcome.classification,
        consensus_verdict=outcome.consensus.verdict if outcome.consensus else None,
        confidence_score=outcome.confidence_score,
        ai_probability_mean=outcome.ai_probability_mean,
        ai_probability_max=outcome.ai_probability_max,
        peak_frame_timestamp=(
            outcome.peak_frame_timestamp
            if outcome.peak_frame_timestamp is not None
            else 0.0
        ),
        temporal_flicker_score=outcome.temporal_telemetry.temporal_flicker_score,
        face_deepfake_status=outcome.face_deepfake_status,
        has_hive_result=bool(outcome.hive_result and outcome.hive_result.status == "SUCCESS"),
        hive_score=(
            outcome.hive_result.ai_generated_score
            if outcome.hive_result and outcome.hive_result.status == "SUCCESS"
            else None
        ),
        frame_scores_json=json.dumps([asdict(f) for f in outcome.frame_scores]),
        temporal_telemetry_json=json.dumps(asdict(outcome.temporal_telemetry)),
        facial_telemetry_json=json.dumps(asdict(outcome.facial_telemetry)) if outcome.facial_telemetry else None,
        consensus_json=json.dumps(asdict(outcome.consensus)) if outcome.consensus else None,
        evidence_json=json.dumps(outcome.evidence),
        limitations_text=json.dumps(outcome.limitations),
        status=outcome.status,
        processing_time_ms=outcome.processing_time_ms,
    )
    db.add(record)
    await db.flush()

    # 8. Optionally create linked case report in the forensic cases archive
    case_report_id: int | None = None
    if save_to_cases:
        score_display = f"{(outcome.confidence_score * 100):.1f}%"
        verdict_str = outcome.consensus.verdict if outcome.consensus else outcome.classification
        summary_text = (
            f"Verdict: {verdict_str} (Confidence: {score_display}). "
            f"File: {file_name} ({outcome.width}x{outcome.height}, {outcome.duration_seconds:.1f}s, {outcome.fps} fps). "
            f"Sampled Frames: {outcome.sampled_frame_count} | Mean AI: {outcome.ai_probability_mean:.1%}, "
            f"Facial Status: {outcome.face_deepfake_status} | "
            f"Flicker Score: {outcome.temporal_telemetry.temporal_flicker_score:.4f}."
        )
        report = ForensicReport(
            user_id=current_user.id,
            title=f"Video Forensics: {file_name}",
            media_type="video",
            summary=summary_text,
            is_private=True,
        )
        db.add(report)
        await db.flush()
        case_report_id = report.id

    await db.commit()
    await db.refresh(record)

    return VideoAnalysisResponse(
        analysis_id=record.id,
        user_id=record.user_id,
        file_hash=record.file_hash,
        file_name=record.file_name,
        file_size_bytes=record.file_size_bytes,
        duration_seconds=record.duration_seconds,
        video_width=record.video_width,
        video_height=record.video_height,
        fps=record.fps,
        total_frames=record.total_frames,
        sampled_frame_count=record.sampled_frame_count,
        model_name=record.model_name,
        model_version=record.model_version,
        frame_classifier_id=record.frame_classifier_id,
        status=record.status,
        classification=record.classification,
        consensus_verdict=record.consensus_verdict,
        confidence_score=record.confidence_score,
        ai_probability_mean=record.ai_probability_mean,
        ai_probability_max=record.ai_probability_max,
        peak_frame_timestamp=record.peak_frame_timestamp,
        temporal_flicker_score=record.temporal_flicker_score,
        face_deepfake_status=record.face_deepfake_status,
        frame_scores=frame_scores,
        temporal_telemetry=temporal_info,
        facial_telemetry=facial_info,
        consensus=consensus_info,
        hive_result=hive_info,
        evidence=evidence_items,
        limitations=outcome.limitations,
        processing_time_ms=record.processing_time_ms,
        created_at=record.created_at,
        case_report_id=case_report_id,
    )


@router.get(
    "/history",
    response_model=list[VideoAnalysisHistoryItem],
    status_code=status.HTTP_200_OK,
    summary="List User Video Analyses",
    description="Returns previous video forensic analyses performed by the authenticated analyst.",
)
async def list_video_analyses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[VideoAnalysisHistoryItem]:
    stmt = (
        select(VideoAnalysisRecord)
        .where(VideoAnalysisRecord.user_id == current_user.id)
        .order_by(VideoAnalysisRecord.created_at.desc())
        .limit(50)
    )
    result = await db.execute(stmt)
    records = result.scalars().all()
    return [VideoAnalysisHistoryItem.model_validate(r) for r in records]


@router.get(
    "/analyses/{analysis_id}",
    response_model=VideoAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Specific Video Analysis Record",
    description="Retrieves a specific video analysis record with strict cross-user isolation checks.",
)
async def get_video_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VideoAnalysisResponse:
    stmt = select(VideoAnalysisRecord).where(VideoAnalysisRecord.id == analysis_id)
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video analysis record not found.",
        )

    # Cross-account isolation check
    if record.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You cannot view analysis records created by other analysts.",
        )

    # Parse stored JSON fields safely
    try:
        frames_data = json.loads(record.frame_scores_json)
        frame_scores = [FrameScoreItem(**item) for item in frames_data]
    except Exception:
        frame_scores = []

    try:
        temp_dict = json.loads(record.temporal_telemetry_json)
        temporal_info = TemporalTelemetryInfo(
            mean_frame_difference=temp_dict.get("mean_frame_difference", 0.0),
            temporal_flicker_score=temp_dict.get("temporal_flicker_score", 0.0),
            suspicious_transition_timestamps=temp_dict.get("suspicious_transition_timestamps", []),
            inter_frame_variance_ratio=temp_dict.get("inter_frame_variance_ratio", 0.0),
            motion_stability_score=temp_dict.get("motion_stability_score", 1.0),
            is_heuristic=temp_dict.get("is_heuristic", True),
            heuristic_notes=temp_dict.get("heuristic_notes", ""),
        )
    except Exception:
        temporal_info = None

    facial_info: FacialDeepfakeTelemetryInfo | None = None
    if getattr(record, "facial_telemetry_json", None):
        try:
            face_dict = json.loads(record.facial_telemetry_json)
            timeline_items = [
                FacialFrameRecordItem(
                    frame_index=item["frame_index"],
                    timestamp_seconds=item["timestamp_seconds"],
                    face_count=item["face_count"],
                    face_detected=item["face_detected"],
                    primary_bbox=item.get("primary_bbox"),
                    face_manipulation_score=item.get("face_manipulation_score"),
                    boundary_seam_delta=item.get("boundary_seam_delta"),
                    is_low_res=item.get("is_low_res", False),
                    verdict=item.get("verdict", "NO_FACE"),
                )
                for item in face_dict.get("timeline", [])
            ]
            seg_items = [
                SuspiciousSegmentItem(
                    start_timestamp_seconds=s["start_timestamp_seconds"],
                    end_timestamp_seconds=s["end_timestamp_seconds"],
                    frame_count=s["frame_count"],
                    peak_manipulation_score=s.get("peak_manipulation_score"),
                    peak_boundary_seam_delta=s.get("peak_boundary_seam_delta", 0.0),
                    description=s["description"],
                )
                for s in face_dict.get("suspicious_temporal_segments", [])
            ]
            facial_info = FacialDeepfakeTelemetryInfo(
                model_name=face_dict.get("model_name", "MesoNet-4 Facial Forensics Head"),
                model_version=face_dict.get("model_version", "1.0.0"),
                model_license=face_dict.get("model_license", "MIT / Research"),
                availability=face_dict.get("availability", record.face_deepfake_status),
                total_faces_analyzed=face_dict.get("total_faces_analyzed", 0),
                frames_with_faces=face_dict.get("frames_with_faces", 0),
                total_frames_sampled=face_dict.get("total_frames_sampled", 0),
                mean_facial_manipulation_score=face_dict.get("mean_facial_manipulation_score"),
                max_facial_manipulation_score=face_dict.get("max_facial_manipulation_score"),
                mean_boundary_seam_delta=face_dict.get("mean_boundary_seam_delta", 0.0),
                max_boundary_seam_delta=face_dict.get("max_boundary_seam_delta", 0.0),
                peak_manipulation_timestamp=face_dict.get("peak_manipulation_timestamp"),
                low_resolution_frames_count=face_dict.get("low_resolution_frames_count", 0),
                timeline=timeline_items,
                suspicious_temporal_segments=seg_items,
                error_message=face_dict.get("error_message"),
            )
        except Exception as exc:
            logger.warning("Failed to deserialize facial_telemetry_json: %s", exc)
            facial_info = None

    consensus_info: VideoConsensusBreakdownInfo | None = None
    if getattr(record, "consensus_json", None):
        try:
            cons_dict = json.loads(record.consensus_json)
            consensus_info = VideoConsensusBreakdownInfo(
                verdict=cons_dict.get("verdict", record.consensus_verdict or "Inconclusive"),
                confidence_score=cons_dict.get("confidence_score", record.confidence_score),
                composite_manipulation_score=cons_dict.get("composite_manipulation_score", 0.5),
                frame_screening_score=cons_dict.get("frame_screening_score", record.ai_probability_mean),
                frame_classifier_status=cons_dict.get("frame_classifier_status", "READY"),
                facial_deepfake_score=cons_dict.get("facial_deepfake_score"),
                facial_detector_status=cons_dict.get("facial_detector_status", record.face_deepfake_status),
                boundary_seam_delta=cons_dict.get("boundary_seam_delta", 0.0),
                temporal_flicker_score=cons_dict.get("temporal_flicker_score", record.temporal_flicker_score),
            )
        except Exception as exc:
            logger.warning("Failed to deserialize consensus_json: %s", exc)
            consensus_info = None

    try:
        ev_list = json.loads(record.evidence_json)
        evidence_items = [VideoEvidenceItem(**item) for item in ev_list]
    except Exception:
        evidence_items = []

    try:
        limitations = json.loads(record.limitations_text)
    except Exception:
        limitations = []

    hive_info: HiveAnalysisInfo | None = None
    if record.has_hive_result:
        hive_info = HiveAnalysisInfo(
            is_configured=True,
            status="SUCCESS",
            provider_name="Hive AI",
            ai_generated_score=record.hive_score,
            raw_response_summary="Verified via Hive AI adapter.",
        )

    return VideoAnalysisResponse(
        analysis_id=record.id,
        user_id=record.user_id,
        file_hash=record.file_hash,
        file_name=record.file_name,
        file_size_bytes=record.file_size_bytes,
        duration_seconds=record.duration_seconds,
        video_width=record.video_width,
        video_height=record.video_height,
        fps=record.fps,
        total_frames=record.total_frames,
        sampled_frame_count=record.sampled_frame_count,
        model_name=record.model_name,
        model_version=record.model_version,
        frame_classifier_id=record.frame_classifier_id,
        status=record.status,
        classification=record.classification,
        consensus_verdict=record.consensus_verdict,
        confidence_score=record.confidence_score,
        ai_probability_mean=record.ai_probability_mean,
        ai_probability_max=record.ai_probability_max,
        peak_frame_timestamp=record.peak_frame_timestamp,
        temporal_flicker_score=record.temporal_flicker_score,
        face_deepfake_status=record.face_deepfake_status,
        frame_scores=frame_scores,
        temporal_telemetry=temporal_info,
        facial_telemetry=facial_info,
        consensus=consensus_info,
        hive_result=hive_info,
        evidence=evidence_items,
        limitations=limitations,
        processing_time_ms=record.processing_time_ms,
        created_at=record.created_at,
        case_report_id=None,
    )


@router.get(
    "/analyses/{analysis_id}/pdf",
    summary="Download Video Analysis PDF Report",
    description="Streams an official, professional forensic PDF report for a recorded video analysis.",
    response_class=Response,
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Returns the generated forensic video examination PDF dossier.",
        }
    },
)
async def download_video_analysis_pdf(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    stmt = select(VideoAnalysisRecord).where(VideoAnalysisRecord.id == analysis_id)
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video analysis record #{analysis_id} not found.",
        )

    if record.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You cannot export another analyst's private forensic analysis.",
        )

    analyst_name = current_user.full_name or current_user.username
    try:
        pdf_bytes = generate_video_analysis_pdf(record, analyst_name=analyst_name)
    except Exception as exc:
        logger.error("Failed to generate video analysis PDF: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate forensic PDF report: {exc}",
        ) from exc

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="AICF-Video-Report-{record.id:05d}.pdf"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )
