# AICF Phase 2 — Multi-Model AI Image Forensics Engine: Final Technical Safety Review
*(Architecture Correction & Two-Dimension Forensic Separation)*

**Project:** `C:\Users\acer\IMAGE`  
**Date:** 2026-11-18  
**Status:** **TECHNICAL SAFETY REVIEW COMPLETED — STRICT HOLD AWAITING USER APPROVAL**  
**Document Target:** `docs/PHASE_2_FINAL_SAFETY_REVIEW.md`

---

## 1. Executive Summary & Review Scope

This Technical Safety Review incorporates the final architectural corrections mandated for **AICF Phase 2: Advanced Multi-Model AI Image Forensics Engine**.

### Core Structural Principles:
1. **Two Independent Forensic Dimensions:** Synthetic media detection (Dimension A) and digital manipulation analysis (Dimension B) are strictly decoupled. The system **never** infers full synthesis from the absence of manipulation seams, and manipulation findings **never** alter synthetic probability.
2. **Detailed Evidence & Localization for Manipulation:** Every manipulation finding articulates the observed signal, supporting indicators, region/localization info, evidence strength, limitations, and finding nature (`HEURISTIC` vs `MODEL_SUPPORTED`). ELA and noise residuals alone are explicitly barred from being claimed as proof of manipulation.
3. **Rigorous Empirical Dataset & Calibration Validation:** Exact dataset sources (RAISE-1k, ImageNet, GenImage, Synthbuster, CASIA v2), licensing, balance, perturbations, train/val/test isolation, and calibration metrics (ECE, Brier, reliability diagrams) are documented. Calibration parameters ($T=1.20, \rho=0.68$) remain provisional until empirically validated.
4. **Strict Backward Compatibility:** The signature and return contract of `classify_image()` in `detector.py` remain frozen for Phase 3 video processing. Database schema remains unmodified with zero `ALTER TABLE` migrations. Historical records remain fully readable.
5. **Performance Design Targets:** All latency and memory metrics are formally treated as design targets and instrumented via `time.perf_counter()`, `tracemalloc`, and `psutil`.

---

## 2. Confirmed Findings & Architectural Decoupling

```
+----------------------------------------------------------------------------------------------------+
|                                    INDEPENDENT RESULT DIMENSIONS                                   |
+----------------------------------------------------------------------------------------------------+
| DIMENSION A: SYNTHETIC DETECTION                  | DIMENSION B: MANIPULATION ANALYSIS             |
+---------------------------------------------------+------------------------------------------------+
| - Evaluates global generative AI markers          | - Evaluates localized tampering & inpainting   |
| - Outputs:                                        | - Outputs:                                     |
|   * LIKELY_SYNTHETIC                              |   * SUSPECTED_INPAINTING                       |
|   * LIKELY_HUMAN                                  |   * SUSPECTED_SPLICING                         |
|   * INCONCLUSIVE                                  |   * SUSPECTED_RETOUCHING                       |
|                                                   |   * NO_MANIPULATION_EVIDENCE_DETECTED          |
|                                                   |   * INSUFFICIENT_EVIDENCE                      |
| - Never altered by manipulation scores            | - Never infers full synthesis from clean seams |
+---------------------------------------------------+------------------------------------------------+
```

1. **Separation of Concerns:** Deep vision backbones (Swin-B and ViT-Base) evaluate holistic synthetic representation. Deterministic ELA and noise variance gradients evaluate localized spatial continuity.
2. **Video Screening Invariant:** OpenCV video frame screening imports `image_detector.classify_image()` directly. Preserving `classify_image(image: Image.Image) -> tuple[float, float, float]` guarantees zero regression in Phase 3 video screening.
3. **Database Integrity:** Zero SQLite alterations. Full telemetry encapsulated inside `ensemble_json`. Historical records deserialize seamlessly with missing fields defaulting to `None`.
4. **Zero Package Overhead:** Runs natively in Python 3.12 with existing dependencies (`torch`, `transformers`, `pillow`, `scipy`, `numpy`, `reportlab`).

---

## 3. Unverified Assumptions & Corrective Measures

