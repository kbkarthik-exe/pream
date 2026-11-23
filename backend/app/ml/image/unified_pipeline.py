"""AICF Unified Image Analysis Pipeline Orchestrator.

Orchestrates multi-dimensional image authenticity analysis across:
- Ingestion Security Hardening (security_hardening.py)
- Dimension A: Vision Transformer AI Synthetic Detection (detector.py)
- Stage 1: Generator & Prompt Attribution Engine (generator_attribution.py)
- Dimension B: Image Forensics & Manipulation Detection (evidence_fusion.py)

Strict Architectural Invariants:
1. Dimension Independence: Dimension B manipulation findings never alter Dimension A P(AI).
2. Attribution Independence: Generator attribution never overwrites Dimension A P(AI).
3. Evidence Independence: Absence of manipulation seams never implies full synthesis or authentic reality.
4. Calibration Disclaimer: Dimension B confidence is strictly typed as 'HEURISTIC_SCORE'.
5. Provenance Disclaimer: C2PA certifies signer identity, never visual factual truth.
6. Baseline Immutability: detector.py independently decodes raw bytes per its baseline design;
   pil_img is safely loaded once and shared between attribution and forensics.
"""

from __future__ import annotations

import io
import time
import hashlib
from dataclasses import asdict, dataclass, field
from typing import Any

from PIL import Image

from backend.app.ml.image.detector import ImageForensicsDetector, image_detector
from backend.app.ml.image.generator_attribution import (
    EvidenceTier,
    GeneratorAttributionResult,
    GeneratorOutcome,
    attribute_generator,
)
from backend.app.ml.image.forensics.evidence_fusion import run_forensic_investigation
from backend.app.ml.image.forensics.schemas import ConfidenceType, ManipulationVerdict
from backend.app.ml.image.forensics.security_hardening import (
    DEFAULT_MAX_DIMENSION,
    DEFAULT_MAX_FILE_BYTES,
    DEFAULT_MAX_PIXELS,
    ImageSecurityException,
    validate_image_security,
)


@dataclass
class DimensionAResult:
    """Encapsulates Dimension A: Vision Transformer AI-generation detection results."""
    status: str  # "SUCCESS" | "INCONCLUSIVE" | "FAILED"
    classification: str  # "LIKELY AI-GENERATED" | "LIKELY HUMAN" | "INCONCLUSIVE"
    confidence_score: float | None = None
    ai_probability: float | None = None
    human_probability: float | None = None
    raw_score: float | None = None
    model_name: str = "Swin-B+ViT"
    model_version: str = "2.0.0"
    detector_scores: list[dict[str, Any]] = field(default_factory=list)
    ensemble: dict[str, Any] | None = None
    heatmap: dict[str, Any] | None = None
    fft_features: dict[str, Any] = field(default_factory=dict)
    noise_features: dict[str, Any] = field(default_factory=dict)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    processing_time_ms: float = 0.0
    error: str | None = None


@dataclass
class AttributionResult:
    """Encapsulates Stage 1: Generator & Prompt attribution results."""
    status: str  # "SUCCESS" | "FAILED" | "SKIPPED"
    primary_generator: str = GeneratorOutcome.UNKNOWN.value
    confidence: float = 0.0
    evidence_tier: str = EvidenceTier.NONE.value
    generator_name: str | None = None
    generator_family: str | None = None
    attribution_confidence: float = 0.0
    outcome: str = "UNKNOWN_OR_NATURAL"  # "EXPLICIT_ATTRIBUTION" | "HEURISTIC_ATTRIBUTION" | "UNKNOWN_OR_NATURAL"
    provenance_findings: dict[str, Any] = field(default_factory=dict)
    metadata_findings: dict[str, Any] = field(default_factory=dict)
    statistical_findings: dict[str, Any] = field(default_factory=dict)
    heuristic_findings: dict[str, Any] = field(default_factory=dict)
    conflicting_evidence: bool = False
    limitations: list[str] = field(default_factory=list)
    processing_time_ms: float = 0.0
    error: str | None = None


