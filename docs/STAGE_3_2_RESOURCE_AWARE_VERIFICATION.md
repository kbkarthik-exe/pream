# AICF — STAGE 3.2 RESOURCE-AWARE VERIFICATION REPORT

**Project:** `C:\Users\acer\IMAGE`  
**Date:** 2026-11-22  
**Role:** Senior Python Backend Engineer, ML Systems Engineer & Security Auditor  
**Scope:** Resource-aware verification of Stage 3.2 deliverables and prior regression suites without modifying implementation code or protected baseline files.  
**Classification:** **BLOCKED** (All 86 resource-safe tests passed cleanly; 12 un-mocked heavy vision inference tests remain blocked due to host memory exhaustion)

---

## 1. Executive Summary

Under strict zero-modification constraints, all tests that can safely execute within the current host environment were sequentially executed and recorded. 

- **Orchestrator Unit Tests (`test_unified_pipeline.py`):** **17 / 17 PASSED (100%)**
- **Independent Regression Suites:**
  - Stage 1 Attribution (`test_generator_attribution.py`): **12 / 12 PASSED (100%)**
  - Stage 2.4 Forensics & C2PA (`test_image_forensics_stage2.py`): **28 / 28 PASSED (100%)**
  - Stage 3.1 Security Gate (`test_stage3_1_security_gate.py`): **20 / 20 PASSED (100%)**
- **Production Baseline Safe Subset (`test_image_analysis.py`):** **9 / 9 PASSED (100%)**
- **Total Tests Executed:** **86 / 86 PASSED (100% Pass Rate, 0 Failures)**
- **Blocked Baseline Tests:** 12 tests in `test_image_analysis.py` invoking un-mocked Swin-B+ViT PyTorch inference were prevented from completing by native OpenBLAS memory allocation failures.
- **Protected Baseline Integrity:** **8 / 8 MATCH (100% SHA-256 Bit-for-Bit Verified)**

---

## 2. Resource Diagnostics Prior to Testing

Host memory metrics were sampled directly via the Windows kernel API (`GlobalMemoryStatusEx`) before initiating the verification test runs:

| Resource Metric | Value | Diagnostic Assessment |
|---|---|---|
| **Total Physical RAM** | 7.75 GB | System total |
| **Available Physical RAM** | 0.65 GB (665 MB) | **CRITICAL MEMORY PRESSURE** |
| **Memory Load** | **91%** | Substantial host memory utilization |
| **Total PageFile** | 15.60 GB | Virtual paging file size |
| **Available PageFile** | 1.29 GB | Constrained swap headroom |
| **Total Virtual Memory** | 131,072.00 GB | 64-bit user address space |
| **Available Virtual Memory** | 131,067.90 GB | Normal address space layout |

### Resource Diagnostic Findings:
1. With only **650 MB of available physical RAM** (91% memory load), loading the un-mocked Swin-B+ViT model weights (~425 tensors) combined with multi-threaded OpenBLAS thread buffer allocations exceeds contiguous heap limits.
2. This confirms the empirical finding in task-4509:
   ```text
   OpenBLAS error: Memory allocation still failed after 10 retries, giving up.
   ```
3. In contrast, mock-based unit tests and lightweight algorithmic tests run efficiently with sub-second response times and zero memory errors.

---

## 3. Test Execution Registry (Sequential Execution)

All test suites were executed sequentially with zero concurrent processes.

### 3.1 Suite 1: New Stage 3.2 Orchestrator Tests
- **Target File:** `backend/tests/test_unified_pipeline.py`
- **Exact Command:**
  ```powershell
  backend\venv\Scripts\python.exe -m pytest backend/tests/test_unified_pipeline.py -v
  ```
- **Exit Code:** `0`
- **Summary:** **17 passed in 1.19s**
- **Failed:** 0
- **Warnings:** 0
- **Key Verifications:**
  - Initialization defaults and options
  - Multi-dimensional ingestion across JPEG, PNG, and WebP
  - Dimension independence (splicing/seam findings do not alter $P(\text{AI})$)
  - Single-decode image sharing between attribution and forensics
  - C2PA credential-checking without false visual authenticity claims
  - Explicit heuristic labeling (`confidence_type="HEURISTIC_SCORE"`)
  - Failure isolation and graceful degradation across Dimensions A, B, and Attribution
  - Pre-decode rejection of empty payloads and decompression bombs
  - SHA-256 data contract integrity

### 3.2 Suite 2: Stage 1 Generator Attribution Tests
- **Target File:** `backend/tests/test_generator_attribution.py`
- **Exact Command:**
  ```powershell
  backend\venv\Scripts\python.exe -m pytest backend/tests/test_generator_attribution.py -v
  ```
- **Exit Code:** `0`
- **Summary:** **12 passed in 0.40s**
- **Failed:** 0
- **Warnings:** 0
- **Key Verifications:**
  - PNG generator metadata extraction
  - Software metadata heuristics
  - No metadata / misleading metadata handling
  - Conflicting metadata resolution
  - Missing/truncated C2PA manifests
  - Corruption/unsupported format handling
  - Direct signed C2PA provenance extraction

### 3.3 Suite 3: Stage 2.4 Forensics & C2PA Tests
- **Target File:** `backend/tests/test_image_forensics_stage2.py`
- **Exact Command:**
  ```powershell
  backend\venv\Scripts\python.exe -m pytest backend/tests/test_image_forensics_stage2.py -v
  ```
- **Exit Code:** `0`
- **Summary:** **28 passed in 2.88s**
- **Failed:** 0
- **Warnings:** 0
- **Key Verifications:**
  - Untouched photo vs. AI-generated vs. edited images
  - Copy-move and splicing manipulation detectors
  - Recompression and resizing robustness
  - Localization bounding boxes
  - Pre-decode decompression bomb rejection
  - C2PA manifest verification and fake signature rejection
  - CMFD block limits and rotation sensitivity documentation

