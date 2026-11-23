# AICF Phase 2 – C2PA Provenance Verification Status & Technical Architecture

**Document ID:** `DOC-AICF-P2-C2PA-001`  
**Date:** November 19, 2026  
**Status:** Completed & Hardened (Stage 2.2)  
**Security Classification:** Forensic Engineering Technical Specification  
**Environment:** Python 3.12.10 (AMD64 / Windows 11), Virtual Environment (`backend/venv`)

---

## 1. Executive Summary

In response to the Stage 2.1 independent forensic audit, the C2PA provenance verification subsystem has been completely re-architected. The previous implementation suffered from an unacceptable security flaw: detecting raw byte sequences (`c2pa`, `jumb`, `urn:c2pa`) or JUMBF superbox signatures erroneously reported the provenance state as `CRYPTOGRAPHICALLY_VERIFIED`.

In Stage 2.2, this vulnerability has been eliminated. The system now strictly separates **marker detection**, **manifest container parsing**, **cryptographic signature validation**, **certificate authority chain trust**, **claim-to-asset binding**, and **factual authenticity**.

Under the current environment constraint—where no unauthorized external packages (`c2pa-python`, `cryptography`, `pyopenssl`) may be installed without explicit approval—the system operates safely and transparently in **deterministic inspection mode**. It verifies container structure, detects tampering or truncation, and reports honest, cryptographically accurate statuses (`MANIFEST_PARSED`, `SIGNATURE_UNVERIFIED`, `CERTIFICATE_UNTRUSTED`) while never falsely claiming cryptographic authenticity.

---

## 2. Theoretical Background: The C2PA Verification Model

The Coalition for Content Provenance and Authenticity (C2PA) standard establishes cryptographic provenance for digital media. A complete, valid C2PA verification requires establishing five independent security guarantees:

```
+-----------------------------------------------------------------------------+
|                            C2PA TRUST HIERARCHY                             |
+-----------------------------------------------------------------------------+
|  1. Manifest Existence     : JUMBF superbox present in asset metadata?       |
|  2. Structural Integrity   : JUMBF box lengths and headers uncorrupted?     |
|  3. Signature Validity     : Cryptographic digest matches signed attributes? |
|  4. Certificate Trust      : End-entity certificate chains to trusted root?  |
|  5. Asset Binding          : Byte-hash (hard) or perceptual hash (soft)     |
|                              matches the visual payload of the image?       |
+-----------------------------------------------------------------------------+
|                  ALL 5 MUST HOLD TO ESTABLISH PROVENANCE                    |
+-----------------------------------------------------------------------------+
```

### 2.1 Distinction Between Signed and Trusted Provenance
- **Signed Provenance:** An entity generated a digital signature over the claim dictionary using an asymmetric private key. The mathematical signature is intact.
- **Trusted Provenance:** The signing key is bound to an X.509 certificate issued by a recognized, audited Certificate Authority (CA) on a trusted list (such as the Adobe Trust List or C2PA Recognized Trust Root Store).
- **Critical Risk:** Anyone can generate an RSA-2048 or ECDSA P-256 self-signed key pair and sign an arbitrary manifest claiming an image was captured by "The New York Times" or "Canon EOS R5". Without certificate path validation to an authentic CA, a signed manifest is not trustworthy.

### 2.2 Distinction Between Valid Provenance and Factual Authenticity
- Provenance records *who asserted what*, not *whether what was asserted is physical truth*.
- An authentic, signed, trusted C2PA manifest from an AI generator (e.g., OpenAI DALL-E 3 or Google Imagen) explicitly asserts that the image is synthetic (`c2pa.created: "c2pa.synthetic"`).
- Conversely, a malicious actor can take a photo of an AI-generated image displayed on a physical monitor using a hardware camera equipped with C2PA hardware attestation. The camera will sign the captured frame with valid hardware keys, even though the visual subject is synthetic.
- Therefore, AICF treats C2PA as **direct provenance metadata**, never as absolute, infallible real-world ground truth.

---