| Unverified Assumption | Identified Risk | Corrective Policy / Implementation Safeguard |
| :--- | :--- | :--- |
| **"Absence of manipulation seams implies full AI synthesis"** | Severe logical fallacy. Authentic, unmanipulated camera photographs also possess zero manipulation seams. | **CORRECTED:** The absence of manipulation seams strictly maps to `NO_MANIPULATION_EVIDENCE_DETECTED`. Full synthesis is evaluated solely by Dimension A (Synthetic Detection backbones). |
| **"Manipulation severity should modulate synthetic probability $P(\text{AI})$"** | Semantic confusion; an authentic photo retouched in Photoshop is not an AI-generated image. | **CORRECTED:** Dimension A and Dimension B are completely orthogonal. Manipulation findings never modify $P(\text{AI})$ or synthetic classifications. |
| **"ELA and noise residuals prove manipulation"** | False alarms on high-contrast photographic edges; false negatives on recompressed imagery. | **CORRECTED:** ELA and noise residuals are exploratory anomaly indicators. Edge-mask damping is applied. Findings require structured evidence, region localization, and explicit limitations disclaimers. |
| **"Temperature scaling ($T=1.20$) and covariance penalty ($\rho=0.68$) are calibrated"** | Presenting uncalibrated heuristic scores as certified posterior probabilities violates scientific rigor. | **CORRECTED:** Explicitly labeled as **provisional heuristic baselines**. Outlined empirical calibration roadmap (RAISE, GenImage, ECE, Brier score) required before certification. |
| **"Inference latency (<200ms) and memory (<20MB) are guaranteed"** | Hardware variations cause unpredictable execution times. | **CORRECTED:** Formally classified as **engineering design targets**. Require instrumentation via `time.perf_counter()`, `tracemalloc`, and `psutil`. |

---

## 4. Technical Risks & Mitigation Strategies

```
+------------------------------------+----------+----------------------------------------------------+
| Risk Description                   | Severity | Mitigation Strategy                                |
+------------------------------------+----------+----------------------------------------------------+
| 1. Breaking Video Screening        | CRITICAL | Preserve `classify_image()` signature and return   |
|    (`classify_image`)              |          | contract exactly. Add direct regression test.      |
| 2. Pydantic validation failure on  | HIGH     | Mark all new fields Optional with default=None.    |
|    historical database records     |          | Enforce `ConfigDict(extra="ignore")` across models.|
| 3. False alarms on real high-      | MEDIUM   | Apply high-frequency edge-mask damping before      |
|    contrast contours in ELA        |          | calculating block-level ELA variance.              |
| 4. Next.js build failure on new    | MEDIUM   | Extend TypeScript interfaces in `api.ts` to mirror |
|    telemetry fields                |          | Pydantic schema; run `npx tsc --noEmit` and build. |
| 5. Conflating manipulation and     | MEDIUM   | Enforce two independent schema objects in API,     |
|    synthetic classifications       |          | database JSON, PDF report, and frontend UI.        |
+------------------------------------+----------+----------------------------------------------------+
```

---

## 5. Backward Compatibility Safeguards

1. **Video Module Backward Compatibility:**
   - Method: `classify_image(self, image: Image.Image) -> tuple[float, float, float]`
   - Return Value: `(ai_probability, human_probability, raw_score)`
   - Safeguard: Retains exact existing signature and return contract in `detector.py`.
2. **Database Schema Backward Compatibility:**
   - Zero SQLite schema alterations (`ALTER TABLE`).
   - Extended telemetry encapsulated inside `ensemble_json`.
   - Historical records deserialize cleanly with default `None`.
3. **API Response Backward Compatibility:**
   - Top-level `classification` retained (aliased to `synthetic_detection.classification`).
   - All new telemetry fields marked `Optional` with `ConfigDict(extra="ignore")`.

---

## 6. Exact Files to Modify & Create

### New Files to Create:
1. `backend/app/ml/image/generator_attribution.py`: Multi-tier generator attribution supporting `UNKNOWN`.
2. `backend/app/ml/image/manipulation.py`: 5-state manipulation detection with structured localization and limitations.

