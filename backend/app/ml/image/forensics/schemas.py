"""Structured schemas and finding representations for image forensics."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    """Severity or importance level of a forensic finding."""

    INFORMATIONAL = "INFORMATIONAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Reliability(str, Enum):
    """Scientific reliability tier of a forensic indicator."""

    CRYPTOGRAPHIC_VERIFIED = "CRYPTOGRAPHIC_VERIFIED"
    STATISTICAL_SUPPORTED = "STATISTICAL_SUPPORTED"
    HEURISTIC = "HEURISTIC"
    UNVERIFIED = "UNVERIFIED"


class ManipulationVerdict(str, Enum):
    """Supported manipulation classification states (Dimension B)."""

    SUSPECTED_INPAINTING = "SUSPECTED_INPAINTING"
    SUSPECTED_SPLICING = "SUSPECTED_SPLICING"
    SUSPECTED_RETOUCHING = "SUSPECTED_RETOUCHING"
    NO_MANIPULATION_EVIDENCE_DETECTED = "NO_MANIPULATION_EVIDENCE_DETECTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class ManifestStatus(str, Enum):
    """C2PA / JUMBF container manifest parsing status."""

    NO_MANIFEST_PRESENT = "NO_MANIFEST_PRESENT"
    MANIFEST_MARKERS_DETECTED = "MANIFEST_MARKERS_DETECTED"
    MANIFEST_PARSED = "MANIFEST_PARSED"


class SignatureStatus(str, Enum):
    """Cryptographic signature validation status."""

    SIGNATURE_VALID = "SIGNATURE_VALID"
    SIGNATURE_INVALID = "SIGNATURE_INVALID"
    SIGNATURE_UNVERIFIED = "SIGNATURE_UNVERIFIED"
    NO_SIGNATURE_PRESENT = "NO_SIGNATURE_PRESENT"


class CertificateStatus(str, Enum):
    """X.509 certificate trust-anchor validation status."""

    CERTIFICATE_TRUSTED = "CERTIFICATE_TRUSTED"
    CERTIFICATE_UNTRUSTED = "CERTIFICATE_UNTRUSTED"
    NO_CERTIFICATE_PRESENT = "NO_CERTIFICATE_PRESENT"


class AssetBindingStatus(str, Enum):
    """Claim-to-asset pixel data hash binding status."""

    ASSET_BINDING_VALID = "ASSET_BINDING_VALID"
    ASSET_BINDING_INVALID = "ASSET_BINDING_INVALID"
    ASSET_BINDING_UNVERIFIED = "ASSET_BINDING_UNVERIFIED"
    BINDING_UNVERIFIED = "ASSET_BINDING_UNVERIFIED"


class ConfidenceType(str, Enum):
    """Classification of confidence estimation methodology."""

    HEURISTIC_SCORE = "HEURISTIC_SCORE"
    MODEL_PROBABILITY = "MODEL_PROBABILITY"
    CALIBRATED_CONFIDENCE = "CALIBRATED_CONFIDENCE"


class EvidenceStrength(str, Enum):
    """Categorical strength of accumulated forensic evidence."""

    NONE = "NONE"
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"
    CONCLUSIVE = "CONCLUSIVE"


class ProvenanceStatus(str, Enum):
    """C2PA / Content Credentials overall provenance status."""

    NO_MANIFEST_PRESENT = "NO_MANIFEST_PRESENT"
    MANIFEST_MARKERS_DETECTED = "MANIFEST_MARKERS_DETECTED"
    MANIFEST_PARSED = "MANIFEST_PARSED"
    SIGNATURE_VALID = "SIGNATURE_VALID"
    SIGNATURE_INVALID = "SIGNATURE_INVALID"
    SIGNATURE_UNVERIFIED = "SIGNATURE_UNVERIFIED"
    CERTIFICATE_TRUSTED = "CERTIFICATE_TRUSTED"
    CERTIFICATE_UNTRUSTED = "CERTIFICATE_UNTRUSTED"
    ASSET_BINDING_VALID = "ASSET_BINDING_VALID"
    ASSET_BINDING_INVALID = "ASSET_BINDING_INVALID"

    # Backward compatibility aliases
    UNVERIFIED_MANIFEST_ONLY = "MANIFEST_MARKERS_DETECTED"
    INVALID_OR_TAMPERED_SIGNATURE = "SIGNATURE_INVALID"
    CRYPTOGRAPHICALLY_VERIFIED = "SIGNATURE_VALID"


@dataclass
class EvidenceFinding:
    """Individual forensic finding with source, severity, reliability, and limitations."""

    source: str
    description: str
    severity: Severity = Severity.INFORMATIONAL
    reliability: Reliability = Reliability.HEURISTIC
    limitations: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize finding to dictionary."""
        d = asdict(self)
        d["severity"] = self.severity.value
        d["reliability"] = self.reliability.value
        return d


@dataclass
class SuspiciousRegion:
    """Localized spatial region exhibiting anomalous forensic signals."""

    region_id: str
    quadrant: str  # e.g., "Q1_TOP_LEFT", "Q2_TOP_RIGHT", "Q3_BOTTOM_LEFT", "Q4_BOTTOM_RIGHT"
    bounding_box: tuple[int, int, int, int]  # (ymin, xmin, ymax, xmax) in pixels
    normalized_box: tuple[float, float, float, float]  # (ymin, xmin, ymax, xmax) in [0, 1]
    anomalous_block_count: int
    primary_indicator: str
    confidence: float  # Bounded [0.0, 1.0]

    def to_dict(self) -> dict[str, Any]:
        """Serialize region to dictionary."""
        return asdict(self)


@dataclass
class ForensicReport:
    """Comprehensive, multi-dimensional forensic analysis report."""

    manipulation_verdict: str
    confidence: float
    confidence_type: str = "HEURISTIC_SCORE"
    is_calibrated: bool = False
    evidence_strength: str = "NONE"
    heuristic_score: float = 0.0
    model_probability: float | None = None
    calibrated_confidence: float | None = None
    calibration_limitation: str = (
        "Empirical probability calibration (e.g. Platt scaling / isotonic regression) is not active. "
        "Value represents an uncalibrated heuristic rule-tier score."
    )
    findings: list[EvidenceFinding] = field(default_factory=list)
    suspicious_regions: list[SuspiciousRegion] = field(default_factory=list)
    metadata_summary: dict[str, Any] = field(default_factory=dict)
    provenance_summary: dict[str, Any] = field(default_factory=dict)
    disclaimers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize full forensic report to dictionary."""
        return {
            "manipulation_verdict": self.manipulation_verdict,
            "confidence": round(self.confidence, 4),
            "confidence_type": self.confidence_type,
            "is_calibrated": self.is_calibrated,
            "evidence_strength": self.evidence_strength,
            "heuristic_score": round(self.heuristic_score, 4),
            "model_probability": round(self.model_probability, 4) if self.model_probability is not None else None,
            "calibrated_confidence": round(self.calibrated_confidence, 4) if self.calibrated_confidence is not None else None,
            "calibration_limitation": self.calibration_limitation,
            "findings": [f.to_dict() for f in self.findings],
            "suspicious_regions": [r.to_dict() for r in self.suspicious_regions],
            "metadata_summary": self.metadata_summary,
            "provenance_summary": self.provenance_summary,
            "disclaimers": self.disclaimers,
        }
