# AICF Phase 2 — Multi-Model AI Image Forensics Engine: Final Implementation Plan
*(Architecture Correction & Two-Dimension Forensic Separation)*

**Project:** `C:\Users\acer\IMAGE`  
**Date:** 2026-11-18  
**Status:** **FINAL ARCHITECTURE APPROVED FOR PLANNING — STRICT HOLD AWAITING IMPLEMENTATION AUTHORIZATION**  
**Document Target:** `docs/PHASE_2_FINAL_IMPLEMENTATION_PLAN.md`

---

## 1. Architectural Design: Two Independent Forensic Dimensions

A foundational principle of forensic media analysis is that **authenticity is multidimensional**:
- An image may be 100% synthetically generated from scratch.
- An image may be an authentic camera photograph with localized generative inpainting or spliced elements.
- An image may be an authentic camera photograph with zero modifications.
- An image may be synthetically generated and contain no localized seams because it was generated globally.

To prevent category errors, false certainty, and cross-contamination, Phase 2 implements **Two Completely Orthogonal Result Dimensions**:

```
                         [ Input Image Raster & Raw Bytes ]
                                         |
     +-----------------------------------+-----------------------------------+
     |                                                                       |
     v                                                                       v
[ DIMENSION A: SYNTHETIC DETECTION ]                   [ DIMENSION B: MANIPULATION ANALYSIS ]
  - Evaluates global generative markers                  - Evaluates localized editing anomalies
  - Deep Vision Backbones:                               - Deterministic Signal Processing:
    * Swin-B ViT (Primary)                                 * 16x16 Block ELA Discontinuity
    * ViT-Base (Gated Secondary)                           * High-frequency Edge-Mask Damping
    * Model Registry Telemetry                             * Spatial Noise Variance Gradients
  - Orthogonal Spectral Priors:                            * Inter-quadrant Color Covariance
    * 2D Fourier (FFT) Anisotropy                        - Outputs:
    * Global Laplacian Noise Residuals                     * SUSPECTED_INPAINTING
  - Provisional Ensemble (T=1.20, rho=0.68)                * SUSPECTED_SPLICING
  - Outputs:                                               * SUSPECTED_RETOUCHING
    * LIKELY_SYNTHETIC                                     * NO_MANIPULATION_EVIDENCE_DETECTED
    * LIKELY_HUMAN                                         * INSUFFICIENT_EVIDENCE
    * INCONCLUSIVE                                       - Includes Structured Region Localization
```

### Strict Architectural Boundaries:
1. **No Mutual Inference:** The absence of manipulation seams must **NEVER** be used to infer full synthetic generation. An image with no manipulation seams may be an unedited authentic photograph or an unedited synthetic generation.
2. **Zero Score Cross-Contamination:** Manipulation scores must **NEVER** silently alter or inflate the synthetic probability score $P(\text{AI})$. They represent distinct physical phenomena and remain completely decoupled in logic and scoring.
3. **Evidence Strength Decoupling:** An image may have `LIKELY_SYNTHETIC` with `STRONG` evidence while simultaneously having `NO_MANIPULATION_EVIDENCE_DETECTED` for localized tampering. Conversely, an image may be `LIKELY_HUMAN` (overall authentic camera capture) with `SUSPECTED_INPAINTING` (localized generative fill in a bounding region).

---

## 2. Dimension Specifications & Schemas

### 2.1 Dimension A: Synthetic Detection Engine

Evaluates whether the holistic image raster was produced by a generative AI model or captured by an optical camera sensor.

- **Classifications:**
  - `LIKELY_SYNTHETIC`: Strong or moderate global synthesis artifacts detected ($P(\text{AI}) \ge 0.70$).
  - `LIKELY_HUMAN`: Consistent optical sensor noise, physical optics, and camera characteristics ($P(\text{AI}) \le 0.30$).
  - `INCONCLUSIVE`: Borderline scores ($0.30 < P(\text{AI}) < 0.70$), discordant models, low resolution ($<32 \times 32$), or severe degradation.
