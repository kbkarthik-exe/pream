# AICF Phase 2 — Multi-Model AI Image Forensics Engine: Hive AI Feature Gap Analysis
*(Technical Safety & Scientific Rigor Revision)*

**Project:** `C:\Users\acer\IMAGE`  
**Date:** 2026-11-18  
**Status:** **TECHNICAL SAFETY REVIEW COMPLETED — PROVISIONAL DESIGN AWAITING USER APPROVAL**  
**Document Target:** `docs/PHASE_2_GAP_ANALYSIS.md`

---

## 1. Executive Summary

This gap analysis compares the existing AICF Phase 1 image forensics engine against the publicly observable features, workflows, and forensic capabilities of Hive AI.

### Guiding Forensic Principles for Phase 2:
- **No Overstated Claims:** Hive AI operates proprietary multi-task convolutional and transformer heads trained on millions of internal images. AICF does not claim to duplicate Hive AI's private models or achieve 100% accuracy.
- **Evidence-Tiered Attribution:** Generator attribution must clearly separate direct cryptographic provenance, metadata clues, and heuristic inferences, and must support `UNKNOWN` and `INCONCLUSIVE`.
- **Realistic Manipulation Forensics:** Error Level Analysis (ELA) and noise residuals must be recognized as heuristic anomaly indicators, not definitive proof of manipulation. A structured 6-tier classification taxonomy is mandated.
- **Provisional Ensemble Calibration:** Ensemble parameters ($T = 1.20, \rho = 0.68$) are designated as provisional heuristic baselines pending formal empirical calibration on benchmark datasets.

---

## 2. Feature-by-Feature Parity & Gap Matrix

| Feature / Forensic Dimension | Hive AI Publicly Observable Capability | AICF Current Status (Phase 1 Baseline) | Parity Status | Phase 2 Implementation Priority |
| :--- | :--- | :--- | :---: | :---: |
| **Synthetic vs. Human Classification** | Outputs overall score $[0.0, 1.0]$ with categorical verdict (`Yes` / `No` / `Possible`). | Outputs `ai_probability`, `human_probability`, and categorical classification (`AI_GENERATED`, `HUMAN_ORIGINAL`, `INCONCLUSIVE`). | **Full Parity** | Maintain baseline; mark calibration as provisional. |
| **Generator Family Attribution** | Predicts probability across generative engines: Midjourney, Stable Diffusion, DALL-E 2/3, FLUX, Adobe Firefly, Imagen. | Currently outputs a single aggregate AI probability score across models with no generator breakdown. | **GAP** | **PRIORITY 1** (Multi-Tier Evidence Engine; must support `UNKNOWN`). |
| **Image Manipulation Detection** | Detects local digital alterations, inpainting seams, facial swaps, and splicing vs. full synthetic generation. | Computes overall ELA block discontinuity score, but does not categorize into distinct forensic manipulation states. | **GAP** | **PRIORITY 1** (6-tier taxonomy; must support `INSUFFICIENT_EVIDENCE`). |
| **Visual Anomaly Heatmaps** | Generates bounding boxes or thermal anomaly maps highlighting suspicious regions. | Generates dual forensic heatmaps: Error Level Analysis (ELA) with $16 \times 16$ blocks and Laplacian Noise Residual thermal maps. | **Parity / Exceeds** | **PRIORITY 2** (Add scale legends and edge-mask guidance). |
| **Physical & Signal Forensics** | Black-box deep neural network scoring; does not expose underlying frequency or physical sensor metrics. | Fully transparent deterministic signal processing: 2D Fourier (FFT) 8-octant spectral anisotropy, radial power bands, noise variance, RGB channel covariance. | **Exceeds Hive** (Scientific Explainability) | Maintain baseline; clearly document heuristic bounds. |
| **Provenance & Metadata Inspection** | Proprietary C2PA / watermark extraction (where supported). | Exhaustive EXIF extraction, camera hardware tags, generation prompt/parameter mining (PNG chunks), and C2PA byte manifest scanning. | **Parity / Exceeds** | Maintain baseline; distinguish direct vs metadata clues. |
| **Model Registry & Telemetry** | Monolithic API response with proprietary confidence scores. | Exposes individual detector scores, but lacks standardized raw telemetry (`logits`, `raw_probs`, `input_dimensions`, `device`). | **GAP** | **PRIORITY 2** (Expose standardized raw telemetry). |
| **Disagreement & Uncertainty Narrative** | High-level risk score; limited explanation of internal model conflicts. | Mathematical temperature and covariance discounting, but lacks human-readable narrative explaining internal model discordance. | **GAP** | **PRIORITY 2** (Synthesize written consensus & uncertainty drivers). |
| **Auditability & Integrity Verification** | Standard JSON API response; no client-side verifiable cryptographic audit trail. | Computes SHA-256 integrity hash, multi-user tenant isolation, persistent case history, and forensic court-ready PDF generation. | **Exceeds Hive** | Maintain baseline. |
| **Data Privacy & Air-Gapped Deployment** | Cloud-only SaaS API; all media uploaded to third-party infrastructure. | 100% local inference, zero-cost, privacy-preserving, air-gapped capable, no telemetry leakage. | **Exceeds Hive** | Maintain baseline. |

