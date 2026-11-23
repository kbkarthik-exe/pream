# AICF Phase 2 — Stage 2.3 Independent Implementation Verification Audit

**Project:** `C:\Users\acer\IMAGE`  
**Audit Report ID:** `AUD-AICF-P2-STAGE-2.3`  
**Date:** November 19, 2026  
**Auditor Roles:** Independent Senior Software Auditor, Digital Forensics Engineer, Application Security Reviewer  
**Audit Scope:** Verification of Stage 2.2 remediations, source code inspection, test reproducibility, security boundaries, baseline preservation, and documentation accuracy.

---

## 1. Executive Summary & Audit Verdict

### Overall Verdict: **PASS WITH LIMITATIONS**

The Stage 2.2 implementation was subjected to an independent, adversarial code and runtime audit. The isolated forensic modules (`provenance_verifier.py`, `security_hardening.py`, `manipulation_detector.py`, `metadata_forensics.py`, `frequency_analyzer.py`, `evidence_fusion.py`) and their schemas successfully remediate the primary failure modes flagged in the Stage 2.1 audit. 

All 52 automated regression tests pass cleanly in 29.94 seconds without regression. All 7 protected baseline files and the Stage 1 generator attribution deliverable are **100% untouched**, matching their pre-Stage 1/Stage 2 baseline hashes bit-for-bit.

However, several critical architectural limitations, unverified claims, and integration gaps exist that must be formally documented before proceeding to Stage 3.

```
+---------------------------------------------------------------------------------------------------------+
|                                    STAGE 2.3 AUDIT SCORECARD                                            |
+--------------------------+-----------------------+------------------------------------------------------+
| Subsystem                | Verdict               | Key Audit Finding                                    |
+--------------------------+-----------------------+------------------------------------------------------+
| 1. C2PA Verification     | PASS WITH LIMITATIONS | Marker cannot produce SIGNATURE_VALID (Confirmed).   |
|                          |                       | Asset binding is marker-based, not cryptographically  |
|                          |                       | hashed. No official C2PA SDK installed in venv.       |
| 2. Image Security        | PASS WITH LIMITATIONS | Pre-decode sniffing is verified in isolated tests    |
|                          |                       | but NOT YET INTEGRATED into production API endpoint. |
| 3. Manipulation Analysis | PASS WITH LIMITATIONS | Bokeh and texture false positives eliminated;        |
|                          |                       | CMFD bypassed for >4000 blocks; rotation-sensitive.  |
| 4. Evidence Fusion       | PASS                  | Strict decoupling of P(AI) and Manipulation score.   |
|                          |                       | Confidences are heuristic constants, not Bayesian.   |
| 5. Reproducible Testing  | PASS                  | 52/52 tests pass (100% reproducible across 3 suites).|
| 6. Baseline Preservation | PASS                  | Exact SHA-256 matches on all baseline files.         |
|                          |                       | Git failure root cause confirmed: Git not on PATH.   |
+--------------------------+-----------------------+------------------------------------------------------+
```

---

## 2. Audit 1 — C2PA Provenance Verification Subsystem