- **Components:**
  - `SwinImageDetector` (`umm-maybe/AI-image-detector`): Local shifted-window patch representation.
  - `VitImageDetector` (`capcheck/ai-image-detection`): Global semantic and structural attention (resource-gated).
  - 2D Fourier (FFT) azimuthal anisotropy ratio and radial power distribution.
  - Global Laplacian noise variance.
  - Provisional Ensemble ($T = 1.20, \rho = 0.68$).
- **Associated Module: Generator Attribution (Multi-Tier Evidence):**
  - Identifies target families: `Midjourney`, `Stable Diffusion` (including `ComfyUI` and `Automatic1111`), `DALL-E` ($2/3$), `FLUX.1`, `Adobe Firefly`, and `UNKNOWN / GENERIC`.
  - Evidence Tiers:
    1. *Direct Provenance Evidence:* Cryptographically signed C2PA manifests.
    2. *Metadata-Based Clues:* PNG text chunks, software tags, prompt parameters.
    3. *Statistical Model Predictions:* Neural feature correlations.
    4. *Heuristic Indicators:* Canonical resolution buckets, aspect ratios, Fourier lattice harmonics.
  - **Fail-Safe:** If metadata is absent and heuristics are ambiguous, emits `primary_generator = "UNKNOWN"` with confidence $0.0$. Never claims 100% accuracy.

### 2.2 Dimension B: Forensic Manipulation Analysis Engine

Evaluates whether an image exhibits localized physical or compression anomalies indicative of post-capture tampering, compositing, or inpainting.

- **Classifications:**
  - `SUSPECTED_INPAINTING`: Localized cluster of high compression error and noise variance discontinuity embedded within a uniform background.
  - `SUSPECTED_SPLICING`: Sharp inter-quadrant noise variance and color covariance discrepancy, indicating composite elements from disparate source images.
  - `SUSPECTED_RETOUCHING`: Minor localized compression variances without sharp boundary discontinuities.
  - `NO_MANIPULATION_EVIDENCE_DETECTED`: Consistent compression decay and uniform spatial noise variance across all quadrants.
  - `INSUFFICIENT_EVIDENCE`: Uncompressed image format (PNG/BMP without JPEG history), resolution below threshold ($<64 \times 64$), or severe multi-pass compression ($Q < 50$) destroying diagnostic residual signals.

- **Forensic Evidence & Localization Schema (`ManipulationFinding`):**
  Every manipulation finding must populate the following structured fields:
  ```python
  class ManipulationFinding(BaseModel):
      classification: str  # SUSPECTED_INPAINTING, SUSPECTED_SPLICING, etc.
      observed_signal: str  # e.g., "Elevated 16x16 macro-block ELA variance in quadrant (Q2)"
      supporting_indicators: list[str]  # e.g., ["Noise residual variance gradient delta = 4.2x", "RGB cross-channel covariance shift"]
      region_localization: Optional[dict] = None  # e.g., {"quadrant": "Q2", "bounding_box": [ymin, xmin, ymax, xmax], "anomalous_block_count": 14}
      evidence_strength: str  # STRONG, MODERATE, WEAK, INCONCLUSIVE
      finding_type: str  # HEURISTIC vs MODEL_SUPPORTED
      limitations: list[str]  # e.g., ["ELA alone does not prove manipulation", "High-contrast natural edges may cause localized ELA elevation"]
      confidence_score: float  # Bounded [0.0, 1.0]
  ```

- **Non-Conclusive Disclaimer Requirement:** ELA and noise residuals alone must **never** be presented as proof of manipulation. High-contrast natural edges (hair against sky, text overlays) are damped using a high-frequency Sobel/Scharr edge mask before block variance aggregation.

---

## 3. Dataset & Empirical Calibration Validation Specification

To replace the provisional parameters ($T = 1.20, \rho = 0.68$) with scientifically certified values, the following calibration protocol is documented:

### 3.1 Proposed Dataset Sources & Licensing

| Dataset | Source / Reference | License & Permitted Use | Modality / Role | Target Image Count |
| :--- | :--- | :--- | :--- | :---: |
| **RAISE-1k** | Dang-Nguyen et al. (ACM MM 2015)<br>`http://vel光.isti.cnr.it/RAISE/` | Research & Non-Commercial Open Access | Authentic Uncompressed RAW Camera Captures | 1,000 images (3 primary camera makes: Nikon, Canon, Sony) |
| **ImageNet-1k (Val)** | Russakovsky et al. (IJCV 2015) | Academic / Research Use | Diverse Real-World Natural Photography | 1,000 images (balanced categories: animals, objects, scenes) |
| **GenImage** | Zhu et al. (NeurIPS 2023) | MIT / Research Open Access | Multi-Generator Synthetic (SD v1.4, SD v1.5, Midjourney, GLIDE, VQDM) | 1,000 images (paired with ImageNet classes) |
| **Synthbuster** | Bammey (IEEE WIFS 2023) | CC BY-NC-SA 4.0 | State-of-the-art Generative Models (DALL-E 2, DALL-E 3, SDXL, Midjourney v5, Firefly) | 1,000 images |
| **Inpainting & Splicing Benchmark (CASIA v2 / NIST)** | Dong et al. (CASIA v2) / NIST MFC | Research Use Only | Authentic vs Spliced vs Inpainted Tampered Images | 500 manipulated images + 500 authentic baselines |

### 3.2 Dataset Integrity, Class Balance & Transformations
- **Class Balance:** Exactly 50% authentic (RAISE + ImageNet) and 50% synthetic/manipulated (GenImage + Synthbuster + CASIA).
- **Generator Coverage:** Midjourney (v4, v5, v6), Stable Diffusion (v1.5, SDXL, ComfyUI), DALL-E (2, 3), FLUX.1, Adobe Firefly, and legacy GANs (StyleGAN2).
- **Perturbations & Compression Variations:**
  - Uncompressed baseline (TIFF / PNG).
  - JPEG recompression across 4 quality factors: $Q \in \{95, 85, 70, 50\}$.
  - Resizing transforms: Bicubic downsampling to $\{1024, 512, 256\}$ pixels.
  - Mild Gaussian blur ($\sigma \in \{0.5, 1.0\}$) and additive Gaussian sensor noise ($\sigma = 2.0$).
- **Partitioning & Leakage Prevention:**
  - **Split:** 60% Training / Calibration, 20% Validation, 20% Held-Out Independent Test.
  - **Zero Leakage:** SHA-256 hash deduplication; prompt semantic clustering isolation (no prompts in test appear in train); strict camera sensor separation (no cameras in test appear in train).

### 3.3 Calibration Evaluation Methodology
- **Optimization:** Grid-search optimization and isotonic regression / Platt scaling on the validation set to fit temperature $T$ and covariance penalty $\rho$.
- **Evaluation on Independent Test Split:**
  - **Expected Calibration Error (ECE):**
    $$\text{ECE} = \sum_{m=1}^{M} \frac{|B_m|}{N} \left| \text{acc}(B_m) - \text{conf}(B_m) \right| \quad (\text{Target: } \text{ECE} < 0.05 \text{ across } 10 \text{ bins})$$
  - **Brier Score:** Mean squared error between probability and ground truth (Target: $<0.08$).
  - **Reliability Diagrams:** Verification of monotonic alignment between confidence bins and true accuracy.
- **Current Status:** Until this multi-thousand image empirical validation benchmark is executed on target infrastructure, $T = 1.20$ and $\rho = 0.68$ remain documented as **provisional heuristic baselines**.

---

## 4. Exact File Inventory & Architectural Safeguards

### 4.1 Files to Create (New Modules)

