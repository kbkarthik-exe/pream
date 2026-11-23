# AICF Phase 2 — Stage 2.4: C2PA Asset-Binding Correction & Forensic Coverage Hardening Report

**Project Location:** `C:\Users\acer\IMAGE`  
**Report ID:** `REP-AICF-P2-STAGE-2.4`  
**Date:** November 19, 2026  
**Roles:** Senior Digital Forensics Engineer, Python Architect, Application Security Engineer, Independent Test Engineer  
**Status:** COMPLETE — REMEDIATIONS IMPLEMENTED, 61/61 TESTS PASSING (100%), ALL BASELINE FILES UNTOUCHED  
**Stop Condition:** Work paused here. Awaiting explicit user approval before Stage 3 integration.

---

## 1. Executive Summary

In accordance with the findings of the Stage 2.3 Independent Implementation Verification Audit, Stage 2.4 was conducted to remediate:
1. **Premature C2PA Asset-Binding Claims:** Eliminated the vulnerability where the presence of the byte marker `c2pa.hash.data` or any other manifest marker could produce `ASSET_BINDING_VALID`. Until genuine cryptographic asset-hash verification against decoded raster pixels is implemented, asset binding remains strictly `ASSET_BINDING_UNVERIFIED` (or `ASSET_BINDING_INVALID` if malformed/truncated).
2. **CMFD Analysis Coverage Hardening:** Remediated the unmonitored 4,000-block processing bypass in Copy-Move Forgery Detection (CMFD). Skipped processing is never interpreted as evidence of no manipulation or authenticity. The system now exposes an explicit `cmfd_status` (`COMPLETED`, `SKIPPED_EXCESSIVE_BLOCKS`, or `SKIPPED_INSUFFICIENT_DIMENSIONS`), logs the exact budget limit, and explicitly documents non-robustness to patch rotation and scaling.
3. **Confidence Semantics & Decoupling:** Replaced ambiguous confidence representations with distinct, orthogonal metrics: `heuristic_score`, `model_probability`, `calibrated_confidence`, and `evidence_strength`. The system explicitly flags that heuristic rule-tier scores are uncalibrated and must not be interpreted as Bayesian posterior probabilities.
4. **Reproducible Test Coverage:** Expanded the isolated test suite from 19 to 28 tests in `test_image_forensics_stage2.py`. All 61 regression tests across Stage 1, Stage 2, and Baseline pass in 33.28 seconds.
5. **Strict Baseline Preservation:** Verified that all 7 protected baseline files and Stage 1 deliverables are 100% bit-for-bit identical to their baseline backups.

---

## 2. Mandatory Pre-Flight Audit & Backup Summary

Prior to making source code modifications, a complete pre-flight audit was executed:
- **Working Directory Confirmed:** `C:\Users\acer\IMAGE`
- **Pre-Flight Hash Baseline:** Recorded full SHA-256 hashes for all protected and mutable files.
- **Timestamped Backup Created:** All files subject to remediation were backed up to:
  `backups/stage2_3_pre_stage2_4/`
  - `schemas.py`
  - `provenance_verifier.py`
  - `manipulation_detector.py`
  - `evidence_fusion.py`
  - `test_image_forensics_stage2.py`
- **Baseline Integrity Confirmed:** Verified that `backups/phase2_baseline_checkpoint/` was intact.

---

## 3. Detailed Technical Remediations

### 3.1 Task A — C2PA Asset-Binding Correction
**Problem:** In Stage 2.2, `provenance_verifier.py` assigned `AssetBindingStatus.ASSET_BINDING_VALID` whenever `b"c2pa.hash.data"` was found in the stream, without computing pixel hashes or comparing digests.

**Remediation:**
1. In `backend/app/ml/image/forensics/schemas.py`:
   - Enforced `AssetBindingStatus.ASSET_BINDING_UNVERIFIED` and alias `BINDING_UNVERIFIED`.
