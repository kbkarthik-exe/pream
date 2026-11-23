# AICF Phase 2 — Multi-Model AI Image Forensics Engine: Audit & Implementation Plan

**Project:** `C:\Users\acer\IMAGE`  
**Date:** 2026-11-18  
**Status:** **PROPOSED — AWAITING USER APPROVAL PRIOR TO SOURCE CODE MODIFICATION**  
**Git Checkpoint / Safe Baseline Backup:** `backups\phase2_baseline_checkpoint` created.  

---

## 1. Audit of Existing Image Forensics Implementation

### 1.1 Architectural Overview
The existing image forensics engine (`backend/app/ml/image/`) is built on a modular design combining deep representation classification with deterministic signal processing:

- **Primary Deep Learning Backbone (`SwinImageDetector`):** Shifted Window Hierarchical Vision Transformer (`umm-maybe/AI-image-detector`), operating on $224 \times 224$ patches to identify synthesis texture artifacts.
- **Secondary Deep Learning Backbone (`VitImageDetector`):** Vision Transformer with global multi-head self-attention (`capcheck/ai-image-detection`), providing global semantic and structural consistency verification.
- **Deterministic Signal Processing (`features.py`):**
  - **2D Fourier Spectral Analysis (FFT):** 2D Fast Fourier Transform on grayscale luminance, measuring radial low/mid/high frequency power ratios and 8-octant azimuthal anisotropy.
  - **Laplacian Noise Residual Profiler:** Spatial filtering evaluating sensor noise variance and RGB cross-channel correlation.
  - **Metadata & Provenance:** EXIF extraction, camera hardware tags, PNG metadata (Stable Diffusion, ComfyUI, Midjourney parameters), and byte-level C2PA Content Credentials signature scanning.
- **Forensic Heatmaps (`heatmap.py`):**
  - Error Level Analysis (ELA) with $16 \times 16$ block discontinuity scoring.
  - Laplacian spatial noise residual heatmap.
  - Thermal colormap generation emitting base64 PNG data URLs.
- **Ensemble Aggregator (`ensemble.py`):**
  - Temperature scaling ($T = 1.20$) to moderate uncalibrated neural confidence.
  - Empirical covariance penalty ($\rho = 0.68$) to discount correlated vision transformer agreement.
  - Orthogonal physical/spectral prior adjustments.
  - Pre-flight commit memory and disk space verification (`check_system_resources`).
- **Core Video Dependency (`classify_image` in `detector.py`):**
  - OpenCV video frame screening in Phase 3 imports `image_detector.classify_image()` directly.
  - **Strict Preservation Requirement:** `classify_image(image)` must maintain exact parameter types and return shape (`ai_probability`, `human_probability`, `raw_score`).

### 1.2 Schema and Database Storage Baseline
- **Database Model (`ImageAnalysisRecord`):** Contains fixed columns for image dimensions, format, hashes, telemetry, and two flexible text columns: `ensemble_json` and `heatmap_json`.
- **API Response (`ImageAnalysisResponse`):** Serializes `classification`, `confidence_score`, `ai_probability`, `human_probability`, `raw_score`, deterministic metrics, `provenance`, `evidence`, `detector_scores`, `ensemble`, `heatmap`, `limitations`.
- **Database Non-Breaking Strategy:** By serializing new forensic telemetry (generator attribution, manipulation findings, uncertainty drivers, disagreement analysis) inside `ensemble_json`, we extend backend capabilities with **zero SQLite database alter migrations** and zero breakage to existing history records.

---

## 2. Research & Documentation of Candidate Models & Hive AI Workflow

### 2.1 Publicly Observable Hive AI Image Capabilities
Based on research into public documentation and observable features:
1. **Two-Stage Analysis:** Distinguishes between globally AI-generated imagery and locally manipulated/edited photographs.
2. **Generator Attribution:** Classifies probable generative families (Midjourney, Stable Diffusion, DALL-E, FLUX, Adobe Firefly) based on distinct latent space upscaler artifacts and metadata signatures.
3. **Manipulation Localization:** Detects inpainting boundaries, copy-move cloning, and facial deepfakes.
4. **Structured Confidence:** Reports calibrated percentages rather than binary certainties, with visual heatmaps highlighting anomalous regions.

