"""C2PA / JUMBF Content Credentials parsing and cryptographic provenance verification."""

from __future__ import annotations

import struct
from typing import Any

from .schemas import (
    AssetBindingStatus,
    CertificateStatus,
    EvidenceFinding,
    ManifestStatus,
    ProvenanceStatus,
    Reliability,
    Severity,
    SignatureStatus,
)

# Standard JUMBF and C2PA byte markers
JUMBF_TYPE_JUMB = b"jumb"
JUMBF_TYPE_C2PA = b"c2pa"
JUMBF_TYPE_C2AS = b"c2as"
C2PA_CLAIM_MARKER = b"c2pa.claim"
C2PA_SIGNATURE_MARKER = b"c2pa.signature"
C2PA_ASSERTIONS_MARKER = b"c2pa.assertions"
C2PA_HASH_DATA_MARKER = b"c2pa.hash.data"


def verify_provenance(raw_bytes: bytes) -> tuple[dict[str, Any], list[EvidenceFinding]]:
    """Inspect container bytes for C2PA / JUMBF Content Credentials.

    Separates:
    - Manifest parsing
    - Cryptographic signature validity
    - Certificate trust anchor verification
    - Claim-to-asset pixel data binding
    - Factual authenticity of depicted content

    Returns:
        tuple of (provenance_summary_dict, list_of_evidence_findings)
    """
    findings: list[EvidenceFinding] = []

    if not raw_bytes or len(raw_bytes) < 32:
        return {
            "status": ProvenanceStatus.NO_MANIFEST_PRESENT.value,
            "manifest_status": ManifestStatus.NO_MANIFEST_PRESENT.value,
            "signature_status": SignatureStatus.NO_SIGNATURE_PRESENT.value,
            "certificate_status": CertificateStatus.NO_CERTIFICATE_PRESENT.value,
            "asset_binding_status": AssetBindingStatus.ASSET_BINDING_UNVERIFIED.value,
            "has_c2pa": False,
            "has_signature": False,
            "signature_valid": False,
            "signer_info": None,
        }, [
            EvidenceFinding(
                source="PROVENANCE_C2PA",
                description="Byte payload is too short to contain a valid container or provenance manifest.",
                severity=Severity.INFORMATIONAL,
                reliability=Reliability.HEURISTIC,
                limitations=["Insufficient byte length for container analysis."],
            )
        ]

    # -------------------------------------------------------------------------
    # 1. JUMBF Box Header Parsing (ISO/IEC 19566-5)
    # -------------------------------------------------------------------------
    has_jumb = JUMBF_TYPE_JUMB in raw_bytes[:50000] or JUMBF_TYPE_JUMB in raw_bytes[-50000:]
    has_c2pa_box = JUMBF_TYPE_C2PA in raw_bytes[:50000] or JUMBF_TYPE_C2PA in raw_bytes[-50000:]
    has_manifest_markers = has_jumb or has_c2pa_box

    manifest_parsed = False
    jumbf_box_length: int | None = None

    if has_manifest_markers:
        # Attempt to parse box length (LBox) and box type (TBox)
        idx = raw_bytes.find(JUMBF_TYPE_JUMB)
        if idx == -1:
            idx = raw_bytes.find(JUMBF_TYPE_C2PA)

        if idx >= 4:
            try:
                lbox = struct.unpack(">I", raw_bytes[idx - 4 : idx])[0]
                if 8 <= lbox <= (len(raw_bytes) - idx + 4):
                    manifest_parsed = True
                    jumbf_box_length = lbox
            except Exception:
                pass

    if manifest_parsed:
        manifest_status = ManifestStatus.MANIFEST_PARSED
    elif has_manifest_markers:
        manifest_status = ManifestStatus.MANIFEST_MARKERS_DETECTED
    else:
        manifest_status = ManifestStatus.NO_MANIFEST_PRESENT

    # -------------------------------------------------------------------------
    # 2. Claim, Signature, and Assertion Marker Inspection
    # -------------------------------------------------------------------------
    has_claim = C2PA_CLAIM_MARKER in raw_bytes
    has_sig_marker = C2PA_SIGNATURE_MARKER in raw_bytes or JUMBF_TYPE_C2AS in raw_bytes
    has_assertions = C2PA_ASSERTIONS_MARKER in raw_bytes
    has_hash_data = C2PA_HASH_DATA_MARKER in raw_bytes

    # Extract Signer / Tool identity if declared in assertions
    signer_info: str | None = None
    lower_bytes = raw_bytes[:60000].lower() + raw_bytes[-60000:].lower()
    if b"adobe:firefly" in lower_bytes or b"adobe firefly" in lower_bytes:
        signer_info = "Adobe Firefly"
    elif b"dall-e" in lower_bytes or b"openai" in lower_bytes:
        signer_info = "OpenAI DALL-E"
    elif b"microsoft designer" in lower_bytes:
        signer_info = "Microsoft Designer"
    elif b"c2pa.org" in lower_bytes:
        signer_info = "C2PA Reference Implementation"

    # -------------------------------------------------------------------------
    # 3. Signature Validity & Envelope Integrity Verification
    # -------------------------------------------------------------------------
    signature_status: SignatureStatus
    certificate_status: CertificateStatus
    asset_binding_status: AssetBindingStatus

    if not has_sig_marker:
        signature_status = SignatureStatus.NO_SIGNATURE_PRESENT
        certificate_status = CertificateStatus.NO_CERTIFICATE_PRESENT
        asset_binding_status = AssetBindingStatus.ASSET_BINDING_UNVERIFIED
    else:
        sig_idx = raw_bytes.find(C2PA_SIGNATURE_MARKER)
        if sig_idx == -1:
            sig_idx = raw_bytes.find(JUMBF_TYPE_C2AS)

        # Integrity check: signature envelope must not be truncated
        sig_context = raw_bytes[sig_idx : sig_idx + 256]
        is_truncated = (
            len(sig_context) < 32
            or (sig_idx + len(sig_context) >= len(raw_bytes) and len(sig_context) < 64)
        )

        if is_truncated:
            signature_status = SignatureStatus.SIGNATURE_INVALID
            certificate_status = CertificateStatus.CERTIFICATE_UNTRUSTED
            asset_binding_status = AssetBindingStatus.ASSET_BINDING_INVALID
            findings.append(
                EvidenceFinding(
                    source="PROVENANCE_SIGNATURE",
                    description="C2PA signature envelope is truncated or structurally corrupted.",
                    severity=Severity.HIGH,
                    reliability=Reliability.UNVERIFIED,
                    limitations=["Corrupted signature block indicates incomplete transfer or deliberate container tampering."],
                )
            )
        else:
            # Important scientific rule: Marker presence does NOT prove mathematical cryptographic validity!
            # Full public-key verification requires a dedicated cryptographic engine (c2pa SDK).
            signature_status = SignatureStatus.SIGNATURE_UNVERIFIED
            certificate_status = CertificateStatus.CERTIFICATE_UNTRUSTED

            # Scientific security rule: Byte marker presence (e.g. c2pa.hash.data) must NEVER produce ASSET_BINDING_VALID!
            # Asset binding requires extracting the cryptographic digest from the claim assertion and comparing it
            # against the computed SHA-256 hash of the decoded raster pixels.
            # Without dedicated cryptographic verification, asset binding is strictly ASSET_BINDING_UNVERIFIED.
            asset_binding_status = AssetBindingStatus.ASSET_BINDING_UNVERIFIED

            findings.append(
                EvidenceFinding(
                    source="PROVENANCE_SIGNATURE",
                    description=(
                        f"C2PA signature envelope detected for assertion '{signer_info or 'Unknown Claim'}' "
                        f"(Status: SIGNATURE_UNVERIFIED — public key cryptographic validation not executed)."
                    ),
                    severity=Severity.LOW,
                    reliability=Reliability.HEURISTIC,
                    limitations=[
                        "Signature block is structurally present, but full asymmetric RSA/ECDSA mathematical verification "
                        "requires external C2PA cryptographic engine.",
                        "Certificate trust chain is untrusted pending root certificate trust store validation.",
                        "Asset binding is UNVERIFIED: Byte marker presence (e.g. c2pa.hash.data) does NOT verify that pixel payload matches manifest assertion. Cryptographic hash comparison against decoded pixels is required.",
                        "A cryptographically valid signature certifies the signing identity, NOT the factual authenticity of depicted content."
                    ],
                    metadata={
                        "signer_info": signer_info,
                        "has_assertions": has_assertions,
                        "has_hash_data": has_hash_data,
                        "asset_binding_verified": False,
                    },
                )
            )

    # -------------------------------------------------------------------------
    # 4. Manifest Status Reporting & Absence Safeguards
    # -------------------------------------------------------------------------
    if manifest_status == ManifestStatus.NO_MANIFEST_PRESENT:
        overall_status = ProvenanceStatus.NO_MANIFEST_PRESENT.value
        findings.append(
            EvidenceFinding(
                source="PROVENANCE_C2PA",
                description="No C2PA / JUMBF Content Credentials manifest detected in container.",
                severity=Severity.INFORMATIONAL,
                reliability=Reliability.HEURISTIC,
                limitations=[
                    "Missing C2PA manifest does NOT imply human or authentic origin.",
                    "Social media platforms, messaging applications, and web optimizers routinely strip C2PA manifests."
                ],
            )
        )
    elif signature_status == SignatureStatus.SIGNATURE_INVALID:
        overall_status = ProvenanceStatus.SIGNATURE_INVALID.value
    elif signature_status == SignatureStatus.SIGNATURE_UNVERIFIED:
        overall_status = ProvenanceStatus.SIGNATURE_UNVERIFIED.value
    else:
        overall_status = ProvenanceStatus.MANIFEST_MARKERS_DETECTED.value
        findings.append(
            EvidenceFinding(
                source="PROVENANCE_C2PA",
                description="C2PA manifest headers detected, but no cryptographic signature envelope is present.",
                severity=Severity.MEDIUM,
                reliability=Reliability.UNVERIFIED,
                limitations=["Unsigned manifests provide no cryptographic non-repudiation."],
            )
        )

    summary = {
        "status": overall_status,
        "manifest_status": manifest_status.value,
        "signature_status": signature_status.value,
        "certificate_status": certificate_status.value,
        "asset_binding_status": asset_binding_status.value,
        "has_c2pa": has_manifest_markers,
        "has_signature": has_sig_marker,
        "signature_valid": (signature_status == SignatureStatus.SIGNATURE_VALID),
        "asset_binding_valid": False,  # Never claimed without verified cryptographic hash comparison
        "signer_info": signer_info,
        "jumbf_box_length": jumbf_box_length,
        "has_assertions": has_assertions,
        "has_claim": has_claim,
        "has_hash_data": has_hash_data,
        "factual_authenticity": "INDEPENDENT_OF_CRYPTOGRAPHIC_PROVENANCE",
    }

    return summary, findings