2. In `backend/app/ml/image/forensics/provenance_verifier.py`:
   - Byte marker presence (`c2pa.hash.data`, `c2pa.claim`, `c2pa.signature`) **NEVER** yields `ASSET_BINDING_VALID`.
   - Manifests with intact structure but without dedicated cryptographic hash calculation evaluate to:
     - `manifest_status = ManifestStatus.MANIFEST_PARSED`
     - `signature_status = SignatureStatus.SIGNATURE_UNVERIFIED`
     - `certificate_status = CertificateStatus.CERTIFICATE_UNTRUSTED`
     - `asset_binding_status = AssetBindingStatus.ASSET_BINDING_UNVERIFIED`
     - `asset_binding_valid = False`
   - Truncated or corrupt manifests evaluate to `ASSET_BINDING_INVALID`.
   - Added explicit limitation: *"Asset binding is UNVERIFIED: Byte marker presence does NOT verify that pixel payload matches manifest assertion. Cryptographic hash comparison against decoded pixels is required."*
   - Set `"factual_authenticity": "INDEPENDENT_OF_CRYPTOGRAPHIC_PROVENANCE"`.

### 3.2 Task B — CMFD Coverage Hardening & Processing Limits
**Problem:** Images resulting in $\ge 4,000$ spatial blocks were silently skipped by CMFD without notification, creating a risk that skipped analysis would be misinterpreted as an absence of manipulation. Furthermore, the algorithm was non-robust to rotation.

**Remediation:**
1. In `backend/app/ml/image/forensics/manipulation_detector.py`:
   - Introduced `cmfd_status`:
     - `"COMPLETED"`: Analysis ran normally.
     - `"SKIPPED_EXCESSIVE_BLOCKS"`: Block count exceeded 4,000 blocks budget.
     - `"SKIPPED_INSUFFICIENT_DIMENSIONS"`: Subsampled dimensions $< 4 \times 4$ blocks.
   - When the limit is reached, an explicit `INFORMATIONAL` finding is recorded:
     *"Copy-Move Forgery Detection (CMFD) skipped: Image spatial grid (H x W blocks) exceeds maximum real-time processing limit of 4,000 blocks."*
   - Explicitly added disclaimer: *"Skipped CMFD processing does NOT constitute evidence of no manipulation or authenticity."*
   - Documented rotation sensitivity: `"cmfd_rotation_invariant": False`. Block matching is strictly axis-aligned and does not detect patches rotated $> 5^\circ$ or scaled $> 10\%$.
   - Retained pixel-level Mean Absolute Error filter ($\text{MAE} < 3.0$) and contiguous spatial clustering ($\ge 2$ neighbor links) to suppress false positives on periodic natural textures (brick, foliage, fabric).

### 3.3 Task C — Confidence Semantics & Decoupling
**Problem:** Heuristic rules assigned confidence numbers ($0.75, 0.70, 0.65, 0.55$) that could be misinterpreted as calibrated statistical probabilities.

**Remediation:**
1. In `backend/app/ml/image/forensics/schemas.py`:
   - Added enums `ConfidenceType` (`HEURISTIC_SCORE`, `MODEL_PROBABILITY`, `CALIBRATED_CONFIDENCE`) and `EvidenceStrength` (`NONE`, `WEAK`, `MODERATE`, `STRONG`, `CONCLUSIVE`).
   - Extended `ForensicReport` with:
     - `confidence_type: str = "HEURISTIC_SCORE"`
     - `is_calibrated: bool = False`
     - `evidence_strength: str`
     - `heuristic_score: float`
     - `model_probability: float | None = None`
     - `calibrated_confidence: float | None = None`
     - `calibration_limitation: str`
2. In `backend/app/ml/image/forensics/evidence_fusion.py`:
   - Decoupled Dimension A ($P(\text{AI})$) and Dimension B (Manipulation Analysis).
   - Added global disclaimer: *"Confidence values in Dimension B represent uncalibrated heuristic rule-tier scores and must NOT be interpreted as calibrated posterior Bayesian probabilities."*
   - Mapped evidence tiers to strength: Copy-move / Inpainting $\to$ `STRONG`, Noise Splicing $\to$ `MODERATE`, Retouching $\to$ `WEAK`, Clean baseline $\to$ `NONE`.

---

## 4. Test Verification & Coverage Expansion