### 2.2 Model Candidates Evaluation Matrix

| Model Family / Architecture | Source / Reference | License | Hardware Req | Inference (CPU) | Strengths | Known Weaknesses / Limitations |
| :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| **Swin-B ViT (`umm-maybe/AI-image-detector`)** | Hugging Face / Swin Transformer | MIT | $\ge 1.0$ GB RAM | ~90ms | Multi-scale patch analysis, trained on Midjourney/SD/DALL-E | Sensitive to heavy JPEG recompression; correlated with ViT |
| **ViT-Base (`capcheck/ai-image-detection`)** | Hugging Face / ViT-Base | Apache-2.0 | $\ge 0.8$ GB RAM | ~110ms | Global semantic composition and structural coherence | Lower sensitivity to micro-boundary blending anomalies |
| **CNNDetection (Wang et al., CVPR 2020)** | ResNet-50 / ProGAN baseline | Academic / Research | $\ge 0.5$ GB RAM | ~60ms | Fast CNN baseline for GAN artifact detection | Degrades on modern latent diffusion models (SDXL, FLUX) |
| **UnivFD (Ojha et al., CVPR 2023)** | Frozen CLIP ViT-L/14 + MLP | MIT | $\ge 1.8$ GB RAM | ~180ms | High cross-generator generalization | High memory footprint; large model download (>1.2 GB) |
| **Deterministic Spectral & ELA Profiler** | Mathematical / Peer-Reviewed | Proprietary / Native | Minimal (<10 MB) | <10ms | Air-gapped, zero external download, mathematically explainable | Heuristic alone cannot prove AI authorship |
| **Rule-Based & Latent Signature Attribution Engine** | Native AICF Implementation | Native Open Source | Minimal (<5 MB) | <5ms | Detects generation parameters, grid spikes, aspect ratios, EXIF | Cannot attribute models with stripped metadata or non-standard upscalers |
| **Forensic Manipulation Analyzer** | Block-level ELA + Laplacian Noise Gradients | Native Open Source | Minimal (<15 MB) | <15ms | Localizes inpainting seams and copy-move discontinuities | High-contrast real edges can create false ELA peaks |

### 2.3 Selected Phase 2 Architecture (Local Primacy & Resilient Multi-Model)
To maintain local air-gapped execution, low memory overhead, and instant responsiveness without multi-gigabyte unverified downloads:
1. **Primary Synthesis Backbone:** Swin-B Hierarchical Vision Transformer (`umm-maybe/AI-image-detector`).
2. **Secondary Synthesis Backbone:** ViT-Base Vision Transformer (`capcheck/ai-image-detection`) with safe pre-flight resource checks.
3. **Generator Attribution Engine:** Multi-factor attribution engine analyzing frequency grid harmonics, aspect ratio defaults, latent upscaler signatures, and embedded metadata (Midjourney, Stable Diffusion, DALL-E, FLUX, Adobe Firefly).
4. **Image Manipulation & Splicing Detector:** Block-level ELA discontinuity analysis combined with local noise variance gradients to identify localized inpainting, splicing, and retouching.
5. **Physical & Spectral Forensics:** 2D Fourier (FFT) octant anisotropy, Laplacian spatial noise residuals, and JPEG quantization metrics.
6. **Model Registry & Telemetry Standard:** Every detector reports identifier, version, model type, input dimensions, raw output (`logits`, `raw_probs`), device, latency, and status.

---

## 3. Implementation Plan (10-Step Controlled Execution)

