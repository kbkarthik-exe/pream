# AICF Phase 3 — Stage 3.0: Unified Image Pipeline Integration Architecture Audit & Plan

**Project Location:** `C:\Users\acer\IMAGE`  
**Document ID:** `PLAN-AICF-P3-STAGE-3.0`  
**Date:** November 19, 2026  
**Roles:** Senior Python Architect, ML Systems Engineer, API Architect, Security Engineer, Integration Auditor  
**Status:** COMPLETE ARCHITECTURE AUDIT & PLANNING SPECIFICATION  
**Scope:** Stage 3.0 is **Audit and Planning Only**. No source code, database models, tests, or API endpoints are modified.

---

## 1. Executive Summary

AICF (AI Content Forensics & Authenticity Intelligence Platform) Phase 2 delivered:
1. **Stage 1:** An independent image generator attribution engine (`generator_attribution.py`) supporting direct provenance, metadata heuristics, and statistical markers.
2. **Stage 2 & 2.2 / 2.4:** An isolated, hardened multi-dimensional image forensics package (`backend/app/ml/image/forensics/`) comprising metadata forensics, structural C2PA provenance verification, 2D FFT spectral anisotropy, ELA compression analysis, Laplacian noise variance profiling, copy-move forgery detection (CMFD with pixel-level MAE filtering and 4,000-block budgeting), spatial localization of tampering, pre-decode image security hardening, and evidence fusion.

Currently, these capabilities exist as standalone, tested libraries with 61/61 passing regression tests. However, **they are not yet wired into the production FastAPI application** (`backend/app/api/v1/endpoints/image.py`), the primary database schema (`ImageAnalysisRecord`), the PDF export generator (`pdf_generator.py`), or the Next.js frontend dashboard (`frontend/src/app/dashboard/image/page.tsx`).

This document provides a comprehensive architectural blueprint for safely integrating Stage 1 and Stage 2 capabilities into a **Unified Multi-Dimensional Image Forensics Pipeline** without regressing existing baseline capabilities, compromising two-dimensional decoupling, or degrading user latency.

---

## 2. Project State & Baseline Verification Record

### 2.1 Runtime Environment
- **Operating System:** Windows 11 (10.0.26200 AMD64)
- **Python Version:** 3.12.10 (64-bit WindowsPE, tags/v3.12.10:0cc8128)
- **Virtual Environment:** `C:\Users\acer\IMAGE\backend\venv`
- **Pytest Suite:** 61 tests passing (12 Stage 1, 28 Stage 2.4, 21 Baseline Production) in 33.28s.
- **Git Availability:** Absent on host system (`CommandNotFoundException`). Authoritative baseline tracking is enforced via SHA-256 verification against `backups/phase2_baseline_checkpoint/`.

### 2.2 Authoritative Cryptographic Baseline Hashes
Every file subject to future integration was hashed before commencing Stage 3.0 planning:

| File Path | SHA-256 Checksum | Baseline Status |
| :--- | :--- | :--- |
| `backend/app/ml/image/detector.py` | `54bf8ae13ac208ea1ae53a281ff3e21721eb26faa6e155c8c32f2aa236285716` | **100% Match (Untouched)** |
| `backend/app/ml/image/ensemble.py` | `3726bd3084ffa97c246a219df047c49c2a28484175fe7d6529955c2f6007468e` | **100% Match (Untouched)** |
| `backend/app/ml/image/features.py` | `d8baf3331eaef5108e6cc2c3c0b8fec08cdd27128f23b3e858bf30c76e2c5475` | **100% Match (Untouched)** |
| `backend/app/ml/image/heatmap.py` | `b8772f642f210a7ea494a7826cac3fc311622923ba4d4d4650b3c4387001fd20` | **100% Match (Untouched)** |
| `backend/app/ml/image/hive_adapter.py` | `04b3f480d376f7b2862883b67a02ad00085256ae362423fb8aabcb33593ee1f9` | **100% Match (Untouched)** |
| `backend/app/ml/image/__init__.py` | `583df30bc0aa53bf29238e724ddfe9aa9d015c14eaa54ae6e38df1ed8ea13545` | **100% Match (Untouched)** |
| `backend/app/api/v1/endpoints/image.py` | `1d096a00b1354db221aee765e5a5782add85a3c90abe84992cfab741687e504d` | **100% Match (Untouched)** |
| `backend/tests/test_image_analysis.py` | `e0d095b0bf0d06a7ffadc5e44b1a08336abb2cd926fd76f6c3db7371e437707d` | **100% Match (Untouched)** |
| `backend/app/schemas/image_analysis.py` | `ad3179b5277297fa04a1d70a5d8760ee4753ffe2f1c06382f389db358954ea6b` | Live Baseline Recorded |
| `backend/app/models/image_analysis.py` | `0e460b889e6c1b8239408cbf9856fde54bdf62336a7d1b3962942e13fa84bc51` | Live Baseline Recorded |
| `backend/app/services/pdf_generator.py` | `30182950a8dac436c69518a73a797ee460853bb90823456b9cf507af2c2e4175` | Live Baseline Recorded |
| `generator_attribution.py` (Stage 1) | `c04701d978436cf6f7ef28bd7c805315eed2056f5ba43d7f4b313d09e8859033` | Stage 1 Final Recorded |
| `forensics/schemas.py` | `383332d49dee1e237d3d8a05e2f3a34402031f98b6d538c7cf0253261794e058` | Stage 2.4 Final Recorded |
| `forensics/metadata_forensics.py` | `26c155d17d047d9ceade3fc8729b806c8d6362d24247424cc75a168fd2c84f1f` | Stage 2.4 Final Recorded |
| `forensics/provenance_verifier.py` | `113b0fb307d86ca2e190292807d7d726634099b747f5abcf62988818ad502fc5` | Stage 2.4 Final Recorded |
| `forensics/frequency_forensics.py` | `96056c3c030df8c2b03641ced63810c846ac33af183997d1f2077e205ac1afe7` | Stage 2.4 Final Recorded |
| `forensics/manipulation_detector.py` | `f6786e94a0245e67dffafe0bfe3cbf312b06b265c50cb2baeff6b5549a315166` | Stage 2.4 Final Recorded |
| `forensics/localization.py` | `206515a9b1a15e59a8e3cf8e2418897428c3d34098b6c2ea90322dd4eaa88448` | Stage 2.4 Final Recorded |
| `forensics/evidence_fusion.py` | `385b34cd6d710b2cde4b8025b594a080ff7042478fbcca6d7fa9121b06b6f622` | Stage 2.4 Final Recorded |
| `forensics/security_hardening.py` | `6ab94486f92d50a2f8fffb718316ac5aaa1b233409bcec140590a078e23a0ca3` | Stage 2.4 Final Recorded |
| `forensics/__init__.py` | `31b8da66180dc3fb7e2d5e69d2c00417fe1f0d429c223b62ec922e401cc5f7b8` | Stage 2.4 Final Recorded |

---

## 3. Verified Image Processing Flow (As-Is Architecture)

The current production image detection workflow was traced across frontend, HTTP routing, inference, persistence, and reporting:

```
[User Browser / Next.js]
  | 1. Form Upload: multipart/form-data ("file", "save_to_cases")
  |    Component: frontend/src/app/dashboard/image/page.tsx (ImageDetectionPage)
  |    Client:    frontend/src/lib/api.ts (imageApi.analyze)
  v
[FastAPI Router: backend/app/api/v1/endpoints/image.py]
  | 2. Rate Limiting: rate_limiter.check("image_analysis")
  | 3. Raw Read: file_bytes = await file.read()
  | 4. Header Validation: with Image.open(io.BytesIO(file_bytes)) as pil_img:
  |    - Checks format in {"JPEG", "JPG", "PNG", "WEBP"}
  |    - Checks width <= 8192, height <= 8192, total_pixels <= IMAGE_MAX_PIXELS
  v
[Detector Engine: backend/app/ml/image/detector.py]
  | 5. analyze_image_bytes(file_bytes, file_name)
  |    - Redundant Image.open(io.BytesIO(image_bytes)) & pil_img.load() [DECODE #2]
  |    - Metadata & Provenance: extract_metadata_and_provenance(pil_img, image_bytes)
  |    - Frequency & Noise: compute_frequency_domain_features, compute_noise_residual_variance
  |    - ELA Heatmap: generate_image_forensic_heatmap(pil_img)
  |    - Primary Swin ViT: self.swin.predict(pil_img) -> [Swin-B forward pass]
  |    - Secondary ViT: self.vit.predict(pil_img) -> [ViT-Base forward pass]
  |    - Aggregator: self.ensemble_aggregator.aggregate(...) -> consensus_score, confidence
  v
[Database Persistence & PDF Generation]
  | 6. ImageAnalysisRecord created in PostgreSQL/SQLite (ORM model in models/image_analysis.py)
  | 7. Optional ForensicReport case archive entry created
  | 8. PDF Export: backend/app/services/pdf_generator.py (generate_image_analysis_pdf)
  v
[HTTP Response: ImageAnalysisResponse]
  | 9. Returned to Next.js frontend and rendered in ImageDetectionPage
```

