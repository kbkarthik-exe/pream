"""Advanced image forensics and manipulation detection package for AICF Phase 2."""

from .evidence_fusion import run_forensic_investigation
from .frequency_forensics import analyze_frequency_domain
from .localization import localize_suspicious_regions
from .manipulation_detector import analyze_manipulation
from .metadata_forensics import analyze_metadata
from .provenance_verifier import verify_provenance
from .schemas import (
    AssetBindingStatus,
    CertificateStatus,
    ConfidenceType,
    EvidenceFinding,
    EvidenceStrength,
    ForensicReport,
    ManifestStatus,
    ManipulationVerdict,
    ProvenanceStatus,
    Reliability,
    Severity,
    SignatureStatus,
    SuspiciousRegion,
)
from .security_hardening import validate_image_security

__all__ = [
    "run_forensic_investigation",
    "analyze_metadata",
    "verify_provenance",
    "analyze_frequency_domain",
    "analyze_manipulation",
    "localize_suspicious_regions",
    "validate_image_security",
    "EvidenceFinding",
    "ForensicReport",
    "ManipulationVerdict",
    "ProvenanceStatus",
    "ManifestStatus",
    "SignatureStatus",
    "CertificateStatus",
    "AssetBindingStatus",
    "ConfidenceType",
    "EvidenceStrength",
    "Reliability",
    "Severity",
    "SuspiciousRegion",
]
