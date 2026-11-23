# AICF Phase 2 — Multi-Model AI Image Forensics Engine: Acceptance Checklist

**Project:** `C:\Users\acer\IMAGE`  
**Phase:** Phase 2 — Advanced Multi-Model AI Image Forensics Engine  
**Date:** 2026-11-18  
**Status:** **AWAITING USER AUTHORIZATION PRIOR TO IMPLEMENTATION**  
**Document Target:** `docs/PHASE_2_ACCEPTANCE_CHECKLIST.md`

---

## 1. Architectural Boundaries & Scientific Safeguards

- [ ] **Two Independent Result Dimensions Enforced:**
  - Dimension A (Synthetic Detection) and Dimension B (Manipulation Analysis) are computed and returned as completely separate objects in the API, database JSON, and UI.
  - Manipulation scores **never** modulate or silently alter synthetic probability $P(\text{AI})$.
  - Absence of manipulation seams **never** infers full synthesis; it strictly maps to `NO_MANIPULATION_EVIDENCE_DETECTED`.
- [ ] **No 100% Certainty Claims:**
  - No detector, heuristic, or metadata parser claims 100% accuracy in code, logs, UI, or PDF outputs.
  - Mandatory support for `UNKNOWN` in generator attribution and `INSUFFICIENT_EVIDENCE` in manipulation analysis.
- [ ] **Provisional Calibration Notation:**
  - Temperature scaling ($T = 1.20$) and covariance penalty ($\rho = 0.68$) are explicitly labeled as `PROVISIONAL_HEURISTIC` in API responses, UI meters, and PDF reports.
- [ ] **Zero Package Overhead:**
  - Zero new external Python packages installed; runs entirely on existing baseline dependencies.
- [ ] **Zero Database Schema Migrations:**
  - No `ALTER TABLE` statements; SQLite table `image_analyses` schema is unaltered. All new telemetry serializes inside `ensemble_json`.

---

## 2. Dimension A: Synthetic Media Detection Criteria

- [ ] **Classification States:**
  - Output strictly restricted to: `LIKELY_SYNTHETIC`, `LIKELY_HUMAN`, or `INCONCLUSIVE`.
- [ ] **Decision Thresholds:**
  - $P(\text{AI}) \ge 0.70 \implies \text{LIKELY\_SYNTHETIC}$
  - $P(\text{AI}) \le 0.30 \implies \text{LIKELY\_HUMAN}$
  - $0.30 < P(\text{AI}) < 0.70 \implies \text{INCONCLUSIVE}$
  - Image resolution $< 32 \times 32$ pixels forces `INCONCLUSIVE` with confidence $0.0$.
- [ ] **Ensemble Aggregation:**
  - Integrates Swin-B Transformer (`umm-maybe/AI-image-detector`) as primary backbone.
  - Integrates ViT-Base Transformer (`capcheck/ai-image-detection`) as gated secondary backbone.
  - Incorporates 2D Fourier (FFT) 8-octant spectral anisotropy and Laplacian noise variance as orthogonal physical priors.
  - Applies temperature scaling ($T = 1.20$) and empirical covariance penalty ($\rho = 0.68$).
- [ ] **Evidence Strength Grading:**
  - Assigns categorical grade: `STRONG`, `MODERATE`, `WEAK`, or `INCONCLUSIVE`.
- [ ] **Disagreement & Uncertainty Telemetry:**
  - Synthesizes a written `disagreement_analysis` narrative explaining concordances/conflicts between deep vision and signal metrics.
  - Logs explicit `uncertainty_drivers` (e.g., `HIGH_JPEG_COMPRESSION`, `DISCORDANT_NEURAL_BACKBONES`, `STRIPPED_EXIF_METADATA`).

---

## 3. Dimension B: Digital Manipulation Analysis Criteria

- [ ] **Classification States:**
  - Output strictly restricted to:
    1. `SUSPECTED_INPAINTING`
    2. `SUSPECTED_SPLICING`
    3. `SUSPECTED_RETOUCHING`
    4. `NO_MANIPULATION_EVIDENCE_DETECTED`
    5. `INSUFFICIENT_EVIDENCE`
- [ ] **Signal Processing Implementation:**
  - Evaluates $16 \times 16$ macro-block Error Level Analysis (ELA) compression variance.
  - Evaluates inter-quadrant Laplacian spatial noise variance gradients.
  - Evaluates RGB cross-channel covariance shifts.
- [ ] **Edge-Mask Damping:**
  - High-frequency Sobel/Scharr edge mask applied to damp false positive ELA spikes on sharp natural photographic edges.
- [ ] **Forensic Evidence & Localization Schema Populated:**
  - `observed_signal`: Specific physical anomaly observed (e.g., "Elevated 16x16 ELA block variance in Q2").
  - `supporting_indicators`: List of corroborating metrics (e.g., noise variance delta, color covariance shifts).
  - `region_localization`: Dictionary containing quadrant ID, bounding box `[ymin, xmin, ymax, xmax]`, and anomalous block count (if localized).
  - `evidence_strength`: Categorical classification (`STRONG`, `MODERATE`, `WEAK`, `INCONCLUSIVE`).
  - `finding_type`: Explicitly declared as `HEURISTIC` or `MODEL_SUPPORTED`.
  - `limitations`: Mandatory warning list (e.g., "ELA alone does not prove manipulation").