## 3. Python 3.12 & Platform Compatibility Assessment

### 3.1 Environment Inspection
During Stage 2.2 pre-flight engineering, the `backend/venv` runtime environment was inspected:
- **Operating System:** Windows 11 (64-bit x86_64)
- **Python Version:** 3.12.10
- **Standard Library Capabilities:** `ssl` (OpenSSL 3.0.16 22 Oct 2024), `hashlib`, `struct`, `io`
- **Installed Cryptographic Packages:** None (`c2pa` not installed, `cryptography` not installed, `asn1crypto` not installed)

### 3.2 Upstream C2PA Library Status
| Package | Version Tested / Target | Python 3.12 Windows x86_64 Compatibility | Notes / Blockers |
| :--- | :--- | :--- | :--- |
| `c2pa-python` | `0.7.0`+ | Supported (Pre-built wheels available for Windows x86_64, Python 3.10-3.12) | Official Rust C2PA library with C-FFI / Python bindings. Requires wheel download. |
| `cryptography` | `43.0.0`+ | Fully Supported (Pre-built binary wheels) | Provides X.509 certificate parsing, RSA/ECDSA/Ed25519 signature verification, and PKCS#7 / CMS envelope parsing. |
| Standard Library `ssl` | 3.0.16 | Built-in | Exposes SSL/TLS transport and `SSLContext`, but **does NOT** expose generic CMS/COSE or JUMBF signature verification APIs. |

### 3.3 Strict Package Policy Compliance
Under the Phase 2 strict preservation constraints, **no pip packages were installed**. 
AICF Stage 2.2 implements a pure-Python, zero-dependency JUMBF parser and structural validator that operates safely within standard Python 3.12.

---

## 4. Architectural Remediations Implemented

### 4.1 Granular Status Enumerations
The monolithic, error-prone `ProvenanceStatus` enum was refactored into distinct, orthogonally verifiable state machines in `backend/app/ml/image/forensics/schemas.py`:

```python
class ManifestStatus(str, Enum):
    NO_MANIFEST_PRESENT = "NO_MANIFEST_PRESENT"
    MARKERS_DETECTED = "MARKERS_DETECTED"
    MANIFEST_PARSED = "MANIFEST_PARSED"
    MANIFEST_CORRUPT = "MANIFEST_CORRUPT"

class SignatureStatus(str, Enum):
    NO_SIGNATURE = "NO_SIGNATURE"
    SIGNATURE_UNVERIFIED = "SIGNATURE_UNVERIFIED"
    SIGNATURE_VALID = "SIGNATURE_VALID"
    SIGNATURE_INVALID = "SIGNATURE_INVALID"
    SIGNATURE_TRUNCATED = "SIGNATURE_TRUNCATED"

class CertificateStatus(str, Enum):
    NO_CERTIFICATE = "NO_CERTIFICATE"
    CERTIFICATE_UNTRUSTED = "CERTIFICATE_UNTRUSTED"
    CERTIFICATE_EXPIRED = "CERTIFICATE_EXPIRED"
    CERTIFICATE_REVOKED = "CERTIFICATE_REVOKED"
    CERTIFICATE_TRUSTED = "CERTIFICATE_TRUSTED"

class AssetBindingStatus(str, Enum):
    NOT_EVALUATED = "NOT_EVALUATED"
    HARD_BINDING_VALID = "HARD_BINDING_VALID"
    HARD_BINDING_MISMATCH = "HARD_BINDING_MISMATCH"
    SOFT_BINDING_PROBABLE = "SOFT_BINDING_PROBABLE"
    BINDING_UNVERIFIED = "BINDING_UNVERIFIED"
```

### 4.2 Deterministic JUMBF Parsing & Box Integrity
In `backend/app/ml/image/forensics/provenance_verifier.py`, the engine now parses binary JUMBF (JPEG Universal Metadata Box Format, ISO/IEC 19566-5) structures:
1. **Magic Signature & Length Parsing:** When marker `jumb` is detected, the 32-bit big-endian length header is extracted:
   $$\text{box\_length} = \mathbf{struct.unpack}(">I", \text{data}[idx-4:idx])[0]$$