The test suite in `backend/tests/test_image_forensics_stage2.py` was expanded from 19 to 28 tests:
- `test_20_fake_hash_marker_cannot_produce_valid_binding`: Verifies fake `c2pa.hash.data` marker yields `ASSET_BINDING_UNVERIFIED` and `asset_binding_valid: False`.
- `test_21_manifest_with_hash_marker_remains_unverified`: Verifies parsed manifest with hash markers remains unverified without cryptographic comparison.
- `test_22_malformed_or_truncated_manifest_binding_invalid`: Verifies truncated manifest yields `ASSET_BINDING_INVALID`.
- `test_23_cmfd_above_block_limit_reports_skipped_status`: Verifies image above 4,000 blocks reports `SKIPPED_EXCESSIVE_BLOCKS` and documents non-manipulation disclaimer.
- `test_24_cmfd_rotation_sensitivity_documented_not_claimed`: Verifies `rotation_invariant: False` metadata.
- `test_25_heuristic_confidence_distinguished_from_calibrated_probability`: Verifies `confidence_type == "HEURISTIC_SCORE"`, `is_calibrated == False`, and calibration limitation disclaimer.
- `test_26_missing_manifest_binding_unverified`: Verifies missing manifest yields `NO_MANIFEST_PRESENT` and `ASSET_BINDING_UNVERIFIED`.
- `test_27_invalid_binding_data_not_valid`: Verifies corrupt container with invalid length yields non-valid binding.
- `test_28_rotated_cloned_patch_cmfd_limitation`: Verifies axis-aligned CMFD does not detect 90-degree rotated cloned patch and documents limitation.

### Comprehensive Test Suite Results:
```powershell
backend\venv\Scripts\python.exe -m pytest backend/tests/test_generator_attribution.py backend/tests/test_image_forensics_stage2.py backend/tests/test_image_analysis.py -v
```

| Suite | File | Tests | Passed | Failed | Skipped | Time |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Stage 1 Attribution** | `test_generator_attribution.py` | 12 | 12 | 0 | 0 | 1.9s |
| **Stage 2 Forensics** | `test_image_forensics_stage2.py` | 28 | 28 | 0 | 0 | 2.4s |
| **Baseline Regression** | `test_image_analysis.py` | 21 | 21 | 0 | 0 | 29.0s |
| **TOTAL** | **All 3 Suites** | **61** | **61** | **0** | **0** | **33.28s** |

*Warnings:* 5 Starlette deprecation warnings (`HTTP_422_UNPROCESSABLE_ENTITY` in FastAPI internal routing). Zero errors. 100% reproducible.

---

## 5. Cryptographic Baseline Hash Verification

Full SHA-256 integrity audit comparing live files against `backups/phase2_baseline_checkpoint/`:

| File | Baseline Backup SHA-256 | Current Live SHA-256 | Status |
| :--- | :--- | :--- | :--- |
| `backend/app/ml/image/detector.py` | `54bf8ae13ac208ea1ae53a281ff3e21721eb26faa6e155c8c32f2aa236285716` | `54bf8ae13ac208ea1ae53a281ff3e21721eb26faa6e155c8c32f2aa236285716` | **MATCH (100% Untouched)** |
| `backend/app/ml/image/ensemble.py` | `3726bd3084ffa97c246a219df047c49c2a28484175fe7d6529955c2f6007468e` | `3726bd3084ffa97c246a219df047c49c2a28484175fe7d6529955c2f6007468e` | **MATCH (100% Untouched)** |
| `backend/app/ml/image/features.py` | `d8baf3331eaef5108e6cc2c3c0b8fec08cdd27128f23b3e858bf30c76e2c5475` | `d8baf3331eaef5108e6cc2c3c0b8fec08cdd27128f23b3e858bf30c76e2c5475` | **MATCH (100% Untouched)** |
| `backend/app/ml/image/heatmap.py` | `b8772f642f210a7ea494a7826cac3fc311622923ba4d4d4650b3c4387001fd20` | `b8772f642f210a7ea494a7826cac3fc311622923ba4d4d4650b3c4387001fd20` | **MATCH (100% Untouched)** |
| `backend/app/ml/image/hive_adapter.py` | `04b3f480d376f7b2862883b67a02ad00085256ae362423fb8aabcb33593ee1f9` | `04b3f480d376f7b2862883b67a02ad00085256ae362423fb8aabcb33593ee1f9` | **MATCH (100% Untouched)** |
| `backend/app/ml/image/__init__.py` | `583df30bc0aa53bf29238e724ddfe9aa9d015c14eaa54ae6e38df1ed8ea13545` | `583df30bc0aa53bf29238e724ddfe9aa9d015c14eaa54ae6e38df1ed8ea13545` | **MATCH (100% Untouched)** |
| `backend/app/api/v1/endpoints/image.py` | `1d096a00b1354db221aee765e5a5782add85a3c90abe84992cfab741687e504d` | `1d096a00b1354db221aee765e5a5782add85a3c90abe84992cfab741687e504d` | **MATCH (100% Untouched)** |
| `backend/tests/test_image_analysis.py` | `e0d095b0bf0d06a7ffadc5e44b1a08336abb2cd926fd76f6c3db7371e437707d` | `e0d095b0bf0d06a7ffadc5e44b1a08336abb2cd926fd76f6c3db7371e437707d` | **MATCH (100% Untouched)** |
| `generator_attribution.py` (Stage 1) | `c04701d978436cf6f7ef28bd7c805315eed2056f5ba43d7f4b313d09e8859033` | `c04701d978436cf6f7ef28bd7c805315eed2056f5ba43d7f4b313d09e8859033` | **MATCH (Stage 1 Untouched)** |