### Existing Files to Modify:
1. `backend/app/ml/image/detector.py`: Model registry telemetry exposure; strict preservation of `classify_image()`.
2. `backend/app/ml/image/ensemble.py`: Decouple manipulation from synthetic scoring; provisional calibration notation.
3. `backend/app/schemas/image_analysis.py`: Two-dimension Pydantic schemas with `ConfigDict(extra="ignore")`.
4. `backend/app/api/v1/endpoints/image.py`: JSON serialization/deserialization into `ensemble_json`.
5. `backend/app/services/pdf_generator.py`: Two-section forensic PDF layout (Synthetic Media vs Manipulation Analysis).
6. `frontend/src/lib/api.ts`: TypeScript interface extensions for both dimensions.
7. `frontend/src/app/dashboard/image/page.tsx`: Two dedicated UI cards (Synthetic Origin vs Manipulation Analysis).
8. `backend/tests/test_image_analysis.py`: Test suite expansion from 27 to 35+ tests.

---

## 7. Acceptance Criteria

Phase 2 will be accepted only when all criteria in [PHASE_2_ACCEPTANCE_CHECKLIST.md](file:///C:/Users/acer/IMAGE/docs/PHASE_2_ACCEPTANCE_CHECKLIST.md) are met:
1. **Dimension A:** Produces `LIKELY_SYNTHETIC`, `LIKELY_HUMAN`, or `INCONCLUSIVE`.
2. **Dimension B:** Produces `SUSPECTED_INPAINTING`, `SUSPECTED_SPLICING`, `SUSPECTED_RETOUCHING`, `NO_MANIPULATION_EVIDENCE_DETECTED`, or `INSUFFICIENT_EVIDENCE`.
3. **Decoupled Scoring:** Manipulation finding has zero mathematical impact on $P(\text{AI})$.
4. **Structured Evidence & Localization:** Manipulation findings detail observed signal, supporting indicators, region localization, evidence strength, limitations, and finding type.
5. **No Certainty Overclaims:** ELA is never described as proof; generator attribution supports `UNKNOWN`.
6. **Video Screening Intact:** `classify_image()` produces identical outputs for video frame screening.
7. **Zero Database Migrations:** SQLite schema unmodified; historical records fully readable.
8. **Expanded Test Suite Passing:** All 35+ image tests pass without warnings.
9. **Full Regression Passing:** All 140+ backend tests pass.
10. **Clean Production Build:** Frontend passes TypeScript check and production build (`npm run build`).

---

## 8. Final Implementation Sequence (Awaiting Explicit Approval)

- **Step 1:** Implement `backend/app/ml/image/generator_attribution.py` (4 evidence tiers, mandatory `UNKNOWN` support).
- **Step 2:** Implement `backend/app/ml/image/manipulation.py` (5-state taxonomy, edge-mask damping, localization drawer, limitations).
- **Step 3:** Refactor `backend/app/ml/image/detector.py` (model registry, raw telemetry; freeze `classify_image`).
- **Step 4:** Refactor `backend/app/ml/image/ensemble.py` (decouple manipulation from synthetic scoring; provisional calibration notation).
- **Step 5:** Extend `backend/app/schemas/image_analysis.py` (two-dimension schemas with `ConfigDict(extra="ignore")`).
- **Step 6:** Update `backend/app/api/v1/endpoints/image.py` (database persistence and unpacking).
- **Step 7:** Update `backend/app/services/pdf_generator.py` (two-section forensic PDF layout).
- **Step 8:** Update `frontend/src/lib/api.ts` & `frontend/src/app/dashboard/image/page.tsx` (two dedicated UI cards).
- **Step 9:** Expand and execute `backend/tests/test_image_analysis.py` (35+ tests) with active latency/memory instrumentation.
- **Step 10:** Execute full backend regression suite (140+ tests across text, image, video, auth, cloud, PDF).
- **Step 11:** Execute frontend TypeScript validation (`npx tsc --noEmit`) and production build (`npm run build`).
- **Step 12:** Compile `docs/PHASE_2_IMPLEMENTATION_REPORT.md` and present completion audit.
