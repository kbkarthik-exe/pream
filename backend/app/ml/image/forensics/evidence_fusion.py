"""Evidence fusion engine: multi-modal forensic synthesis and manipulation classification."""

from __future__ import annotations

from PIL import Image

from .frequency_forensics import analyze_frequency_domain
from .localization import localize_suspicious_regions
from .manipulation_detector import analyze_manipulation
from .metadata_forensics import analyze_metadata
from .provenance_verifier import verify_provenance
from .schemas import (
    EvidenceFinding,
    ForensicReport,
    ManipulationVerdict,
    Reliability,
    Severity,
)
from .security_hardening import validate_image_security


def run_forensic_investigation(
    image: Image.Image | None,
    raw_bytes: bytes,
) -> ForensicReport:
    """Execute complete multi-modal forensic investigation across all forensic tiers.

    Maintains strict independence between synthetic detection (Dimension A)
    and manipulation analysis (Dimension B).

    Args:
        image: Pillow Image instance (optional if raw_bytes provided).
        raw_bytes: Raw bytes of the image file.

    Returns:
        ForensicReport containing findings, manipulation verdict, and regions.
    """
    disclaimers: list[str] = [
        "Forensic indicators are probabilistic and exploratory; heuristics do NOT constitute definitive legal proof.",
        "Absence of manipulation seams does NOT prove an image is authentic or fully AI-synthesized.",
        "Absence of C2PA Content Credentials does NOT imply human or authentic camera origin.",
        "Error Level Analysis (ELA) and noise residuals are sensitive to legitimate high-contrast natural contours.",
        "Confidence values represent uncalibrated heuristic rule-tier scores and are NOT calibrated statistical probabilities.",
    ]

    # Validate inputs
    if not raw_bytes or len(raw_bytes) == 0:
        return ForensicReport(
            manipulation_verdict=ManipulationVerdict.INSUFFICIENT_EVIDENCE.value,
            confidence=0.0,
            findings=[
                EvidenceFinding(
                    source="CONTAINER_VALIDATION",
                    description="Input image bytes are empty or corrupted.",
                    severity=Severity.HIGH,
                    reliability=Reliability.HEURISTIC,
                    limitations=["Analysis aborted due to zero-byte or unreadable file stream."],
                )
            ],
            disclaimers=disclaimers,
        )

    # Pre-flight Image Security & Decompression Bomb Validation
    is_safe, sec_reason, sec_telemetry = validate_image_security(raw_bytes)
    if not is_safe:
        return ForensicReport(
            manipulation_verdict=ManipulationVerdict.INSUFFICIENT_EVIDENCE.value,
            confidence=0.0,
            findings=[
                EvidenceFinding(
                    source="CONTAINER_SECURITY",
                    description=f"Image rejected by security hardening gate: {sec_reason}",
                    severity=Severity.HIGH,
                    reliability=Reliability.HEURISTIC,
                    limitations=["Stream violated memory bounds, dimension limits, or decompression-bomb constraints."],
                    metadata=sec_telemetry,
                )
            ],
            disclaimers=disclaimers,
        )

    # Resolve Image instance and ensure container info is loaded
    if image is None or (not getattr(image, "info", None) and raw_bytes):
        try:
            import io
            reloaded = Image.open(io.BytesIO(raw_bytes))
            if image is None or getattr(reloaded, "info", None):
                image = reloaded
        except Exception as e:
            if image is None:
                return ForensicReport(
                    manipulation_verdict=ManipulationVerdict.INSUFFICIENT_EVIDENCE.value,
                    confidence=0.0,
                    findings=[
                        EvidenceFinding(
                            source="CONTAINER_VALIDATION",
                            description=f"Unable to parse image raster from stream: {e}",
                            severity=Severity.HIGH,
                            reliability=Reliability.HEURISTIC,
                            limitations=["File container does not conform to supported image raster specifications."],
                        )
                    ],
                    disclaimers=disclaimers,
                )

    try:
        width, height = image.size
    except Exception:
        return ForensicReport(
            manipulation_verdict=ManipulationVerdict.INSUFFICIENT_EVIDENCE.value,
            confidence=0.0,
            findings=[
                EvidenceFinding(
                    source="CONTAINER_VALIDATION",
                    description="Failed reading image geometry dimensions.",
                    severity=Severity.HIGH,
                    reliability=Reliability.HEURISTIC,
                    limitations=["Malformed image header."],
                )
            ],
            disclaimers=disclaimers,
        )

    # Resolution threshold gate
    if width < 32 or height < 32:
        return ForensicReport(
            manipulation_verdict=ManipulationVerdict.INSUFFICIENT_EVIDENCE.value,
            confidence=0.0,
            findings=[
                EvidenceFinding(
                    source="GEOMETRY_GATE",
                    description=f"Image dimensions ({width}x{height}) fall below minimum forensic threshold (32x32).",
                    severity=Severity.INFORMATIONAL,
                    reliability=Reliability.HEURISTIC,
                    limitations=["Macro-block Fourier and ELA decomposition require sufficient spatial extent."],
                )
            ],
            disclaimers=disclaimers,
        )

    all_findings: list[EvidenceFinding] = []

    # 1. Metadata Forensics
    metadata_summary, meta_findings = analyze_metadata(image)
    all_findings.extend(meta_findings)

    # 2. Provenance Verification (C2PA)
    provenance_summary, prov_findings = verify_provenance(raw_bytes)
    all_findings.extend(prov_findings)

    # 3. Frequency Domain Analysis
    freq_summary, freq_findings = analyze_frequency_domain(image)
    all_findings.extend(freq_findings)

    # 4. Manipulation Forensics (ELA, Noise, Copy-Move)
    manip_summary, manip_findings, anomaly_map = analyze_manipulation(image, raw_bytes)
    all_findings.extend(manip_findings)

    # 5. Spatial Localization of Suspicious Regions
    suspicious_regions = localize_suspicious_regions(anomaly_map, width, height)

    # -------------------------------------------------------------------------
    # Evidence Fusion & Manipulation Verdict Synthesis
    # -------------------------------------------------------------------------
    copy_move_detected = manip_summary.get("copy_move_detected", False)
    noise_splicing_detected = manip_summary.get("noise_splicing_detected", False)
    ela_inconsistency_detected = manip_summary.get("ela_inconsistency_detected", False)
    editing_software_detected = bool(metadata_summary.get("editing_software_detected", []))
    generative_metadata_detected = bool(metadata_summary.get("generative_software_detected", []))

    verdict: ManipulationVerdict
    heuristic_score: float
    evidence_strength: str

    # Case A: Copy-Move Forgery
    if copy_move_detected:
        verdict = ManipulationVerdict.SUSPECTED_SPLICING
        heuristic_score = 0.75
        evidence_strength = "STRONG"

    # Case B: Localized Inpainting (ELA block anomaly + localized region + generative or editing cues)
    elif ela_inconsistency_detected and (suspicious_regions or generative_metadata_detected):
        verdict = ManipulationVerdict.SUSPECTED_INPAINTING
        heuristic_score = 0.70
        evidence_strength = "STRONG"

    # Case C: Image Splicing (Noise gradient discrepancy across quadrants)
    elif noise_splicing_detected and (suspicious_regions or editing_software_detected):
        verdict = ManipulationVerdict.SUSPECTED_SPLICING
        heuristic_score = 0.65
        evidence_strength = "MODERATE"

    # Case D: Local Retouching (Editing software tags present or minor ELA variance without sharp seams)
    elif editing_software_detected or (ela_inconsistency_detected and not suspicious_regions):
        verdict = ManipulationVerdict.SUSPECTED_RETOUCHING
        heuristic_score = 0.55
        evidence_strength = "WEAK"

    # Case E: No Evidence Detected (Consistent compression and noise, no anomalous regions)
    else:
        verdict = ManipulationVerdict.NO_MANIPULATION_EVIDENCE_DETECTED
        heuristic_score = 0.0
        evidence_strength = "NONE"

    return ForensicReport(
        manipulation_verdict=verdict.value,
        confidence=heuristic_score,
        confidence_type="HEURISTIC_SCORE",
        is_calibrated=False,
        evidence_strength=evidence_strength,
        heuristic_score=heuristic_score,
        model_probability=None,
        calibrated_confidence=None,
        calibration_limitation=(
            "Empirical probability calibration (e.g. Platt scaling / isotonic regression) is not active. "
            "Value represents an uncalibrated heuristic rule-tier score."
        ),
        findings=all_findings,
        suspicious_regions=suspicious_regions,
        metadata_summary=metadata_summary,
        provenance_summary=provenance_summary,
        disclaimers=disclaimers,
    )