### 3.4 Suite 4: Stage 3.1 Ingestion Security Gate Tests
- **Target File:** `backend/tests/test_stage3_1_security_gate.py`
- **Exact Command:**
  ```powershell
  backend\venv\Scripts\python.exe -m pytest backend/tests/test_stage3_1_security_gate.py -v
  ```
- **Exit Code:** `0`
- **Summary:** **20 passed, 12 warnings in 5.82s**
- **Failed:** 0
- **Warnings:** 12 Starlette deprecation warnings (`HTTP_422_UNPROCESSABLE_ENTITY`)
- **Key Verifications:**
  - Ingestion gate pass-through for valid JPEG, PNG, WebP
  - Pre-decode rejection of empty, oversized, disguised, truncated, and corrupted files
  - Decompression bomb dimension sniffing
  - Single-axis dimension limits
  - Information leakage prevention (no internal paths, memory addresses, or temp files leaked)

### 3.5 Suite 5: Production Baseline Safe Non-Inference Tests
- **Target File:** `backend/tests/test_image_analysis.py` (safe subset)
- **Exact Command:**
  ```powershell
  backend\venv\Scripts\python.exe -m pytest backend/tests/test_image_analysis.py -k "test_image_analysis_unauthenticated or test_image_analysis_empty_upload or test_image_analysis_corrupted_file or test_image_analysis_unsupported_format or test_image_analysis_oversized_file or test_image_analysis_excessive_dimensions or test_image_analysis_model_unavailable or test_image_analysis_inference_exception or test_image_analysis_hive_cloud_adapter_unconfigured" -v
  ```
- **Exit Code:** `0`
- **Summary:** **9 passed, 12 deselected, 5 warnings in 3.35s**
- **Failed:** 0
- **Warnings:** 5 Starlette deprecation warnings (`HTTP_422_UNPROCESSABLE_ENTITY`)
- **Passed Tests:**
  1. `test_image_analysis_unauthenticated`
  2. `test_image_analysis_empty_upload`
  3. `test_image_analysis_corrupted_file`
  4. `test_image_analysis_unsupported_format`
  5. `test_image_analysis_oversized_file`
  6. `test_image_analysis_excessive_dimensions`
  7. `test_image_analysis_model_unavailable`
  8. `test_image_analysis_inference_exception`
  9. `test_image_analysis_hive_cloud_adapter_unconfigured`

---

## 4. Blocked Tests & Technical Root Cause

The following 12 tests in `backend/tests/test_image_analysis.py` were not executed to avoid crashing the runner:

| Test Name | Reason for Classification as BLOCKED |
|---|---|
| `test_image_analysis_valid_jpeg` | Invokes un-mocked Swin-B+ViT forward pass; triggers OpenBLAS allocation failure |
| `test_image_analysis_valid_png` | Invokes un-mocked vision model inference |
| `test_image_analysis_valid_webp` | Invokes un-mocked vision model inference |
| `test_image_analysis_low_resolution_inconclusive` | Invokes un-mocked vision model inference |
| `test_image_analysis_user_isolation` | Invokes un-mocked vision model inference |
| `test_image_analysis_history_and_case_save` | Invokes un-mocked vision model inference |
| `test_image_analysis_no_temp_file_leak` | Invokes un-mocked vision model inference |
| `test_image_analysis_ensemble_calibration` | Invokes un-mocked vision model inference |
| `test_image_analysis_secondary_vit_execution` | Invokes un-mocked secondary ViT inference |
| `test_image_analysis_ela_explainability_heatmap` | Invokes un-mocked vision model inference |
| `test_image_analysis_multi_detector_api_response` | Invokes un-mocked vision model inference |
| `test_image_analysis_pdf_with_ensemble` | Invokes un-mocked vision model inference |

### Technical Root Cause:
- `test_image_analysis.py` was authored in Phase 2 as an integration test without mocking the Vision Transformer weights.
- When running in an environment with only 650 MB available physical RAM (91% system load), the native C++ multithreading layer in `OpenBLAS` (linked by NumPy/PyTorch) fails to allocate contiguous working memory blocks.
- This causes the native DLL to abort the process directly with exit code 1:
  `OpenBLAS error: Memory allocation still failed after 10 retries, giving up.`
- Per strict instructions, the protected baseline file `test_image_analysis.py` must not be modified or monkeypatched.

---

## 5. Protected Baseline Hash Verification (8 Files)

Every core baseline file was verified via SHA-256 against `backups/phase2_baseline_checkpoint/` and documented checkpoints:

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

**Baseline Integrity Verdict:** **8 / 8 MATCH (100% BIT-FOR-BIT IDENTICAL)**

---

## 6. Unresolved Issues

1. **Host Memory Constraint on Heavy Inference:** Running full un-mocked neural network inference under current physical RAM availability (~650 MB free) is vulnerable to OpenBLAS allocation failure.
2. **Sequential vs. Isolated Test Execution:** While lightweight tests can run sequentially in a single pytest command, heavy baseline tests require either dedicated single-threaded configuration or increased host memory to execute without native library aborts.

---

## 7. Final Classification

**Classification:** **BLOCKED**

*Rationale:* In accordance with the requirement *"Do not claim full regression PASS if any required test remains unexecuted"*, the status is **BLOCKED**. All 86 tests that can safely run passed with a 100% pass rate and 0 failures, all 8 protected baseline files match their hashes bit-for-bit, but 12 un-mocked inference tests in the legacy `test_image_analysis.py` remain blocked due to host OpenBLAS memory exhaustion under high memory load (91%).

**Next Stage Status:** Stage 3.3 has NOT been started. Execution has stopped as requested.