### Critical Architectural Deficiencies in Current Flow:
1. **Redundant Ingestion & Memory Decoding:** `Image.open()` is called twice (in `image.py` and `detector.py:360`), and would be called a third time if `evidence_fusion.py` was invoked naively.
2. **Missing Pre-Decode Security:** The HTTP upload route calls `Image.open()` *before* verifying image stream headers, expansion ratios, or decompression bomb signatures.
3. **Stage 1 & Stage 2 Disconnection:** Neither `attribute_generator` nor `run_forensic_investigation` is called in the production request cycle.
4. **Dimension Flattening:** The database and API schemas only reflect Dimension A (Synthetic Detection), omitting Dimension B (Manipulation Analysis) and Generator Attribution.

---

## 4. Stage 1 & Stage 2 Module Inventory

Each available module was audited for capabilities, interfaces, dependencies, and integration readiness:

### 4.1 Stage 1 Module: `generator_attribution.py`
- **Location:** `backend/app/ml/image/generator_attribution.py`
- **Purpose:** Identifies likely generative AI engines (Midjourney, DALL-E, Stable Diffusion, Adobe Firefly, etc.) based on hierarchical evidence tiers.
- **Public Interface:**
  `attribute_generator(image: Any, raw_bytes: bytes, heuristic_clues: dict | None = None) -> GeneratorAttributionResult`
- **Data Types:**
  - `EvidenceTier`: `TIER_1_PROVENANCE`, `TIER_2_METADATA`, `TIER_3_HEURISTIC`, `TIER_4_NONE`.
  - `GeneratorOutcome`: `CONFIRMED`, `PROBABLE`, `SUSPECTED`, `UNKNOWN`, `INCONCLUSIVE`.
  - `GeneratorAttributionResult`: Dataclass containing `generator_name`, `generator_family`, `outcome`, `evidence_tier`, `confidence`, `evidence_findings`, `limitations`.
- **Dependencies:** Standard library (`json`, `re`, `struct`), `PIL.Image`. Zero heavy ML dependencies.
- **Empirical Latency:** **0.09 ms** on a $512 \times 512$ image.
- **Integration Readiness:** **100% Ready**. Clean functional interface, thread-safe, fast.

### 4.2 Stage 2 Modules (`backend/app/ml/image/forensics/`)