1. **`backend/app/ml/image/generator_attribution.py`**
   - **Purpose:** Identifies likely generator families without overclaiming precision.
   - **Supported Target Families:** `Midjourney`, `Stable Diffusion` (`ComfyUI`, `Automatic1111`), `DALL-E` ($2/3$), `FLUX.1`, `Adobe Firefly`, `UNKNOWN / GENERIC`.
   - **Four-Tier Evidence Structure:** Direct Provenance, Metadata Clues, Statistical Predictions, Heuristic Indicators.
   - **Exports:** `attribute_generator(image: Image.Image, raw_bytes: bytes, fft_metrics: dict) -> GeneratorAttributionResult`.

2. **`backend/app/ml/image/manipulation.py`**
   - **Purpose:** Analyzes compression and noise anomalies to classify image manipulation into the five allowed states:
     `SUSPECTED_INPAINTING`, `SUSPECTED_SPLICING`, `SUSPECTED_RETOUCHING`, `NO_MANIPULATION_EVIDENCE_DETECTED`, `INSUFFICIENT_EVIDENCE`.
   - **Features:** $16 \times 16$ block ELA variance, high-frequency edge-mask damping, spatial noise variance gradients, structured region localization dictionary.
   - **Exports:** `detect_manipulation(image: Image.Image, raw_bytes: bytes, ela_metrics: dict, noise_metrics: dict) -> ManipulationResult`.

### 4.2 Files to Modify (Carefully Scoped Refactoring)

1. **`backend/app/ml/image/detector.py`**
   - Standardize `SwinImageDetector` and `VitImageDetector` to expose `raw_output` (`logits`, `raw_probs`, `input_dimensions`, `device`).
   - Integrate `generator_attribution` and `manipulation` into `analyze_image_bytes()`.
   - **CRITICAL BACKWARD COMPATIBILITY INVARIANT:**
     ```python
     def classify_image(self, image: Image.Image) -> tuple[float, float, float]:
         """
         Legacy/screening interface preserved strictly for Phase 3 video frame screening.
         Returns: (ai_probability, human_probability, raw_score)
         """
     ```
     This method's signature, parameter types, and return tuple will remain **completely untouched**.

2. **`backend/app/ml/image/ensemble.py`**
   - Label calibration parameters ($T = 1.20, \rho = 0.68$) as provisional heuristic baselines.
   - Format `ModelRegistryEntry` records.
   - Implement `generate_disagreement_narrative()` and `identify_uncertainty_drivers()`.
   - Implement categorical `evidence_strength` assignment (`STRONG`, `MODERATE`, `WEAK`, `INCONCLUSIVE`).
   - Ensure manipulation findings **never** alter synthetic probability.

3. **`backend/app/schemas/image_analysis.py`**
   - Define `GeneratorAttribution`, `ManipulationFinding`, and `ModelRegistryEntry`.
   - Extend `ImageAnalysisResponse` with distinct top-level objects:
     - `synthetic_detection`: Classification (`LIKELY_SYNTHETIC`, `LIKELY_HUMAN`, `INCONCLUSIVE`), probabilities, evidence strength.
     - `manipulation_analysis`: Full `ManipulationFinding` object.
     - `generator_attribution`: Full `GeneratorAttribution` object.
     - `model_registry`: List of `ModelRegistryEntry`.
     - `disagreement_analysis`: Written narrative.
     - `uncertainty_drivers`: List of active risk flags.
   - Maintain top-level `classification` (aliasing `synthetic_detection.classification`) for backward compatibility with existing tests and API consumers.
   - Enforce `model_config = ConfigDict(extra="ignore")`.

4. **`backend/app/api/v1/endpoints/image.py`**
   - In `/analyze`, serialize all extended telemetry into the existing `record.ensemble_json` SQLite text column.
   - In `/analyses` and `/analyses/{id}`, unpack and return both synthetic detection and manipulation analysis fields.