- [ ] **Insufficient Evidence Handling:**
  - Uncompressed formats without JPEG history, low resolution ($<64 \times 64$), or severe recompression ($Q < 50$) output `INSUFFICIENT_EVIDENCE`.

---

## 4. Generator Attribution Criteria

- [ ] **Evidence-Tier Separation:**
  - Evaluates evidence in four discrete tiers:
    1. *Direct Provenance Evidence:* Signed C2PA manifests.
    2. *Metadata-Based Clues:* PNG text chunks (`parameters`, `workflow`), software tags.
    3. *Statistical Model Predictions:* Neural feature correlations.
    4. *Heuristic Indicators:* Canonical dimension pairs, aspect ratios, Fourier grid harmonics.
- [ ] **Target Family Coverage:**
  - Detects `Midjourney`, `Stable Diffusion` (including `ComfyUI` / `Automatic1111`), `DALL-E` ($2/3$), `FLUX.1`, `Adobe Firefly`, and `UNKNOWN / GENERIC`.
- [ ] **Fail-Safe & Uncertainty:**
  - If metadata is stripped and heuristics are below confidence threshold, outputs `primary_generator = "UNKNOWN"`, `confidence = 0.0`, `evidence_tier = "NONE"`.

---

## 5. Model Registry & Raw Telemetry Criteria

- [ ] **Telemetry Standards:**
  - Every active detector in the ensemble returns a `ModelRegistryEntry` containing:
    - `model_id`: String identifier (e.g., `swin-b-vit-forensics`, `vit-base-global`).
    - `version`: String version.
    - `model_type`: Categorical (`TRANSFORMER_LOCAL`, `TRANSFORMER_GLOBAL`, `HEURISTIC_SIGNAL`).
    - `input_dimensions`: List of dimensions (e.g., `[3, 224, 224]`).
    - `raw_output`: Dict containing uncalibrated `logits`, `raw_probs`, and execution `device`.
    - `latency_ms`: Measured execution time in milliseconds.

---

## 6. Backward Compatibility & System Integrity Criteria

- [ ] **Phase 3 Video Screening Invariant:**
  - `classify_image(self, image: Image.Image) -> tuple[float, float, float]` in `backend/app/ml/image/detector.py` retains its exact signature, parameter types, and return contract `(ai_probability, human_probability, raw_score)`.
  - Video module (`backend/app/ml/video/detector.py`) imports and calls `classify_image()` with zero regressions.
- [ ] **Historical Case Readability:**
  - Historical `image_analyses` records created in Phase 1 deserialize cleanly from `ensemble_json` with new Phase 2 fields defaulting to `None`.
  - Endpoint `GET /api/v1/image/analyses` and `GET /api/v1/image/analyses/{id}` return historical records without HTTP 500 errors.
- [ ] **Pydantic Model Robustness:**
  - All schemas enforce `model_config = ConfigDict(extra="ignore")`.

---

## 7. Forensic PDF Report Criteria

- [ ] **Two-Section Visual Layout:**
  - **Section A:** Synthetic Media Determination (Classification banner, probability gauge, generator attribution card, multi-model consensus table).
  - **Section B:** Digital Manipulation & Tampering Analysis (Manipulation badge, observed signals, supporting indicators, localization coordinates, forensic limitations).
- [ ] **Dual Heatmap Embedding:**
  - Embeds base64 ELA and Noise Residual heatmaps with scale legends.
- [ ] **Integrity & Compliance Disclaimers:**
  - Displays SHA-256 integrity hash, execution timestamp, and explicit disclaimer stating that calibration is provisional and heuristics do not constitute absolute legal proof.

---

## 8. Frontend UI/UX (Obsidian-Gold) Criteria

- [ ] **Two Dedicated Dimension Cards:**
  - **Card 1 (Synthetic Origin):** `LIKELY_SYNTHETIC`, `LIKELY_HUMAN`, or `INCONCLUSIVE` badge, calibrated probability gauge, generator attribution breakdown bar.
  - **Card 2 (Manipulation Analysis):** 5-state manipulation badge, observed signal details, region localization drawer, limitations alert.
- [ ] **Consensus Hub & Heatmap Switcher:**
  - Displays model registry badges (raw logits, dims, device).
  - Interactive switcher toggling between Original Raster, ELA Heatmap, and Noise Residual Heatmap.
- [ ] **Design Language Consistency:**
  - Obsidian-and-gold aesthetic preserved with responsive desktop and mobile viewports.

---

## 9. Comprehensive Test Suite & Regression Verification

The expanded test suite `backend/tests/test_image_analysis.py` (35+ tests) must pass with zero failures:

### Detailed Test Checklist:

```
[ ] test_image_analysis_valid_jpeg                             (Valid real JPEG handling)
[ ] test_image_analysis_valid_png                              (Valid real PNG handling)
[ ] test_image_analysis_valid_webp                             (Valid WebP format handling)
[ ] test_image_analysis_empty_file                             (0-byte upload rejection: HTTP 400)
[ ] test_image_analysis_corrupted_file                         (Malformed byte rejection: HTTP 400)
[ ] test_image_analysis_unsupported_format                     (Non-image rejection: HTTP 400)
[ ] test_image_analysis_oversized_file                         (Exceeding 10MB limit: HTTP 413)
[ ] test_image_analysis_low_resolution_gate                    (<32x32 forces INCONCLUSIVE)
[ ] test_image_analysis_generator_attribution_direct_provenance (C2PA signed manifest parsing)
[ ] test_image_analysis_generator_attribution_midjourney        (Midjourney prompt parameter mining)
[ ] test_image_analysis_generator_attribution_stablediffusion   (ComfyUI / A1111 parameter mining)
[ ] test_image_analysis_generator_attribution_canonical_heurist (Resolution / aspect ratio matching)
[ ] test_image_analysis_generator_attribution_unknown_fallback (Stripped metadata outputs UNKNOWN)
[ ] test_image_analysis_manipulation_suspected_inpainting      (Localized block anomaly detection)
[ ] test_image_analysis_manipulation_suspected_splicing        (Noise variance gradient discrepancy)
[ ] test_image_analysis_manipulation_suspected_retouching      (Smooth compression anomaly detection)
[ ] test_image_analysis_manipulation_no_evidence_detected      (Authentic camera image baseline)
[ ] test_image_analysis_manipulation_insufficient_evidence     (Severe compression Q<50 outputs INSUFFICIENT)
[ ] test_image_analysis_manipulation_zero_score_contamination  (Manipulation finding does not alter P(AI))
[ ] test_image_analysis_manipulation_localization_coordinates  (Quadrant & bounding box verification)
[ ] test_image_analysis_model_registry_telemetry               (Logits, raw_probs, dims, device verification)
[ ] test_image_analysis_classify_image_backward_compatibility  (Frozen classify_image() contract check)
[ ] test_image_analysis_disagreement_analysis_concordant       (Concordant backbones narrative)
[ ] test_image_analysis_disagreement_analysis_discordant       (Discordant backbones narrative)
[ ] test_image_analysis_uncertainty_drivers_logging            (Correct risk tag extraction)
[ ] test_image_analysis_evidence_strength_grades               (STRONG / MODERATE / WEAK / INCONCLUSIVE)
[ ] test_image_analysis_secondary_model_fallback               (Graceful secondary model gating)
[ ] test_image_analysis_pdf_generation                         (Two-section ReportLab PDF generation)
[ ] test_image_analysis_user_isolation                         (Cross-tenant security enforcement)
[ ] test_image_analysis_benchmark_evaluation                   (Precision, Recall, F1, FPR, FNR)
[ ] test_image_analysis_provisional_calibration_labeling       (PROVISIONAL_HEURISTIC label check)
[ ] test_image_analysis_historical_record_deserialization      (Backward compatibility with Phase 1 DB)
[ ] test_image_analysis_performance_instrumentation            (Latency <200ms target, RAM <20MB target)
[ ] test_image_analysis_edge_mask_damping                      (High-contrast edge false alarm suppression)
[ ] test_image_analysis_c2pa_byte_signature_detection          (C2PA manifest scanning)
```

### System-Wide Regression Checklist:
- [ ] **Text Module Regression:** All 21 text tests in `backend/tests/test_text_analysis.py` pass.
- [ ] **Video Module Regression:** All 23 video tests in `backend/tests/test_video_analysis.py` pass.
- [ ] **Core, Auth & Cloud Regression:** All 47 core/auth/cloud/pdf tests pass.
- [ ] **Full Backend Test Suite:** All 140+ backend tests pass (`pytest backend/tests`).
- [ ] **Frontend TypeScript Validation:** `npx tsc --noEmit` completes with 0 errors.
- [ ] **Frontend Production Build:** `npm run build` succeeds with all 14 routes statically generated.

---

## 10. Formal Sign-Off Gate

| Gate Milestone | Responsible Role | Verification Method | Status |
| :--- | :--- | :--- | :---: |
| **Safety Review & Architecture Correction** | Lead System Architect | Audit of planning docs | **COMPLETED** |
| **User Implementation Authorization** | Project Owner / User | Explicit approval prompt | **PENDING** |
| **Phase 2 Implementation Execution** | Engineering Team | Steps 1–8 of implementation plan | ON HOLD |
| **Test Suite & Regression Verification** | QA / Forensic Validation | 140+ backend tests, Next.js build | ON HOLD |
| **Final Implementation Audit Report** | Lead Auditor | `PHASE_2_IMPLEMENTATION_REPORT.md` | ON HOLD |

