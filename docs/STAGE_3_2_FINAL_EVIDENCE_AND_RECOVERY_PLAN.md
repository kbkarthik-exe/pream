# AICF — STAGE 3.2 FINAL EVIDENCE CONSOLIDATION & RECOVERY PLAN

**Project:** `C:\Users\acer\IMAGE`  
**Date:** 2026-11-22  
**Role:** Senior Python Backend Engineer, ML Systems Engineer & Security Auditor  
**Status:** **BLOCKED** (Pending Stage 3.2B Full Inference Verification)

---

## 1. Executive Summary & Verification Bifurcation

Stage 3.2 verification has been bifurcated into two distinct, rigorous evidentiary categories based on host hardware availability and process isolation:

1. **Stage 3.2A — Resource-Safe Verification:** **PASS (86 / 86 tests passed, 0 failed, 100% pass rate)**.
   - Covers the complete new `UnifiedImagePipeline` orchestrator suite (17/17).
   - Covers all Stage 1 attribution tests (12/12).
   - Covers all Stage 2.4 image forensics and C2PA provenance tests (28/28).
   - Covers all Stage 3.1 ingestion security gate tests (20/20).
   - Covers all non-heavy API baseline validation and rejection tests (9/9).
   - Covers 100% bit-for-bit cryptographic integrity across all 8 protected baseline files.
2. **Stage 3.2B — Full Neural Inference Verification:** **BLOCKED (12 / 12 un-mocked inference tests pending)**.
   - 12 legacy integration tests in `backend/tests/test_image_analysis.py` invoke real, un-mocked Swin-B + ViT neural network forward passes.
   - Under critical host memory pressure (7.75 GB total RAM, only 0.65 GB available, 91% memory load), PyTorch and native OpenBLAS fail with:
     ```text
     OpenBLAS error: Memory allocation still failed after 10 retries, giving up.
     ```
3. **Core Governance Principle:** **Neither category alone proves full Stage 3.2 regression completion.**
   - Stage 3.2A proves complete architectural correctness, mathematical decoupling, interface compliance, failure isolation, and baseline immutability.
   - Stage 3.2B is required to prove end-to-end integration with the un-mocked vision backbone in the live runtime.
   - Therefore, the official status of Stage 3.2 remains **BLOCKED** until Stage 3.2B can be safely executed under sufficient host resources.

---

## 2. Evidence Reconciliation Across Stage 3.2 Reports

The three authoritative audit reports in `docs/` have been audited and reconciled. All three documents agree on the following facts:

| Verification Metric | Document Agreement | Recorded Evidence |
|---|---|---|
| **Orchestrator Unit Tests** | `STAGE_3_2_RESOURCE_AWARE_VERIFICATION.md`<br>`STAGE_3_2_VERIFICATION_FAILURE_INVESTIGATION.md`<br>`STAGE_3_2_IMPLEMENTATION_REPORT.md` | **17 / 17 Passed** (0 failures, 1.19s execution) |
| **Resource-Safe Regression Tests** | `STAGE_3_2_RESOURCE_AWARE_VERIFICATION.md`<br>`STAGE_3_2_VERIFICATION_FAILURE_INVESTIGATION.md` | **86 / 86 Passed** (0 failures, 100% pass rate) |
| **Blocked Inference Tests** | `STAGE_3_2_RESOURCE_AWARE_VERIFICATION.md`<br>`STAGE_3_2_VERIFICATION_FAILURE_INVESTIGATION.md` | **12 Tests Blocked** in `test_image_analysis.py` |
| **Protected Baseline Hashes** | All three audit reports | **8 / 8 Match** (100% bit-for-bit against checkpoint) |
| **Implementation Invariants** | All three audit reports | **All 10 Safety Invariants Verified** in `unified_pipeline.py` |

---

## 3. Detailed Results: Stage 3.2A Resource-Safe Verification

All 86 resource-safe tests were executed sequentially using `backend\venv\Scripts\python.exe` with zero concurrent processes:

### 3.1 Test Execution Table

| Suite # | Target Test Suite | Test File | Passed | Failed | Warnings | Duration | Exit Code |
|---|---|---|---|---|---|---|---|
| **1** | Stage 3.2 Unified Orchestrator | `backend/tests/test_unified_pipeline.py` | **17** | 0 | 0 | 1.19s | **0** |
| **2** | Stage 1 Generator Attribution | `backend/tests/test_generator_attribution.py` | **12** | 0 | 0 | 0.40s | **0** |
| **3** | Stage 2.4 Forensics & C2PA | `backend/tests/test_image_forensics_stage2.py` | **28** | 0 | 0 | 2.88s | **0** |
| **4** | Stage 3.1 Ingestion Security Gate | `backend/tests/test_stage3_1_security_gate.py` | **20** | 0 | 12 | 5.82s | **0** |
| **5** | Baseline Safe Non-Inference Subset | `backend/tests/test_image_analysis.py` (subset) | **9** | 0 | 5 | 3.35s | **0** |
| **Total** | **All Resource-Safe Suites** | — | **86** | **0** | **17** | **13.64s** | **0** |