---

## 3. Rigorous Analysis of Technical Gaps

### 3.1 Gap 1: Generator Family Attribution (Evidence-Tiered)
- **Forensic Problem:** Users need to understand which tool likely produced an image, but overclaiming attribution accuracy creates severe liability.
- **Evidence Hierarchy to Implement:**
  1. *Direct Provenance:* Signed C2PA manifests (e.g. Adobe Firefly, Leica).
  2. *Metadata Clues:* Software headers and prompt parameters (`Automatic1111`, `ComfyUI`, `Midjourney`, `DALL-E`).
  3. *Statistical Model Predictions:* Model feature correlation scores.
  4. *Heuristic Indicators:* Canonical dimensions (e.g., SDXL $1024 \times 1024$, $1152 \times 896$), aspect ratios ($16:9$, $4:5$), and Fourier lattice harmonics.
- **Mandatory Fail-Safe:** If metadata is absent or stripped and heuristics do not meet strict confidence thresholds, the engine must return:
  - `primary_generator`: `UNKNOWN`
  - `attribution_confidence`: `0.0`
  - `evidence_tier`: `NONE`

### 3.2 Gap 2: Separate Manipulation Classification (6-Tier Taxonomy)
- **Forensic Problem:** ELA and noise residuals highlight compression differences and spatial noise variances, but do not provide autonomous "proof" of tampering. Legitimate photographic textures (sharp silhouettes, text, clear skies) produce natural ELA variations.
- **Mandatory Six-Tier Classification Taxonomy:**
  1. `FULL_SYNTHESIS`: Global synthetic markers across all backbones; no localized seam detected.
  2. `LOCAL_INPAINTING`: Significant localized ELA and noise anomaly cluster surrounded by consistent camera background.
  3. `IMAGE_SPLICING`: Sharp inter-quadrant noise variance and channel covariance discordance.
  4. `RETOUCHING`: Minor localized compression variations without boundary discontinuities.
  5. `NO_MANIPULATION_EVIDENCE_DETECTED`: Consistent compression decay and uniform noise variance across all regions.
  6. `INSUFFICIENT_EVIDENCE`: Uncompressed image formats, low-resolution files, or multi-generation recompression destroying diagnostic signals.

### 3.3 Gap 3: Model Registry & Telemetry Standardization
- **Forensic Problem:** Forensic transparency requires that every active model exposes its raw uncalibrated tensor outputs alongside high-level probabilities.
- **Telemetry Specification:**
  - `model_id`: String (e.g., `swin-b-vit-forensics`, `vit-base-global`).
  - `version`: String.
  - `model_type`: Categorical (`TRANSFORMER_LOCAL`, `TRANSFORMER_GLOBAL`, `HEURISTIC_SIGNAL`).
  - `input_dimensions`: List of ints (e.g., `[3, 224, 224]`).
  - `raw_output`: Dict containing `logits`, `raw_probs`, and execution `device`.
  - `latency_ms`: Measured execution time in milliseconds.

### 3.4 Gap 4: Disagreement Narrative & Uncertainty Drivers
- **Forensic Problem:** When backbones disagree (e.g. Swin indicates AI, ViT indicates Human), users need clear explanations rather than opaque numeric compromises.
- **Reporting Enhancements:**
  - `disagreement_analysis`: Synthesized narrative explaining concordances and conflicts between deep learning and signal metrics.
  - `uncertainty_drivers`: Explicit list of forensic risk factors (e.g., `HIGH_JPEG_COMPRESSION`, `DISCORDANT_NEURAL_BACKBONES`, `STRIPPED_EXIF_METADATA`, `LOW_RESOLUTION_INPUT`).
  - `evidence_strength`: Categorical classification (`STRONG`, `MODERATE`, `WEAK`, `INCONCLUSIVE`).

---

## 4. Prioritization & Safety Matrix for Phase 2

| Priority | Deliverable Module | Safety Safeguards | Estimated Complexity |
| :---: | :--- | :--- | :---: |
| **P1** | **Generator Attribution Engine** (`generator_attribution.py`) | 4-tier evidence separation; mandatory `UNKNOWN` support; no 100% claims. | Low-Moderate |
| **P1** | **Manipulation & Inpainting Detector** (`manipulation.py`) | 6-tier taxonomy; edge-mask damping; mandatory `INSUFFICIENT_EVIDENCE` state. | Moderate |
| **P2** | **Model Registry & Telemetry Standard** (`detector.py`) | Uncalibrated logits, dims, device; strict backward compatibility for `classify_image()`. | Low |
| **P2** | **Disagreement Narrative & Uncertainty Drivers** (`ensemble.py`) | Provisional label on calibration parameters ($T=1.20, \rho=0.68$); explicit uncertainty logging. | Low-Moderate |
| **P3** | **Interactive Dashboard & PDF Report Upgrade** (Frontend & ReportLab) | Visual attribution meter with uncertainty tags; manipulation badges; forensic disclaimers. | Moderate |