| Module | Public Interface | Input Types | Output Types | Dependencies | Empirical Latency | Integration Readiness |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `security_hardening.py` | `validate_image_security()`, `sniff_image_dimensions_pre_decode()` | `raw_bytes: bytes` | `tuple[bool, str \| None, dict]` | `struct`, `io`, `PIL.Image` | **0.06 ms** | **100% Ready** (Must be placed before `Image.open`) |
| `metadata_forensics.py` | `analyze_metadata()` | `image: Image.Image` | `tuple[dict, list[EvidenceFinding]]` | `PIL.ExifTags` | **0.01 ms** | **100% Ready** |
| `provenance_verifier.py`| `verify_provenance()` | `raw_bytes: bytes` | `tuple[dict, list[EvidenceFinding]]` | `struct`, standard library | **1.10 ms** | **100% Ready** (Separates manifest, signature, CA, binding) |
| `frequency_forensics.py`| `analyze_frequency_domain()` | `image: Image.Image` | `tuple[dict, list[EvidenceFinding]]` | `numpy.fft` | **60.01 ms** | **100% Ready** |
| `manipulation_detector.py`| `analyze_manipulation()` | `image: Image.Image, raw_bytes: bytes` | `tuple[dict, list[EvidenceFinding], ndarray]` | `numpy`, `io`, `PIL.Image` | **343.52 ms** | **100% Ready** (Has 4,000-block budget & bokeh seam check) |
| `localization.py` | `localize_suspicious_regions()` | `anomaly_map: ndarray, width: int, height: int` | `list[SuspiciousRegion]` | `numpy`, standard library | **4.15 ms** | **100% Ready** |
| `evidence_fusion.py` | `run_forensic_investigation()` | `image: Image.Image \| None, raw_bytes: bytes` | `ForensicReport` | All above forensic modules | **486.26 ms** | **100% Ready** (Orchestrator for Dimension B) |
| `schemas.py` | Enums & Dataclasses | Data schemas | Serialized dictionaries | Standard library `dataclasses`, `enum` | Negligible | **100% Ready** |

---

## 5. Security Integration Plan

### 5.1 Pre-Decode Binary Interception Architecture
The critical vulnerability identified in Stage 2.3 is that `backend/app/api/v1/endpoints/image.py` invokes `Image.open(io.BytesIO(file_bytes))` directly upon receiving the payload.

In Stage 3.1, `validate_image_security` will be positioned as an impassable gate immediately after `await file.read()`:

```
[HTTP Request Stream]
          |
          v
[1. file_bytes = await file.read()]
          |
          v
+--------------------------------------------------------------------------+
| 2. PRE-DECODE SECURITY GATE (security_hardening.py)                      |
|    - Payload byte limit <= 10 MB                                         |
|    - Binary header sniff (PNG IHDR, JPEG SOF0/SOF2, WebP VP8/VP8L)       |
|    - Single-axis dimension check: width <= 8192, height <= 8192          |
|    - Total pixel limit: width * height <= 16,777,216 px                  |
|    - Decompression bomb check: expansion ratio < 120.0x for > 4 MP       |
+--------------------------------------------------------------------------+
          |
     [Is Safe?]
    /          \
  NO           YES
  /              \
[Abort: 422]      [Single Safe Decode: pil_img = Image.open(io.BytesIO(file_bytes))]
                  [pil_img.load() executed ONCE; reused across all modules]
```

### 5.2 Elimination of Redundant Image Decoding
In the unified pipeline:
1. `image.py` opens `pil_img` **once** after passing `validate_image_security`.
2. `pil_img` is passed directly into the unified orchestrator.
3. `detector.py`, `generator_attribution.py`, and `evidence_fusion.py` accept the pre-opened `pil_img` instance.
4. Internal calls to `Image.open(io.BytesIO(raw_bytes))` within downstream modules are replaced with the shared image reference, eliminating up to **7.5 ms** of redundant decode overhead and preventing memory thrashing.

---

## 6. Proposed Unified Analysis Architecture

The unified engine operates as a dual-track analytical pipeline preserving strict mathematical independence between **Dimension A (AI Synthetic Media Detection)** and **Dimension B (Digital Manipulation & Splicing Analysis)**:

```
                                  [ Uploaded Image: file_bytes ]
                                                 |
                                                 v
                                 +-------------------------------+
                                 |   A. Secure Image Ingestion   |
                                 |  (validate_image_security)    |
                                 +-------------------------------+
                                                 |
                                        [ Verified pil_img ]
                                                 |
                   +-----------------------------+-----------------------------+
                   |                                                           |
                   v                                                           v
+--------------------------------------+             +--------------------------------------+
|       DIMENSION A: SYNTHETIC         |             |       DIMENSION B: MANIPULATION      |
|           MEDIA DETECTION            |             |           & PROVENANCE FORENSICS     |
+--------------------------------------+             +--------------------------------------+
| 1. Swin-B Vision Transformer         |             | 1. Generator Attribution (Stage 1)   |
| 2. ViT-Base Self-Attention           |             | 2. Metadata & EXIF Analysis          |
| 3. 2D FFT Spectral Anisotropy        |             | 3. C2PA Provenance & Signature Trust |
| 4. Laplacian Noise Variance          |             | 4. ELA Recompression Discontinuity   |
| 5. Calibrated Consensus Ensemble     |             | 5. Spatial Noise Residual Gradients  |
|                                      |             | 6. Copy-Move Forgery (CMFD, 4k cap)  |
| Output:                              |             | 7. Tampering Localization (Boxes)    |
| - Classification: LIKELY AI / HUMAN  |             |                                      |
| - Consensus Score: P(AI) in [0, 1]   |             | Output:                              |
| - Calibrated Confidence in [0, 1]    |             | - Manipulation Verdict: SPLICING,    |
| - Multi-Detector Score Breakdown     |             |   INPAINTING, RETOUCHING, NONE       |
+--------------------------------------+             | - Heuristic Score & Evidence Strength|
                   |                                 | - Attribution: Family & Engine Name  |
                   |                                 | - Provenance State & Limitations     |
                   |                                 +--------------------------------------+
                   |                                                           |
                   +-----------------------------+-----------------------------+
                                                 |
                                                 v
                               +-----------------------------------+
                               |     H. Unified Result Builder     |
                               |    - Validates Dimension Decoupling|
                               |    - Enforces Uncalibrated Labels |
                               |    - Collects Coverage Telemetry  |
                               +-----------------------------------+
                                                 |
                         +-----------------------+-----------------------+
                         |                                               |
                         v                                               v
           [ HTTP API Response (JSON) ]                     [ Database Persistence ]
         ImageAnalysisResponse (Extended)                     ImageAnalysisRecord
```

### Decoupling Rules Enforced in Unified Builder:
- **Rule 1:** A `SUSPECTED_SPLICING` or `SUSPECTED_INPAINTING` finding in Dimension B **never** increments, decrements, or modulates $P(\text{AI})$ in Dimension A.
- **Rule 2:** The absence of manipulation seams does **never** imply that an image is fully AI-synthesized or authentic.
- **Rule 3:** The presence of a valid C2PA manifest certifies **who signed the claim**, never the factual authenticity of the visual content.
- **Rule 4:** Heuristic scores in Dimension B are explicitly typed as `HEURISTIC_SCORE` and are forbidden from being presented as calibrated probabilities.

---

## 7. Unified Result Schema Design

To guarantee 100% backward compatibility with existing tests and clients while exposing rich multi-dimensional forensics, `ImageAnalysisResponse` in `backend/app/schemas/image_analysis.py` will be extended with optional, defaulted sub-schemas:

### 7.1 New Pydantic Sub-Schemas
```python
class GeneratorAttributionInfo(BaseModel):
    generator_name: str | None = None
    generator_family: str | None = None
    outcome: str = "UNKNOWN"
    evidence_tier: str = "TIER_4_NONE"
    confidence: float = 0.0
    evidence_findings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)

class SuspiciousRegionInfo(BaseModel):
    region_id: str
    quadrant: str
    bounding_box: tuple[int, int, int, int]
    normalized_box: tuple[float, float, float, float]
    anomalous_block_count: int
    primary_indicator: str
    confidence: float

class ForensicAnalysisInfo(BaseModel):
    manipulation_verdict: str = "NO_MANIPULATION_EVIDENCE_DETECTED"
    heuristic_score: float = 0.0
    confidence_type: str = "HEURISTIC_SCORE"
    is_calibrated: bool = False
    evidence_strength: str = "NONE"
    calibration_limitation: str = ""
    suspicious_regions: list[SuspiciousRegionInfo] = Field(default_factory=list)
    cmfd_status: str = "COMPLETED"
    cmfd_blocks_evaluated: int = 0
    disclaimers: list[str] = Field(default_factory=list)
```