@dataclass
class DimensionBResult:
    """Encapsulates Dimension B: Image forensics & manipulation analysis results."""
    status: str  # "SUCCESS" | "FAILED" | "SKIPPED"
    manipulation_verdict: str = ManipulationVerdict.NO_MANIPULATION_EVIDENCE_DETECTED.value
    heuristic_score: float = 0.0
    confidence_type: str = ConfidenceType.HEURISTIC_SCORE.value  # Strictly "HEURISTIC_SCORE"
    evidence_strength: str = "NONE"
    findings: list[dict[str, Any]] = field(default_factory=list)
    suspicious_regions: list[dict[str, Any]] = field(default_factory=list)
    metadata_summary: str = ""
    provenance_summary: str = ""
    localization_notes: list[str] = field(default_factory=list)
    disclaimers: list[str] = field(default_factory=list)
    c2pa_status: dict[str, Any] = field(default_factory=dict)
    analysis_coverage: dict[str, bool] = field(default_factory=dict)
    processing_time_ms: float = 0.0
    error: str | None = None


@dataclass
class UnifiedAnalysisResult:
    """Complete multi-dimensional analysis contract returned by UnifiedImagePipeline."""
    file_hash: str
    file_name: str
    file_size_bytes: int
    image_width: int
    image_height: int
    image_format: str
    overall_status: str  # "SUCCESS" | "PARTIAL" | "FAILED"
    dimension_a: DimensionAResult
    attribution: AttributionResult
    dimension_b: DimensionBResult
    total_processing_time_ms: float
    analysis_coverage: dict[str, bool] = field(default_factory=dict)
    skipped_modules: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize complete analysis contract to a JSON-compatible dictionary."""
        return asdict(self)


class UnifiedImagePipeline:
    """Orchestrates secure multi-dimensional image authenticity analysis.

    Coordinates:
    - Pre-decode Ingestion Security Validation
    - Dimension A: AI Generation Detection (ImageDetector)
    - Stage 1: Generator Attribution Engine (attribute_generator)
    - Dimension B: Image Forensics & Manipulation Detection (run_forensic_investigation)
    """

    def __init__(self, detector: ImageForensicsDetector | None = None) -> None:
        """Initialize pipeline with vision detector instance."""
        self.detector = detector or image_detector

    def analyze(
        self,
        raw_bytes: bytes,
        file_name: str = "uploaded_image",
        max_pixels: int = DEFAULT_MAX_PIXELS,
        max_dimension: int = DEFAULT_MAX_DIMENSION,
        max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    ) -> UnifiedAnalysisResult:
        """Execute secure, multi-dimensional forensic analysis on raw image bytes.

        Args:
            raw_bytes: Binary stream of the image file.
            file_name: Original uploaded filename.
            max_pixels: Maximum allowed pixel count threshold.
            max_dimension: Maximum allowed single-axis threshold.
            max_file_bytes: Maximum allowed byte stream size.

        Returns:
            UnifiedAnalysisResult with Dimension A, Attribution, and Dimension B outputs.

        Raises:
            ImageSecurityException: If the image violates container security,
                pixel bounds, axis limits, or decompression bomb defenses.
        """
        start_pipeline = time.perf_counter()
        file_hash = hashlib.sha256(raw_bytes).hexdigest()
        file_size = len(raw_bytes)
        skipped_modules: list[str] = []
        warnings: list[str] = []

        # -----------------------------------------------------------------
        # 1. Mandatory Ingestion Security Gate
        # -----------------------------------------------------------------
        is_safe, sec_reason, sec_telemetry = validate_image_security(
            raw_bytes=raw_bytes,
            max_pixels=max_pixels,
            max_dimension=max_dimension,
            max_file_bytes=max_file_bytes,
        )
        if not is_safe:
            # Under strict security requirements: NEVER invoke any downstream analysis module
            raise ImageSecurityException(
                sec_reason or "Image validation failed security checks."
            )

        width = sec_telemetry.get("width", 0)
        height = sec_telemetry.get("height", 0)
        img_format = sec_telemetry.get("format", "UNKNOWN")

        # -----------------------------------------------------------------
        # 2. Single Safe Image Lifecycle for Attribution & Forensics
        # -----------------------------------------------------------------
        # Note: detector.py independently decodes raw_bytes internally to preserve
        # its immutable baseline implementation. The loaded pil_img is shared
        # between attribute_generator and run_forensic_investigation.
        pil_img: Image.Image | None = None
        try:
            bio = io.BytesIO(raw_bytes)
            pil_img = Image.open(bio)
            pil_img.load()
            if not width or not height:
                width, height = pil_img.size
            if img_format == "UNKNOWN":
                img_format = (pil_img.format or "UNKNOWN").upper()
        except Exception as decode_err:
            warnings.append(f"Pillow raster load warning: {decode_err}")
            pil_img = None

        # -----------------------------------------------------------------
        # 3. Dimension A: AI Generation Detection (Protected Backbone)
        # -----------------------------------------------------------------
        dim_a_start = time.perf_counter()
        dim_a: DimensionAResult
        try:
            raw_det = self.detector.analyze_image_bytes(raw_bytes, file_name=file_name)
            det_status = raw_det.get("status", "SUCCESS")
            dim_a = DimensionAResult(
                status=det_status,
                classification=raw_det.get("classification", "INCONCLUSIVE"),
                confidence_score=raw_det.get("confidence_score"),
                ai_probability=raw_det.get("ai_probability"),
                human_probability=raw_det.get("human_probability"),
                raw_score=raw_det.get("raw_score"),
                model_name=raw_det.get("model_name", "Swin-B+ViT"),
                model_version=raw_det.get("model_version", "2.0.0"),
                detector_scores=raw_det.get("detector_scores", []),
                ensemble=raw_det.get("ensemble"),
                heatmap=raw_det.get("heatmap"),
                fft_features=raw_det.get("fft_features", {}),
                noise_features=raw_det.get("noise_features", {}),
                evidence=raw_det.get("evidence", []),
                limitations=raw_det.get("limitations", []),
                processing_time_ms=round((time.perf_counter() - dim_a_start) * 1000, 2),
                error=raw_det.get("error") if det_status == "FAILED" else None,
            )
        except Exception as exc:
            skipped_modules.append("dimension_a")
            warnings.append(f"Dimension A failure: {exc}")
            dim_a = DimensionAResult(
                status="FAILED",
                classification="INCONCLUSIVE",
                confidence_score=None,
                ai_probability=None,
                human_probability=None,
                raw_score=None,
                processing_time_ms=round((time.perf_counter() - dim_a_start) * 1000, 2),
                error=f"Dimension A execution failed: {exc}",
            )

        # -----------------------------------------------------------------
        # 4. Stage 1: Generator Attribution Engine
        # -----------------------------------------------------------------
        attr_start = time.perf_counter()
        attribution: AttributionResult
        try:
            attr_raw = attribute_generator(image=pil_img, raw_bytes=raw_bytes)
            gen_family = None
            if attr_raw.primary_generator in ("MIDJOURNEY", "STABLE_DIFFUSION", "DALLE", "FLUX", "ADOBE_FIREFLY"):
                gen_family = "Diffusion"

            outcome_str = (
                "EXPLICIT_ATTRIBUTION"
                if attr_raw.evidence_tier in (EvidenceTier.DIRECT_PROVENANCE.value, EvidenceTier.METADATA_CLUES.value)
                else (
                    "HEURISTIC_ATTRIBUTION"
                    if attr_raw.evidence_tier == EvidenceTier.HEURISTIC_INDICATORS.value
                    else "UNKNOWN_OR_NATURAL"
                )
            )

            attribution = AttributionResult(
                status="SUCCESS",
                primary_generator=attr_raw.primary_generator,
                confidence=attr_raw.confidence,
                evidence_tier=attr_raw.evidence_tier,
                generator_name=attr_raw.primary_generator if attr_raw.primary_generator not in (GeneratorOutcome.UNKNOWN.value, GeneratorOutcome.INSUFFICIENT_EVIDENCE.value) else None,
                generator_family=gen_family,
                attribution_confidence=attr_raw.confidence,
                outcome=outcome_str,
                provenance_findings=attr_raw.provenance_findings,
                metadata_findings=attr_raw.metadata_findings,
                statistical_findings=attr_raw.statistical_findings,
                heuristic_findings=attr_raw.heuristic_findings,
                conflicting_evidence=attr_raw.conflicting_evidence,
                limitations=attr_raw.limitations,
                processing_time_ms=round((time.perf_counter() - attr_start) * 1000, 2),
            )
        except Exception as exc:
            skipped_modules.append("generator_attribution")
            warnings.append(f"Generator attribution failure: {exc}")
            attribution = AttributionResult(
                status="FAILED",
                primary_generator=GeneratorOutcome.UNKNOWN.value,
                confidence=0.0,
                evidence_tier=EvidenceTier.NONE.value,
                outcome="UNKNOWN_OR_NATURAL",
                processing_time_ms=round((time.perf_counter() - attr_start) * 1000, 2),
                error=f"Generator attribution execution failed: {exc}",
            )

        # -----------------------------------------------------------------
        # 5. Dimension B: Image Forensics & Manipulation Detection
        # -----------------------------------------------------------------
        dim_b_start = time.perf_counter()
        dim_b: DimensionBResult
        try:
            report = run_forensic_investigation(image=pil_img, raw_bytes=raw_bytes)
            # Serialize findings and suspicious regions to standard dictionaries
            findings_list = [asdict(f) for f in report.findings]
            regions_list = [asdict(r) for r in report.suspicious_regions]

            # Extract C2PA status dictionary from C2PA findings if present
            c2pa_finding = next((f for f in report.findings if "C2PA" in f.source or "PROVENANCE" in f.source), None)
            c2pa_status = c2pa_finding.metadata if c2pa_finding and c2pa_finding.metadata else {}

            # Compile analysis coverage from findings sources
            sources = {f.source for f in report.findings}
            coverage_map = {
                "metadata": any("METADATA" in s for s in sources),
                "c2pa": any("C2PA" in s or "PROVENANCE" in s for s in sources),
                "frequency": any("FREQUENCY" in s or "FFT" in s for s in sources),
                "ela": any("ELA" in s for s in sources),
                "noise": any("NOISE" in s for s in sources),
                "cmfd": any("COPY_MOVE" in s for s in sources),
            }

            dim_b = DimensionBResult(
                status="SUCCESS",
                manipulation_verdict=report.manipulation_verdict,
                heuristic_score=report.heuristic_score if report.heuristic_score is not None else report.confidence,
                confidence_type=report.confidence_type or ConfidenceType.HEURISTIC_SCORE.value,
                evidence_strength=report.evidence_strength,
                findings=findings_list,
                suspicious_regions=regions_list,
                metadata_summary=report.metadata_summary,
                provenance_summary=report.provenance_summary,
                disclaimers=report.disclaimers,
                c2pa_status=c2pa_status,
                analysis_coverage=coverage_map,
                processing_time_ms=round((time.perf_counter() - dim_b_start) * 1000, 2),
            )
        except Exception as exc:
            skipped_modules.append("dimension_b")
            warnings.append(f"Dimension B failure: {exc}")
            dim_b = DimensionBResult(
                status="FAILED",
                manipulation_verdict=ManipulationVerdict.INSUFFICIENT_EVIDENCE.value,
                heuristic_score=0.0,
                confidence_type=ConfidenceType.HEURISTIC_SCORE.value,
                evidence_strength="NONE",
                processing_time_ms=round((time.perf_counter() - dim_b_start) * 1000, 2),
                error=f"Dimension B forensic investigation failed: {exc}",
            )

        # Clean up in-memory image handles safely
        if pil_img is not None:
            try:
                pil_img.close()
            except Exception:
                pass

        # -----------------------------------------------------------------
        # 6. Overall Status Determination & Coverage Compilation
        # -----------------------------------------------------------------
        statuses = [dim_a.status, attribution.status, dim_b.status]
        if all(s == "SUCCESS" for s in statuses):
            overall_status = "SUCCESS"
        elif all(s == "FAILED" for s in statuses):
            overall_status = "FAILED"
        else:
            overall_status = "PARTIAL"

        coverage = {
            "dimension_a_ai_detection": dim_a.status == "SUCCESS",
            "generator_attribution": attribution.status == "SUCCESS",
            "dimension_b_forensics": dim_b.status == "SUCCESS",
            "metadata_forensics": dim_b.analysis_coverage.get("metadata", False),
            "c2pa_provenance": dim_b.analysis_coverage.get("c2pa", False),
            "frequency_domain": dim_b.analysis_coverage.get("frequency", False),
            "error_level_analysis": dim_b.analysis_coverage.get("ela", False),
            "noise_residuals": dim_b.analysis_coverage.get("noise", False),
            "copy_move_forgery": dim_b.analysis_coverage.get("cmfd", False),
        }

        total_elapsed_ms = round((time.perf_counter() - start_pipeline) * 1000, 2)

        return UnifiedAnalysisResult(
            file_hash=file_hash,
            file_name=file_name,
            file_size_bytes=file_size,
            image_width=width,
            image_height=height,
            image_format=img_format,
            overall_status=overall_status,
            dimension_a=dim_a,
            attribution=attribution,
            dimension_b=dim_b,
            total_processing_time_ms=total_elapsed_ms,
            analysis_coverage=coverage,
            skipped_modules=skipped_modules,
            warnings=warnings,
        )


# Singleton instance for high-throughput pipeline execution
unified_pipeline = UnifiedImagePipeline()