---

## 6. Files Changed vs Files Preserved

### Files Modified in Stage 2.4:
1. `backend/app/ml/image/forensics/schemas.py`: Added `ConfidenceType`, `EvidenceStrength`, `AssetBindingStatus.BINDING_UNVERIFIED`, extended `ForensicReport`.
2. `backend/app/ml/image/forensics/provenance_verifier.py`: Corrected asset binding to `ASSET_BINDING_UNVERIFIED` and `asset_binding_valid: False`.
3. `backend/app/ml/image/forensics/manipulation_detector.py`: Added `cmfd_status`, block budget reporting (4,000 blocks), rotation sensitivity metadata.
4. `backend/app/ml/image/forensics/evidence_fusion.py`: Decoupled confidence semantics, added uncalibrated heuristic score disclaimers.
5. `backend/app/ml/image/forensics/__init__.py`: Exported new schemas (`ConfidenceType`, `EvidenceStrength`).
6. `backend/tests/test_image_forensics_stage2.py`: Expanded test coverage with tests 20 to 28.

### Files Strictly Preserved:
- Production image API endpoint (`backend/app/api/v1/endpoints/image.py`) — **UNTOUCHED**.
- Vision ML models & ensemble (`detector.py`, `ensemble.py`, `features.py`, `heatmap.py`) — **UNTOUCHED**.
- Baseline tests (`test_image_analysis.py`) — **UNTOUCHED**.
- Frontend web applications (`frontend/`) — **UNTOUCHED**.
- PDF generation service (`pdf_generator.py`) — **UNTOUCHED**.
- Authentication, database schemas, text forensics, video forensics — **UNTOUCHED**.

---

## 7. Remaining Known Limitations

1. **No External Cryptographic Engine Installed:**
   `c2pa-python` and `cryptography` are not installed. C2PA verification remains structural and heuristic. True RSA/ECDSA signature verification and CA trust chain validation are offline.
2. **CMFD Rotation Non-Invariance:**
   Block-matching operates on axis-aligned raster grids. Cloned regions rotated $> 5^\circ$ or scaled $> 10\%$ evade detection. Keypoint-based matching (e.g. SIFT/ORB) would be required for full affine invariance.
3. **High-Resolution CMFD Skipping:**
   Images with $> 4,000$ blocks (after $2\times$ subsampling, $\approx 1024 \times 1024$ pixels) have CMFD analysis skipped to ensure real-time bounded response times.
4. **Uncalibrated Confidence Values:**
   Heuristic rule-tier scores ($0.75, 0.70, 0.65, 0.55$) indicate relative evidence weight, not calibrated Bayesian probabilities.
5. **No Production API Integration:**
   As mandated by preservation rules, the forensic package resides in `backend/app/ml/image/forensics/` and is NOT yet wired into `backend/app/api/v1/endpoints/image.py`.

---

## 8. Recommendations Before Stage 3 Integration

1. In Stage 3, integrate `security_hardening.py` pre-decode dimension sniffing at the top of the HTTP route `backend/app/api/v1/endpoints/image.py` before calling `Image.open()`.
2. Connect `evidence_fusion.py` to the primary API response schema, maintaining strict separation between Dimension A ($P(\text{AI})$) and Dimension B (Manipulation Analysis).
3. Update frontend visualization dashboards to render `heuristic_score` and `evidence_strength` with explicit disclaimers rather than presenting them as calibrated probabilities.

---

## 9. Final Stop Condition

Stage 2.4 remediation is **COMPLETE**.

In strict accordance with instructions:
- **Production API endpoints were NOT modified.**
- **Stage 3 integration has NOT been started.**
- **Packages were NOT installed.**
- **Awaiting user review and explicit approval before Stage 3.**