### 7.2 Extended `ImageAnalysisResponse` (Top-Level)
```python
class ImageAnalysisResponse(BaseModel):
    # Existing Baseline Fields (100% Preserved)
    analysis_id: int
    user_id: int
    file_hash: str
    file_name: str
    file_size_bytes: int
    image_width: int
    image_height: int
    image_format: str
    model_name: str
    model_version: str
    status: str
    classification: str
    confidence_score: float | None = None
    ai_probability: float | None = None
    human_probability: float | None = None
    raw_score: float | None = None
    fft_high_freq_ratio: float = 0.0
    spectral_anisotropy: float = 0.0
    noise_variance: float = 0.0
    has_ai_metadata: bool = False
    has_c2pa: bool = False
    provenance: ProvenanceInfo | None = None
    evidence: list[ImageEvidenceItem] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    detector_scores: list[ImageDetectorScore] = Field(default_factory=list)
    ensemble: ImageEnsembleBreakdown | None = None
    heatmap: ImageHeatmapData | None = None
    processing_time_ms: float
    created_at: datetime
    case_report_id: int | None = None

    # New Stage 3 Forensic & Attribution Extensions (Defaulted)
    generator_attribution: GeneratorAttributionInfo | None = None
    forensic_analysis: ForensicAnalysisInfo | None = None
    manipulation_verdict: str = "NO_MANIPULATION_EVIDENCE_DETECTED"
    manipulation_heuristic_score: float = 0.0
    evidence_strength: str = "NONE"
    analysis_coverage: dict[str, Any] = Field(default_factory=dict)
    skipped_modules: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
```

---

## 8. Failure and Partial-Result Design

The unified pipeline enforces defensive degradation, ensuring that failures in non-critical components do not crash the request or discard already-computed evidence:

| Failure Scenario | HTTP Status | Response Status | Determination Behavior | Forensic Telemetry Retained |
| :--- | :--- | :--- | :--- | :--- |
| **Empty Upload (0 bytes)** | `422 Unprocessable` | N/A (HTTP Error) | Request rejected immediately. | None |
| **Oversized Stream (> 10 MB)** | `422 Unprocessable` | N/A (HTTP Error) | Request rejected before reading memory. | None |
| **Corrupted Header / Malformed** | `422 Unprocessable` | N/A (HTTP Error) | Caught by pre-decode sniffer. | Header error status |
| **Decompression Bomb (> 120x)** | `422 Unprocessable` | N/A (HTTP Error) | Aborted before PIL allocate. | Telemetry logged in audit log |
| **Dimension Below Gate (< 64x64)** | `200 OK` | `INCONCLUSIVE` | Classification: `INCONCLUSIVE`. $P(\text{AI})=0.5$. | Metadata & FFT computed if possible |
| **Primary Swin ViT Unavailable** | `200 OK` | `BLOCKED` | Returns `BLOCKED`. $P(\text{AI})=\text{None}$. | Full Stage 1 & Stage 2 forensic report retained |
| **ViT Inference Exception** | `200 OK` | `FAILED` | Graceful fallback without leaking stack traces. | Deterministic features preserved |
| **CMFD Over-Budget (> 4,000 blks)** | `200 OK` | `SUCCESS` | `cmfd_status = "SKIPPED_EXCESSIVE_BLOCKS"`. | All other forensic indicators evaluated |
| **Missing Provenance / EXIF** | `200 OK` | `SUCCESS` | `manifest_status = "NO_MANIFEST_PRESENT"`. | Dimension A & B evaluated normally |
| **Database Failure on Commit** | `500 Error` | N/A | Transaction rolled back; no orphaned state. | Logged securely |

---

## 9. Stage-by-Stage Implementation Plan

```
Stage 3.1: Secure Image Ingestion Gate
    │
    ▼
Stage 3.2: Unified Pipeline Orchestrator (Backend ML)
    │
    ▼
Stage 3.3: Extended Result Schemas & ORM Compatibility
    │
    ▼
Stage 3.4: API Route Integration & Exception Handling
    │
    ▼
Stage 3.5: PDF Forensic Report Generator Upgrade
    │
    ▼
Stage 3.6: Frontend Dashboard & Forensic Visualization
    │
    ▼
Stage 3.7: Independent Verification & Regression Audit
```