### 2.1 Verification of Status Separation & Enums
Inspection of [schemas.py](file:///C:/Users/acer/IMAGE/backend/app/ml/image/forensics/schemas.py) and [provenance_verifier.py](file:///C:/Users/acer/IMAGE/backend/app/ml/image/forensics/provenance_verifier.py) confirms that the monolithic status has been decomposed into independent dimensions:
- `ManifestStatus`: `NO_MANIFEST_PRESENT`, `MANIFEST_MARKERS_DETECTED`, `MANIFEST_PARSED`.
- `SignatureStatus`: `NO_SIGNATURE_PRESENT`, `SIGNATURE_UNVERIFIED`, `SIGNATURE_VALID`, `SIGNATURE_INVALID`.
- `CertificateStatus`: `NO_CERTIFICATE_PRESENT`, `CERTIFICATE_UNTRUSTED`, `CERTIFICATE_TRUSTED`.
- `AssetBindingStatus`: `ASSET_BINDING_UNVERIFIED`, `ASSET_BINDING_VALID`, `ASSET_BINDING_INVALID`.

### 2.2 Verified Capabilities
1. **No False Cryptographic Claims:** When C2PA markers (`c2pa.signature`, `c2pa`, `jumb`) are detected, `signature_status` is explicitly set to `SIGNATURE_UNVERIFIED` and `certificate_status` is set to `CERTIFICATE_UNTRUSTED`.
2. **Signature Verification Distinguished from Certificate Trust:** The code explicitly tracks whether an asymmetric signature is mathematically valid versus whether the signing certificate chains to a recognized root Certificate Authority (CA).
3. **Safe Truncation Handling:** In `provenance_verifier.py` (lines 81–88, 133–140), big-endian box length extraction (`struct.unpack(">I")`) validates stream boundaries. If `lbox < 8` or `sig_context < 32` bytes, the manifest is flagged as `SIGNATURE_INVALID` and `MANIFEST_CORRUPT`.
4. **Factual Authenticity Clarification:** The report explicitly sets `"factual_authenticity": "INDEPENDENT_OF_CRYPTOGRAPHIC_PROVENANCE"`, recognizing that a valid cryptographic signature attests to the signing entity's identity, NOT the physical ground truth of the scene.

### 2.3 Unverified Claims & Security Limitations
- **CRITICAL DEFECT — Marker-Based Asset Binding:** In `provenance_verifier.py` (lines 158–161):
  ```python
  asset_binding_status = (
      AssetBindingStatus.ASSET_BINDING_VALID if has_hash_data
      else AssetBindingStatus.ASSET_BINDING_UNVERIFIED
  )
  ```
  The code assigns `ASSET_BINDING_VALID` based **solely** on the string marker `b"c2pa.hash.data"` being present in `raw_bytes`. The system does **NOT** extract the claimed hash, compute the SHA-256 digest over the decoded pixel stream, or verify that the image pixels match the manifest assertion. This is an unverified claim and a forensic vulnerability.
- **No Official C2PA SDK Installed:** Inspection of `backend/venv` (`pip list`) confirms that neither `c2pa-python`, `cryptography`, nor `pyopenssl` is installed. Pure-Python standard library cannot execute cryptographic CMS/COSE envelope signature verification.
- **Absence of Real-World Signed Fixtures:** Repository search confirms that no genuine signed C2PA test files (e.g. from Adobe Content Authenticity Initiative, Leica, or Truepic) exist in the project. All unit tests use synthetic byte sequences.

---

## 3. Audit 2 — Image Ingestion Security Hardening

### 3.1 Verification of Security Helper (`security_hardening.py`)
Inspection of [security_hardening.py](file:///C:/Users/acer/IMAGE/backend/app/ml/image/forensics/security_hardening.py) confirms robust binary-level parsing:
- **PNG Sniffer:** Parses `\x89PNG\r\n\x1a\n` and unpacks `IHDR` width and height from bytes 16–24 without decompressing scanlines.
- **JPEG Sniffer:** Walks markers ($0xFF, \text{marker}$) to locate `SOF0`/`SOF2` frames and extracts dimensions.
- **WebP Sniffer:** Reads `VP8 ` (lossy) and `VP8L` (lossless) bitstream headers.
- **Decompression Bomb Defense:** Enforces a maximum pixel limit of $16,777,216$ pixels ($16.7\text{ MP}$), an absolute single-axis limit of $8,192\text{ px}$, and checks expansion ratio $\frac{\text{Estimated Uncompressed Bytes}}{\text{Compressed Bytes}}$.
- **Pillow Safety:** Sets `Image.MAX_IMAGE_PIXELS = 16_777_216`.

### 3.2 Production Integration Audit: The Reality Gap
**FINDING: Security checks are NOT currently invoked in the live production upload path!**

Inspection of [backend/app/api/v1/endpoints/image.py](file:///C:/Users/acer/IMAGE/backend/app/api/v1/endpoints/image.py) (lines 101–125) reveals:
```python
# Production endpoint analyze_image()
with Image.open(io.BytesIO(file_bytes)) as pil_img:
    img_format = (pil_img.format or "").upper()
    width, height = pil_img.size
    ...
```
1. `security_hardening.py` is **NOT imported** in `image.py`.
2. `sniff_image_dimensions_pre_decode()` and `validate_image_security()` are **NOT called** before `Image.open()`.
3. The production route relies on its baseline check: invoking `Image.open()` first and checking `settings.IMAGE_MAX_PIXELS`.
4. While `validate_image_security()` is invoked inside `evidence_fusion.py` (lines 66–82), the entire `forensics` package is isolated and not yet connected to the HTTP router.

> [!WARNING]
> **Production Status:** The system cannot claim production protection against decompression bombs or header exploits until `security_hardening.py` is integrated into `backend/app/api/v1/endpoints/image.py` during Stage 3.

---

## 4. Audit 3 — Manipulation Detection Subsystem

### 4.1 Bokeh Portrait Handling
- **Mechanism:** In [manipulation_detector.py](file:///C:/Users/acer/IMAGE/backend/app/ml/image/forensics/manipulation_detector.py) (lines 152–163), the engine computes the mean step difference along the middle horizontal and vertical quadrant axes (`mean_seam_step`). If $\text{mean seam step} \le 3.5$, noise variance gradients are classified as natural optical depth-of-field (`INFORMATIONAL`) rather than `SUSPECTED_SPLICING`.
- **Limitation / False-Negative Risk:** The seam step is evaluated **only** along the quadrant center lines (`mid_y`, `mid_x`). If a spliced object is placed entirely inside a single quadrant, or if the splice was created using feathered or Poisson alpha-blending ($\text{step} \le 3.5$), this check will suppress the splicing alert.

### 4.2 Repetitive Textures & Copy-Move Forgery Detection (CMFD)
- **Mechanism:** CMFD extracts $8 \times 8$ blocks, filters flat areas ($b_{\text{std}} > 8.0$), sorts lexicographically on $(\mu, \sigma)$, and computes pixel-level Mean Absolute Error:
  $$\text{MAE}(b_1, b_2) < 3.0$$
  Candidate pairs must also form a cluster of $\ge 3$ blocks with $\ge 2$ contiguous neighbor links.
- **Empirical Test:**
  - Cloned patches: $\text{MAE} = 0.0$ $\to$ Detected.
  - Brick wall simulation: $\text{MAE} = 18.3$ $\to$ Rejected (no false alarm).
- **Limitations:**
  1. **Block Grid Cap:** Line 216 contains `if ... and (blocks_h * blocks_w) < 4000:`. For images larger than $\approx 1280 \times 1280$, CMFD is completely skipped.
  2. **Rigid Transformations:** Block matching operates on fixed $8 \times 8$ blocks. Any rotation ($> 5^\circ$), scaling ($> 10\%$), or off-grid shift combined with lossy compression will evade detection.
  3. **Heuristic Thresholds:** Thresholds ($\text{MAE} < 3.0$, $\text{seam step} \le 3.5$, $\text{ratio} > 3.2$) were tuned on synthetic tests, not calibrated on standardized forensic benchmarks (e.g., CASIA, CoMoFoD).

---

## 5. Audit 4 — Evidence Fusion Subsystem

### 5.1 Verification of Dimension Independence
Inspection of [evidence_fusion.py](file:///C:/Users/acer/IMAGE/backend/app/ml/image/forensics/evidence_fusion.py) confirms:
- **Decoupled Architecture:** `run_forensic_investigation()` computes **only** `manipulation_verdict` (Dimension B). It does not compute or modify the synthetic media probability $P(\text{AI})$ (Dimension A).
- **Correlated Signal Fusion:** ELA anomalies require localized spatial clustering or generative metadata to escalate from `SUSPECTED_RETOUCHING` to `SUSPECTED_INPAINTING`.
- **Absence of Negative Inferences:** Missing metadata or absence of manipulation seams explicitly yields disclaimers rather than an inference of authenticity.
- **Inconclusive Handling:** Malformed or sub-threshold images correctly return `INSUFFICIENT_EVIDENCE`.

### 5.2 Fusion Limitations
- **Confidence Calibration:** The confidence values assigned ($0.75, 0.70, 0.65, 0.55$) are hardcoded heuristics, not calibrated posterior probabilities.
- **Verdict Granularity:** In `schemas.py`, `ManipulationVerdict` lacks a dedicated `SUSPECTED_COPY_MOVE` state, mapping cloning instead to `SUSPECTED_SPLICING`.

---

## 6. Audit 5 — Reproducible Testing Verification

The entire regression suite was independently executed in `backend/venv`:
```powershell
backend\venv\Scripts\python.exe -m pytest backend/tests/test_generator_attribution.py backend/tests/test_image_forensics_stage2.py backend/tests/test_image_analysis.py -v
```

### Execution Output:
- **Test Discovery:** 52 items collected across 3 test files.
- **Stage 1 Generator Attribution Tests:** 12 passed.
- **Stage 2 Image Forensics Tests:** 19 passed (including tests 15–19 covering fake C2PA markers, decompression bombs, oversized single axis, brick textures, and bokeh portraits).
- **Baseline Image Analysis Tests:** 21 passed.
- **Warnings:** 5 deprecation warnings in `fastapi/routing.py` (`HTTP_422_UNPROCESSABLE_ENTITY` deprecated in Starlette).
- **Total Execution Time:** 29.94 seconds.
- **Reproducibility Verdict:** **100% REPRODUCIBLE (52 Passed, 0 Failed, 0 Skipped).**

---

## 7. Audit 6 — Baseline Preservation and Git Status Investigation

### 7.1 SHA-256 Hash Verification Against Baseline Backup
Every baseline file in `backups/phase2_baseline_checkpoint/` was compared with the live repository:

| File | Live SHA-256 | Backup SHA-256 | Match |
| :--- | :--- | :--- | :--- |
| `backend/app/ml/image/detector.py` | `54bf8ae13ac208ea1ae53a281ff3e21721eb26faa6e155c8c32f2aa236285716` | `54bf8ae13ac208ea1ae53a281ff3e21721eb26faa6e155c8c32f2aa236285716` | **YES** |
| `backend/app/ml/image/ensemble.py` | `3726bd3084ffa97c246a219df047c49c2a28484175fe7d6529955c2f6007468e` | `3726bd3084ffa97c246a219df047c49c2a28484175fe7d6529955c2f6007468e` | **YES** |
| `backend/app/ml/image/features.py` | `d8baf3331eaef5108e6cc2c3c0b8fec08cdd27128f23b3e858bf30c76e2c5475` | `d8baf3331eaef5108e6cc2c3c0b8fec08cdd27128f23b3e858bf30c76e2c5475` | **YES** |
| `backend/app/ml/image/heatmap.py` | `b8772f642f210a7ea494a7826cac3fc311622923ba4d4d4650b3c4387001fd20` | `b8772f642f210a7ea494a7826cac3fc311622923ba4d4d4650b3c4387001fd20` | **YES** |
| `backend/app/ml/image/hive_adapter.py` | `04b3f480d376f7b2862883b67a02ad00085256ae362423fb8aabcb33593ee1f9` | `04b3f480d376f7b2862883b67a02ad00085256ae362423fb8aabcb33593ee1f9` | **YES** |
| `backend/app/ml/image/__init__.py` | `583df30bc0aa53bf29238e724ddfe9aa9d015c14eaa54ae6e38df1ed8ea13545` | `583df30bc0aa53bf29238e724ddfe9aa9d015c14eaa54ae6e38df1ed8ea13545` | **YES** |
| `backend/app/api/v1/endpoints/image.py` | `1d096a00b1354db221aee765e5a5782add85a3c90abe84992cfab741687e504d` | `1d096a00b1354db221aee765e5a5782add85a3c90abe84992cfab741687e504d` | **YES** |
| `backend/tests/test_image_analysis.py` | `e0d095b0bf0d06a7ffadc5e44b1a08336abb2cd926fd76f6c3db7371e437707d` | `e0d095b0bf0d06a7ffadc5e44b1a08336abb2cd926fd76f6c3db7371e437707d` | **YES** |
| `generator_attribution.py` (Stage 1) | `c04701d978436cf6f7ef28bd7c805315eed2056f5ba43d7f4b313d09e8859033` | `c04701d978436cf6f7ef28bd7c805315eed2056f5ba43d7f4b313d09e8859033` | **YES** |

### 7.2 Git Exit Code 1 Investigation
Investigation into why `git status` exited with code 1 reveals:
1. `where.exe git` returned `"INFO: Could not find files for the given pattern(s)"`.
2. Python `shutil.which('git')` returned `None`.
3. The system `PATH` contains an entry pointing to `C:\Users\acer\AppData\Local\GitHubDesktop\app-3.5.8\resources\app\git\cmd`.
4. Inspection of `C:\Users\acer\AppData\Local\GitHubDesktop` found a `.dead` marker and only two residual files (`squirrel.exe`, `v8_context_snapshot.bin`); the git subfolder does not exist.
5. **Conclusion:** Git is not installed or available on this host environment. PowerShell correctly raised `CommandNotFoundException`. The file backup directory and SHA-256 verification serve as the authoritative baseline mechanism.

---

## 8. Exact Recommendations Before Stage 3 Integration

Before proceeding to Stage 3 (Pipeline Assembly & Production Route Integration), the following remediation steps must be incorporated:

1. **Fix Asset Binding Verification:** Update `provenance_verifier.py` to change `AssetBindingStatus.ASSET_BINDING_VALID` to `ASSET_BINDING_UNVERIFIED` unless the image pixel SHA-256 digest is extracted from the manifest and compared against the raw image data.
2. **Integrate Security Sniffer into Production Upload Route:** In Stage 3, import and invoke `validate_image_security(file_bytes)` at the top of `analyze_image` in `backend/app/api/v1/endpoints/image.py` *before* calling `Image.open()`.
3. **Add Dedicated Copy-Move Verdict:** Add `SUSPECTED_COPY_MOVE = "SUSPECTED_COPY_MOVE"` to `ManipulationVerdict` in `schemas.py` to differentiate cloning from inter-image splicing.
4. **Acquire Genuine C2PA Test Vectors:** Obtain standard signed test fixtures from the C2PA specification repository to validate real-world parsing once `c2pa-python` installation is approved.
5. **Calibrate Confidence Scales:** Label confidence scores as `heuristic_score` rather than calibrated probabilities in API responses and frontend dashboards.

---

## 9. Final Stop Condition

Audit 2.3 is complete. In strict adherence to audit rules:
- **No production routes or baseline files were modified.**
- **Stage 3 implementation has NOT been started.**
- **Awaiting user review and explicit approval before any further actions.**