### 3.2 Verified Baseline Safe Subset Tests (`test_image_analysis.py`)
1. `test_image_analysis_unauthenticated`: Authentication guard verification (**PASSED**)
2. `test_image_analysis_empty_upload`: Rejection of 0-byte uploads (**PASSED**)
3. `test_image_analysis_corrupted_file`: Rejection of malformed byte headers (**PASSED**)
4. `test_image_analysis_unsupported_format`: Rejection of non-image MIME types (**PASSED**)
5. `test_image_analysis_oversized_file`: Rejection of files exceeding byte ceiling (**PASSED**)
6. `test_image_analysis_excessive_dimensions`: Pre-decode rejection of pixel bombs (**PASSED**)
7. `test_image_analysis_model_unavailable`: Graceful fallback when model unconfigured (**PASSED**)
8. `test_image_analysis_inference_exception`: Safe exception boundary preventing stack trace leaks (**PASSED**)
9. `test_image_analysis_hive_cloud_adapter_unconfigured`: Clean degradation without API key (**PASSED**)

---

## 4. Stage 3.2B: Blocked Inference Tests & Technical Constraints

The following 12 integration tests in `backend/tests/test_image_analysis.py` require un-mocked neural network execution:

| # | Blocked Test Name | Operational Path | Reason for Blocked Status |
|---|---|---|---|
| 1 | `test_image_analysis_valid_jpeg` | Swin-B + ViT Forward Pass | OpenBLAS memory allocation failure |
| 2 | `test_image_analysis_valid_png` | Swin-B + ViT Forward Pass | Heavy vision backbone inference |
| 3 | `test_image_analysis_valid_webp` | Swin-B + ViT Forward Pass | Heavy vision backbone inference |
| 4 | `test_image_analysis_low_resolution_inconclusive` | Resolution check & Inference | Heavy vision backbone inference |
| 5 | `test_image_analysis_user_isolation` | Database & Full Inference | Heavy vision backbone inference |
| 6 | `test_image_analysis_history_and_case_save` | Case DB & Full Inference | Heavy vision backbone inference |
| 7 | `test_image_analysis_no_temp_file_leak` | Temp Tracker & Full Inference | Heavy vision backbone inference |
| 8 | `test_image_analysis_ensemble_calibration` | Multi-model calibration | Dual model weight allocation |
| 9 | `test_image_analysis_secondary_vit_execution` | Secondary ViT model | Secondary neural network forward pass |
| 10 | `test_image_analysis_ela_explainability_heatmap` | Grad-CAM & ELA map generation | Heavy tensor backprop/activation |
| 11 | `test_image_analysis_multi_detector_api_response` | Consensus aggregation | Full multi-detector forward pass |
| 12 | `test_image_analysis_pdf_with_ensemble` | PDF generation after inference | Full inference + ReportLab rendering |

### Technical Constraints Documented:
- **Host Physical RAM:** 7.75 GB Total / **0.65 GB Available (91% Utilization)**.
- **Root Failure Mode:** `OpenBLAS error: Memory allocation still failed after 10 retries, giving up.`
- **Process Impact:** Hard process exit (exit code 1) from C++ native library without Python traceback.
- **Rule Compliance:** In strict accordance with instructions, `test_image_analysis.py` has not been modified, monkeypatched, or deleted.

---

## 5. Protected Baseline Integrity Audit (8 Core Files)

All 8 protected core baseline files were recalculated using SHA-256 and compared bit-for-bit against the original Stage 3.1 checkpoint:

| Protected File Path | Original Baseline SHA-256 | Current Working Copy SHA-256 | Status |
|---|---|---|---|
| `backend/app/ml/image/detector.py` | `54bf8ae13ac208ea1ae53a281ff3e21721eb26faa6e155c8c32f2aa236285716` | `54bf8ae13ac208ea1ae53a281ff3e21721eb26faa6e155c8c32f2aa236285716` | **MATCH** |
| `backend/app/ml/image/ensemble.py` | `3726bd3084ffa97c246a219df047c49c2a28484175fe7d6529955c2f6007468e` | `3726bd3084ffa97c246a219df047c49c2a28484175fe7d6529955c2f6007468e` | **MATCH** |
| `backend/app/ml/image/features.py` | `d8baf3331eaef5108e6cc2c3c0b8fec08cdd27128f23b3e858bf30c76e2c5475` | `d8baf3331eaef5108e6cc2c3c0b8fec08cdd27128f23b3e858bf30c76e2c5475` | **MATCH** |
| `backend/app/ml/image/heatmap.py` | `b8772f642f210a7ea494a7826cac3fc311622923ba4d4d4650b3c4387001fd20` | `b8772f642f210a7ea494a7826cac3fc311622923ba4d4d4650b3c4387001fd20` | **MATCH** |
| `backend/app/ml/image/hive_adapter.py` | `04b3f480d376f7b2862883b67a02ad00085256ae362423fb8aabcb33593ee1f9` | `04b3f480d376f7b2862883b67a02ad00085256ae362423fb8aabcb33593ee1f9` | **MATCH** |
| `backend/app/ml/image/__init__.py` | `583df30bc0aa53bf29238e724ddfe9aa9d015c14eaa54ae6e38df1ed8ea13545` | `583df30bc0aa53bf29238e724ddfe9aa9d015c14eaa54ae6e38df1ed8ea13545` | **MATCH** |
| `backend/tests/test_image_analysis.py` | `e0d095b0bf0d06a7ffadc5e44b1a08336abb2cd926fd76f6c3db7371e437707d` | `e0d095b0bf0d06a7ffadc5e44b1a08336abb2cd926fd76f6c3db7371e437707d` | **MATCH** |
| `backend/app/ml/image/generator_attribution.py` | `c04701d978436cf6f7ef28bd7c805315eed2056f5ba43d7f4b313d09e8859033` | `c04701d978436cf6f7ef28bd7c805315eed2056f5ba43d7f4b313d09e8859033` | **MATCH** |

**Baseline Integrity Verdict:** **8 / 8 MATCH (100% BIT-FOR-BIT PRESERVED)**

---

## 6. Stage 3.2B Resource Recovery Plan & Execution Checklist

Before attempting to execute the 12 blocked inference tests in Stage 3.2B, the following procedural checklist must be completed:

### Pre-Execution Checklist
- [ ] **1. Close Unnecessary Applications:** Terminate resource-heavy applications (browsers, background Electron apps, IDE visualizers) to free physical RAM.
- [ ] **2. System Reboot (If Pressure Persists):** If available physical RAM remains below 2.5 GB after closing applications, reboot the Windows host to clear leaked kernel memory buffers and fragmented paging files.
- [ ] **3. Pre-Flight Memory Verification:** Execute `GlobalMemoryStatusEx` check to verify that:
  - `Available Physical RAM >= 2.5 GB`
  - `System Memory Load <= 65%`
- [ ] **4. Process Isolation Check:** Verify via `tasklist` or PowerShell that no duplicate or zombie `python.exe` or `pytest.exe` processes exist in background sessions.
- [ ] **5. Sequential Execution Architecture:** Run tests sequentially, never with `-n` (pytest-xdist) or parallel workers.
- [ ] **6. Internal OpenBLAS Thread Throttling:** Ensure the Python runner configures `OPENBLAS_NUM_THREADS=1` and `OMP_NUM_THREADS=1` via Python `os.environ` prior to importing `torch` or `cv2`, avoiding shell-interpolation pitfalls.
- [ ] **7. Exact Telemetry Logging:** Capture standard output, standard error, exit codes, test durations, and memory consumption before and after execution.

---

## 7. Explicit Limitations & Boundaries

1. **Stage 3.2 Scope Boundary:** Stage 3.2 is an architectural orchestration stage (`unified_pipeline.py`). It does not modify the production endpoint router (`backend/app/api/v1/endpoints/image.py`), which remains planned for Stage 3.4.
2. **Model Weight Immutability:** No model weights, checkpoints, or inference architectures were altered or downgraded to circumvent memory constraints.
3. **Pillow Single-Decode Boundary:** As verified in Stage 3.2, global single-decode is impossible without modifying the protected `detector.py` file. The orchestrator achieves single-decode sharing between attribution and forensics, eliminating 2 out of 3 redundant decodes while leaving `detector.py` completely untouched.
4. **No Premature Promotion:** Stage 3.3 (UI / Evaluation / Endpoint Integration) must not commence until Stage 3.2B is formally resolved.

---

## 8. Final Status

**Classification:** **BLOCKED**

*Rationale:* While Stage 3.2A is 100% successful with 86 passing tests and flawless baseline integrity, Stage 3.2 as a whole remains **BLOCKED** pending the execution of Stage 3.2B (the 12 blocked inference tests) under suitable host hardware conditions.

**Implementation Action:** All implementation work is STOPPED. Stage 3.3 has NOT been started.