### Stage 3.1 — Secure Image Ingestion Gate
- **Objective:** Integrate `validate_image_security` into `backend/app/api/v1/endpoints/image.py`. Intercept malformed files, oversized streams, and decompression bombs *before* `Image.open()`.
- **Files Modified:** `backend/app/api/v1/endpoints/image.py`.
- **Files Preserved:** All ML models, frontend, database, tests.
- **Rollback Strategy:** Revert `image.py` from `backups/phase2_baseline_checkpoint/image.py`.
- **Approval Gate:** 21/21 existing baseline image tests pass + dedicated security tests pass.

### Stage 3.2 — Unified Pipeline Orchestrator
- **Objective:** Create `backend/app/ml/image/unified_pipeline.py`. Orchestrates `image_detector`, `attribute_generator`, and `run_forensic_investigation` using a single pre-decoded PIL Image.
- **Files Modified:** New file `backend/app/ml/image/unified_pipeline.py`.
- **Files Preserved:** `detector.py`, `ensemble.py`, `features.py`.
- **Rollback Strategy:** Delete `unified_pipeline.py`.
- **Approval Gate:** Isolated unit tests for orchestrator pass with 100% reproducibility.

### Stage 3.3 — Extended Result Schemas & ORM Compatibility
- **Objective:** Extend `backend/app/schemas/image_analysis.py` with `generator_attribution`, `forensic_analysis`, and `analysis_coverage` with default values. Update `backend/app/models/image_analysis.py` to store extended telemetry in JSON text fields without schema breakage.
- **Files Modified:** `backend/app/schemas/image_analysis.py`, `backend/app/models/image_analysis.py`.
- **Approval Gate:** Schema serialization tests confirm zero breaking changes to existing fields.

### Stage 3.4 — API Route Integration
- **Objective:** Connect `unified_pipeline.py` into `analyze_image` endpoint in `backend/app/api/v1/endpoints/image.py`. Persist extended forensic payload.
- **Files Modified:** `backend/app/api/v1/endpoints/image.py`.
- **Approval Gate:** Full pytest suite (61 tests) passes without regression.

### Stage 3.5 — PDF Forensic Report Generator Upgrade
- **Objective:** Update `generate_image_analysis_pdf` in `backend/app/services/pdf_generator.py` to render Generator Attribution cards, Manipulation Verdict tables, and C2PA Provenance details in exported PDFs.
- **Files Modified:** `backend/app/services/pdf_generator.py`.
- **Approval Gate:** `test_image_analysis_pdf_with_ensemble` passes and generates valid PDF bytes.

### Stage 3.6 — Frontend Dashboard & Forensic Visualization
- **Objective:** Update `frontend/src/app/dashboard/image/page.tsx` and `api.ts` to display:
  1. Dimension A (AI Probability & Consensus Badge)
  2. Dimension B (Manipulation Verdict & Evidence Strength)
  3. Generator Attribution Badge
  4. C2PA Provenance Breakdown Card
  5. Interactive Tampering Bounding Box Overlays
- **Files Modified:** `frontend/src/app/dashboard/image/page.tsx`, `frontend/src/lib/api.ts`.
- **Approval Gate:** Browser smoke test and visual verification.

### Stage 3.7 — Independent Verification & Final Acceptance
- **Objective:** Comprehensive independent audit verifying all 61+ regression tests, security boundaries, performance latency, and baseline hash integrity.

---

## 10. Test Strategy

```
+-------------------------------------------------------------------------------+
|                             AICF TEST PYRAMID                                 |
+-------------------------------------------------------------------------------+
|  Level 1: Unit Tests (30 Tests)                                               |
|    - Isolated tests for security_hardening, provenance_verifier, CMFD,        |
|      metadata_forensics, frequency_forensics, generator_attribution.          |
+-------------------------------------------------------------------------------+
|  Level 2: Pipeline Integration Tests (15 Tests)                               |
|    - Unified orchestrator tests (two-dimensional decoupling, failure fallbacks)|
+-------------------------------------------------------------------------------+
|  Level 3: API End-to-End Regression Tests (25 Tests)                          |
|    - FastAPI test client tests in test_image_analysis.py (Auth, DB, PDF)      |
+-------------------------------------------------------------------------------+
|  Level 4: Adversarial & Fuzzing Benchmark Tests (10 Tests)                    |
|    - Zip bombs, truncated manifests, periodic textures, shallow bokeh portraits|
+-------------------------------------------------------------------------------+
```