5. **`backend/app/services/pdf_generator.py`**
   - Update `generate_image_analysis_pdf()` to clearly present two distinct visual sections:
     - **Section A: Synthetic Media Determination** (Classification, probability gauge, generator attribution, model consensus table).
     - **Section B: Digital Manipulation & Tampering Analysis** (Manipulation classification, observed signal, supporting indicators, localization coordinates, limitations).
     - Preserves SHA-256 hash, metadata, dual heatmaps, and epistemic disclaimers.

6. **`frontend/src/lib/api.ts`**
   - Extend TypeScript interfaces to mirror backend schemas with optional fields.

7. **`frontend/src/app/dashboard/image/page.tsx`**
   - Visual redesign separating the two dimensions into dedicated cards:
     - **Card 1: Synthetic Origin Assessment** (`LIKELY_SYNTHETIC`, `LIKELY_HUMAN`, `INCONCLUSIVE`, attribution meter).
     - **Card 2: Manipulation & Tampering Analysis** (5-state badge, observed signal, localization drawer, limitations warning).
     - **Card 3: Multi-Detector Consensus & Disagreement Hub** (raw logits, dims, device, narrative).
     - Preserves black-and-gold visual theme, responsive layout, and heatmap switcher.

8. **`backend/tests/test_image_analysis.py`**
   - Expand test suite from 27 to 35+ test scenarios.

---

## 5. Database Backwards Compatibility Strategy

- **Zero Schema Migrations:** No changes to SQLite `image_analyses` table schema. No `ALTER TABLE` statements.
- **Serialization in `ensemble_json`:** All Phase 2 telemetry is nested within the existing `ensemble_json` column.
- **Graceful Deserialization:** Historical records deserializing `ensemble_json` default missing fields to `None`, preserving complete historical case readability.

---

## 6. Performance Targets & Instrumentation

All performance numbers are **engineering design targets**, not guarantees.

| Metric | Target | Measurement & Instrumentation Methodology |
| :--- | :---: | :--- |
| **Pipeline Latency (CPU)** | $< 200$ ms total | Instrumented via `time.perf_counter()` from byte receipt to response serialization. |
| **Attribution Latency** | $< 10$ ms | Instrumented via `time.perf_counter()` inside `attribute_generator()`. |
| **Manipulation Latency** | $< 25$ ms | Instrumented via `time.perf_counter()` inside `detect_manipulation()`. |
| **Additional Memory Overhead** | $< 20$ MB | Instrumented via `tracemalloc` peak allocation and `psutil.Process().memory_info().rss`. |
| **VRAM Consumption** | $0$ MB added | Verified via `torch.cuda.memory_allocated()` (remains 0 on CPU). |

---

## 7. Execution Sequence (Post-Approval Only)

- **Step 1:** Create `backend/app/ml/image/generator_attribution.py`.
- **Step 2:** Create `backend/app/ml/image/manipulation.py`.
- **Step 3:** Update `backend/app/ml/image/detector.py` (model registry, raw telemetry; freeze `classify_image`).
- **Step 4:** Update `backend/app/ml/image/ensemble.py` (provisional calibration notation, disagreement narrative, decouple manipulation).
- **Step 5:** Update `backend/app/schemas/image_analysis.py` (two-dimension schema extensions with `ConfigDict(extra="ignore")`).
- **Step 6:** Update `backend/app/api/v1/endpoints/image.py` (database persistence and unpacking).
- **Step 7:** Update `backend/app/services/pdf_generator.py` (two-section forensic PDF layout).
- **Step 8:** Update `frontend/src/lib/api.ts` & `frontend/src/app/dashboard/image/page.tsx` (two-dimension UI layout).
- **Step 9:** Expand and execute `backend/tests/test_image_analysis.py` (35+ tests) with active latency/memory instrumentation.
- **Step 10:** Execute full backend regression suite (140+ tests across text, image, video, auth, cloud, PDF).
- **Step 11:** Execute frontend TypeScript validation (`npx tsc --noEmit`) and production build (`npm run build`).
- **Step 12:** Compile `docs/PHASE_2_IMPLEMENTATION_REPORT.md` and present completion audit.