2. **Bounds & Truncation Checking:** If $\text{box\_length} < 8$ or $\text{stream\_length} < idx - 4 + \text{box\_length}$, the manifest is immediately flagged as `SIGNATURE_TRUNCATED` and `MANIFEST_CORRUPT`.
3. **Envelope Consistency:** Scans for signature envelopes (`c2pa.signature`, `urn:c2pa`). If markers are found without valid JUMBF packaging or with truncated byte runs, the engine classifies the payload as `MANIFEST_CORRUPT` and produces a `CRITICAL` severity finding.
4. **No Premature Cryptographic Claims:** Even if the JUMBF superbox is structurally intact, the status is set to:
   - `manifest_status = ManifestStatus.MANIFEST_PARSED`
   - `signature_status = SignatureStatus.SIGNATURE_UNVERIFIED`
   - `certificate_status = CertificateStatus.CERTIFICATE_UNTRUSTED`
   - `asset_binding_status = AssetBindingStatus.BINDING_UNVERIFIED`
   - `factual_authenticity = "UNVERIFIED: Cryptographic signature engine offline. Manifest present but untrusted."`

---

## 5. Threat Modeling & Failure Modes

| Attack Vector / Scenario | Pre-Remediation Behavior | Post-Remediation Behavior (Stage 2.2) |
| :--- | :--- | :--- |
| **Marker Injection:** Attacker injects ASCII bytes `"c2pa"` or `"jumb"` into PNG `tEXt` or JPEG comment. | Reported `CRYPTOGRAPHICALLY_VERIFIED`. | Reports `MANIFEST_CORRUPT` / `SIGNATURE_INVALID`. Generates `CRITICAL` alert: *"Suspected forged or malformed provenance envelope"*. |
| **Truncated Manifest:** Attacker truncates JUMBF box to strip assertions or certificates. | Reported `CRYPTOGRAPHICALLY_VERIFIED`. | Reports `SIGNATURE_TRUNCATED` and `MANIFEST_CORRUPT`. Length header validation prevents out-of-bounds reads. |
| **Self-Signed Certificate:** Attacker signs manifest with untrusted local key. | Reported `CRYPTOGRAPHICALLY_VERIFIED`. | Reports `CERTIFICATE_UNTRUSTED`. Explicitly warns that root certificate is not anchored in a verified Trust Store. |
| **Valid AI Manifest (e.g. DALL-E 3):** Clean AI-generated image with valid signature. | Undifferentiated "Verified". | Correctly surfaces AI assertion (`digitalSourceType: trainedAlgorithmicMedia`), setting `is_synthetic = True` while noting untrusted CA status. |

---

## 6. Verification and Test Results

All C2PA scenarios are covered by automated unit tests in `backend/tests/test_image_forensics_stage2.py`:
- `test_11_unverified_c2pa_manifest`: Validates that structurally sound manifests with signatures are marked `SIGNATURE_UNVERIFIED` and `CERTIFICATE_UNTRUSTED`.
- `test_12_invalid_or_truncated_signatures`: Validates that truncated byte streams trigger `SIGNATURE_TRUNCATED` and `MANIFEST_CORRUPT`.
- `test_15_fake_c2pa_signature_never_produces_valid`: Confirms that byte marker injection never produces `CRYPTOGRAPHICALLY_VERIFIED`.

---

## 7. Stage 3 Integration Readiness

When user approval is granted to install `c2pa-python`:
1. The isolated `provenance_verifier.py` module is designed with drop-in hooks for `c2pa.Reader`.
2. When `c2pa-python` is present, `verify_provenance_markers()` will seamlessly delegate to `c2pa.Reader.from_stream()`, populating `SIGNATURE_VALID` and validating against the system Trust Store.
3. If `c2pa-python` is absent, the pure-Python fallback continues to protect against malicious injections and false claims without breaking downstream callers.