---

## 11. Performance Plan

### 11.1 Empirical Latency Measurements (Benchmarked on Windows Host, CPU)
Tested on a standard $512 \times 512$ RGB JPEG image:

| Component / Function | Measured Execution Time | Percentage of Total |
| :--- | :--- | :--- |
| `1. validate_image_security` | **0.06 ms** | 0.002% |
| `2. PIL Image.open + load` (Single Decode) | **3.72 ms** | 0.12% |
| `3. attribute_generator` | **0.09 ms** | 0.003% |
| `4. analyze_metadata` | **0.01 ms** | 0.0003% |
| `5. verify_provenance` | **1.10 ms** | 0.03% |
| `6. analyze_frequency_domain` (2D FFT) | **60.01 ms** | 1.89% |
| `7. analyze_manipulation` (ELA + Noise + CMFD) | **343.52 ms** | 10.82% |
| `8. localize_suspicious_regions` | **4.15 ms** | 0.13% |
| **Forensic Subtotal (Dimension B + Attr)** | **486.26 ms** | **15.32%** |
| `9. Swin-B + ViT Primary Inference` (Dimension A) | **2,686.82 ms** | **84.68%** |
| **PROJECTED TOTAL UNIFIED LATENCY** | **~3,173.08 ms** | **100.0%** |

### Latency Conclusion:
Adding Stage 1 Generator Attribution and Stage 2 Forensic Analysis increases request latency by only **~486 ms (an 18% delta)** over the existing heavy vision transformer forward pass. In return, the platform gains full manipulation detection, localization, and provenance telemetry.

---

## 12. Rollback & Disaster Recovery Strategy

If an unexpected failure or regression occurs during any Stage 3 integration step:

1. **Clean Baseline Checkpoint:** The pristine backup remains at:
   `C:\Users\acer\IMAGE\backups\phase2_baseline_checkpoint\`
2. **Instant Revert Protocol:**
   - Revert `backend/app/api/v1/endpoints/image.py` from `backups/phase2_baseline_checkpoint/image.py`.
   - Revert `backend/app/schemas/image_analysis.py` to pre-Stage 3 hash (`ad3179b5...`).
   - Remove `backend/app/ml/image/unified_pipeline.py`.
3. **Automated Verification:** Run `pytest backend/tests/test_image_analysis.py` to confirm the baseline is instantly restored.

---

## 13. Risks and Unresolved Questions

1. **Client-Side Timeout on Large Images:**
   On images $> 2000 \times 2000$ pixels, vision transformer resizing combined with 2D FFT and CMFD could push latency to 5–6 seconds on CPU. The Next.js frontend fetch timeout must be verified to be at least 15 seconds.
2. **PostgreSQL Column Size Constraints:**
   If `evidence_json` or `provenance_json` exceeds default text limits on certain external SQL configurations, fields must be trimmed. On standard SQLite/PostgreSQL, `Text` columns support unlimited lengths.
3. **C2PA Python SDK Installation Requirement:**
   Cryptographic signature validation and root CA trust chain checking remain offline (`SIGNATURE_UNVERIFIED`) until the user approves package installation of `c2pa-python`.

---

## 14. Exact Recommendation for Stage 3.1

**Recommendation:** Proceed immediately with **Stage 3.1: Secure Image Ingestion Gate**.
- **Target File:** `backend/app/api/v1/endpoints/image.py`.
- **Action:** Import `validate_image_security` from `backend.app.ml.image.forensics.security_hardening` and invoke it immediately after `await file.read()`.
- **Zero Risk:** Does not alter model inference, response schemas, or database records. Immediately eliminates server-side decompression bomb vulnerabilities in the live upload route.
- **Verification:** Run `pytest backend/tests/test_image_analysis.py` to ensure all 21 existing baseline tests pass.

---

## 15. Final Stop Condition

Stage 3.0 Architecture Audit is **COMPLETE**.

In strict adherence to instructions:
- **No source code was edited.**
- **No files were deleted or renamed.**
- **No packages were installed.**
- **Implementation has NOT begun.**
- **Awaiting user review and explicit approval before commencing Stage 3.1.**