### Step 1: Baseline Checkpoint (Completed)
- Safe backup created at `backups\phase2_baseline_checkpoint\`.

### Step 2: Implementation of Generator Attribution Engine (`generator_attribution.py`)
- Create `backend/app/ml/image/generator_attribution.py`.
- Evaluates:
  - Provenance prompt markers and software tags (`Midjourney`, `ComfyUI`, `Automatic1111`, `DALL-E`, `Adobe Firefly`, `FLUX.1`).
  - High-frequency grid harmonic patterns in 2D FFT spectrum (characteristic of latent upscalers).
  - Default canvas aspect ratio ratios and resolution signatures.
- Outputs structured `GeneratorAttribution` object with detected signatures and confidence.

### Step 3: Implementation of Manipulation & Splicing Detector (`manipulation.py`)
- Create `backend/app/ml/image/manipulation.py`.
- Evaluates:
  - ELA block-level compression discontinuity across $16 \times 16$ blocks.
  - Spatial noise variance gradients between background and foreground regions.
  - Color channel covariance shifts indicative of composite elements.
- Classifies: `Splicing`, `Generative Inpainting`, `Local Retouching`, `None Detected`.

### Step 4: Model Registry & Raw Output Telemetry (`detector.py`)
- Update `SwinImageDetector` and `VitImageDetector` to return `raw_output` containing `logits`, `raw_probs`, `input_dimensions`, and compute `device`.
- Integrate `generator_attribution` and `manipulation` modules into `ImageForensicsDetector.analyze_image_bytes()`.
- Preserve `classify_image()` signature and functionality for video frame processing.

### Step 5: Calibrated Ensemble & Uncertainty Handling (`ensemble.py`)
- Incorporate generator attribution and manipulation findings into consensus decision.
- Compute model agreement score and generate `disagreement_analysis` narrative.
- Surface categorical `evidence_strength` (`STRONG`, `MODERATE`, `WEAK`, `INCONCLUSIVE`).
- Log explicit `uncertainty_drivers` (e.g. conflicting models, high compression, missing EXIF, ambiguous resolution).

### Step 6: Schema Evolution & API Endpoint Integration (`schemas/` & `endpoints/image.py`)
- Update `backend/app/schemas/image_analysis.py`:
  - Add `GeneratorAttribution`, `ManipulationFinding`, and `ModelRegistryEntry`.
  - Extend `ImageAnalysisResponse` with new forensic fields using `model_config = ConfigDict(extra="ignore")`.
- Update `backend/app/api/v1/endpoints/image.py`:
  - Serialize extended telemetry into `record.ensemble_json`.
  - Return all new fields in API responses.

### Step 7: Enhanced Forensic PDF Generation (`services/pdf_generator.py`)
- In `generate_image_analysis_pdf()`:
  - Add Generator Classification card.
  - Add Manipulation & Inpainting Findings table.
  - Add Inter-Model Agreement & Disagreement analysis table.
  - Embed ELA and Noise Residual heatmaps with scale legends.
  - Preserve black-and-gold aesthetic, SHA-256 hashes, and epistemic disclaimers.

### Step 8: Frontend Dashboard Upgrade (`frontend/src/app/dashboard/image/page.tsx`)
- Update `frontend/src/lib/api.ts` with TypeScript interfaces.
- Enhance `/dashboard/image`:
  - Add Generator Attribution card.
  - Add Manipulation & Splicing Findings card.
  - Add Model Agreement / Disagreement narrative and Uncertainty Drivers box.
  - Add raw output telemetry badges to Multi-Detector Consensus Hub.
  - Preserve interactive heatmap switcher (Original, ELA, Noise Residual) and case saving.

### Step 9: Test Suite Expansion & Validation (`test_image_analysis.py`)
- Expand `backend/tests/test_image_analysis.py` to 35+ test scenarios:
  - Valid JPEG, PNG, WebP.
  - Empty, corrupted, unsupported, oversized files.
  - Low-resolution inconclusive gate (<32x32).
  - Generator attribution unit tests.
  - Manipulation detection unit tests.
  - Raw output telemetry exposure.
  - Model disagreement & uncertainty degradation.
  - Cross-tenant security isolation.
  - PDF generation with new tables.
  - Held-out benchmark dataset evaluation reporting Precision, Recall, F1, FPR, FNR.

### Step 10: Full Regression Verification & Sign-Off
- Run expanded image test suite.
- Run text regression suite (21 tests).
- Run video regression suite (23 tests).
- Run full backend suite (140+ tests).
- Run frontend ESLint, TypeScript check, and Next.js production build.
- Create `docs/PHASE_2_IMPLEMENTATION_REPORT.md`.

---

## 4. Verification Checkpoint & Request for Approval

**STRICT COMPLIANCE:** No source code files have been modified yet. Safe baseline backup is secured.

Please review this audit and implementation plan and grant your approval to proceed to **Step 2 (Implementation of Generator Attribution Engine)**.

