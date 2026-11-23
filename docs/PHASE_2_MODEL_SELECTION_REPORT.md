# AICF Phase 2 — Multi-Model AI Image Forensics Engine: Model Selection Report
*(Technical Safety & Scientific Rigor Revision)*

**Project:** `C:\Users\acer\IMAGE`  
**Date:** 2026-11-18  
**Status:** **TECHNICAL SAFETY REVIEW COMPLETED — PROVISIONAL DESIGN AWAITING USER APPROVAL**  
**Document Target:** `docs/PHASE_2_MODEL_SELECTION_REPORT.md`

---

## 1. Executive Summary & Epistemic Framework

Phase 2 of the AI Content Forensics (AICF) platform aims to advance our image detection engine into a multi-model forensic analysis framework inspired by the public capabilities of Hive AI.

### Core Scientific Principles & Non-Negotiables:
1. **No 100% Accuracy Claims:** In forensic image science, no detector, heuristic, or metadata parser can guarantee 100% accuracy across unconstrained real-world distribution shifts. All scores must be represented as probabilistic estimates with explicit error bars and limitations.
2. **Separation of Evidence Modalities:** A critical forensic distinction must be maintained between:
   - *Direct Provenance Evidence* (cryptographically signed C2PA assertions, tamper-evident hardware manifests).
   - *Metadata-Based Clues* (textual prompt chunks, EXIF software tags, encoder markers).
   - *Statistical Model Predictions* (neural network softmax probabilities, linear probe logits).
   - *Heuristic Indicators* (canonical aspect ratios, dimension matching, Fourier lattice harmonics).
3. **Mandatory Inconclusive & Unknown States:** When evidence is conflicting, degraded, or absent, the system must explicitly emit `UNKNOWN` for generator attribution and `INCONCLUSIVE` for authenticity determinations.
4. **Provisional Nature of Calibration Parameters:** The current temperature scaling ($T = 1.20$) and covariance penalty ($\rho = 0.68$) are **provisional heuristic baselines**. They are not yet certified as mathematically calibrated probabilities until validated against formal calibration metrics on multi-generator benchmark datasets.
5. **Performance Figures as Design Targets:** All latency and memory figures are **engineering targets**, not guarantees, and must be validated through active instrumentation (`time.perf_counter()`, `tracemalloc`, and `psutil`).

---

## 2. Comparative Evaluation Matrix of Candidate Models

| Model Family / Architecture | Reference & Official Repo | License | Pretrained Weights Availability | Training Dataset & Modalities | Hardware Requirements (Target CPU / VRAM / RAM) | Generalization Across Generators | Known Failure Modes & Limitations | Python 3.12 Compatibility | Integration Complexity in AICF |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Swin-B ViT (`umm-maybe/AI-image-detector`)** *(Existing Primary)* | Hugging Face Hub / Swin Transformer (Liu et al., ICCV 2021) | MIT | Immediate via HF Hub (~350 MB SafeTensors) | Midjourney, Stable Diffusion v1.4/v1.5, DALL-E 2, GANs, ImageNet Real | Target CPU: ~90ms<br>Target RAM: ~1.0 GB<br>VRAM: ~1.5 GB | High on diffusion and GAN synthetic textures due to shifted-window local receptive field. | Heavy JPEG recompression ($Q < 65$), extreme downsampling, heavy film grain injection. | Native (PyTorch 2.x, Transformers 4.49+) | **Zero** (Already verified in production baseline). |
| **ViT-Base (`capcheck/ai-image-detection`)** *(Existing Secondary)* | Hugging Face Hub / ViT (Dosovitskiy et al., ICLR 2021) | Apache-2.0 | Immediate via HF Hub (~340 MB SafeTensors) | Multi-generator synthetic dataset (SDXL, MJ v5, Photorealistic GANs) | Target CPU: ~110ms<br>Target RAM: ~850 MB<br>VRAM: ~1.2 GB | High global semantic and structural composition coherence verification. | Micro-boundary seam blending; correlated false positives with Swin on artistic photography. | Native (PyTorch 2.x, Transformers 4.49+) | **Zero** (Already integrated with pre-flight memory gate). |
| **UnivFD (Universal Fake Detector)** | Ojha, Li, Lee (CVPR 2023)<br>`PeterWang512/UnivFD` / `liyuheng98/UniversalFakeDetect` | MIT | GitHub / HF Hub (~1.2 GB to ~1.8 GB) | Frozen CLIP ViT-L/14 + Linear Probe trained strictly on ProGAN (20 classes) | Target CPU: ~220ms<br>Target RAM: ~2.2 GB<br>VRAM: ~3.0 GB | High zero-shot transfer across 12+ diffusion models in academic benchmarks. | High memory footprint; large model download (>1.2 GB); slow cold start on CPU; degraded on low-resolution inputs (<128px). | Compatible via `open_clip_torch` or `transformers` | **Moderate-High** (Heavy download, increases bundle size by 1.5GB; RAM spikes on modest hardware). |
| **CNNDetection** | Wang, Wang, Zhang, Owens, Efros (CVPR 2020)<br>`PeterWang512/CNNDetection` | BSD-2-Clause / Academic | Available via GitHub (~95 MB PyTorch `.pth`) | ResNet-50 trained on ProGAN with blur + JPEG data augmentation | Target CPU: ~50ms<br>Target RAM: ~450 MB<br>VRAM: ~800 MB | High on GANs (StyleGAN, BigGAN, CycleGAN). | **Fails on modern latent diffusion models** (SDXL, FLUX.1, Midjourney v6) because it relies on transposed-convolution checkerboard artifacts absent in diffusion. | Compatible via `torchvision.models.resnet50` | **Low** (Simple ResNet wrapper), but **poor forensic return on investment** due to diffusion blindspot. |
| **DIRE (Diffusion Reconstruction Error)** | Wang, Bao, Zhou, Wang, Li (ICCV 2023)<br>`ZhendongWang6/DIRE` | Apache-2.0 | Multi-stage (Requires guided-diffusion / SD v1.4 UNet + classifier, ~4.5 GB) | Images inverted via DDIM inversion, classified on $\|x - \hat{x}\|$ residual error maps | Target CPU: **30s–90s**<br>VRAM: $\ge 6.0$ GB<br>RAM: $\ge 8.0$ GB | High theoretical accuracy on diffusion architectures sharing the inversion model family. | **Completely infeasible for local CPU execution.** Requires 20-50 DDIM inversion steps per image; CPU latency unviable; massive disk requirement. | High friction with modern diffusers/torch versions | **Extreme** (Incompatible with responsive local interactive user experience). |
| **Latent Signature & Provenance Attribution Engine** *(Proposed)* | AICF Native Engineering (Metadata, Resolution, Aspect Ratio, Fourier Harmonics) | AICF Open Source | Native Code (<15 KB, No external weight download) | Multi-tier rules (Direct Provenance, Metadata Clues, Heuristic Indicators) | Target CPU: **<5ms**<br>Target RAM: **<5 MB**<br>VRAM: 0 MB | Distinguishes known tool signatures when metadata or canonical geometry is present. | Stripped metadata leaves only weak heuristics; cannot identify custom fine-tunes. Emits `UNKNOWN` when indeterminate. | 100% Native Python 3.12, NumPy, Pillow | **Low** (Modular, clean, instantaneous, air-gapped). |
| **Block-Discontinuity Manipulation Analyzer** *(Proposed)* | AICF Native Engineering (ELA Block Variance + Local Noise Gradients) | AICF Open Source | Native Code (<20 KB, No external weight download) | Forensic error level analysis (Krawetz 2007) + spatial noise gradients (Farid 2009) | Target CPU: **<15ms**<br>Target RAM: **<15 MB**<br>VRAM: 0 MB | Identifies compression and noise variance anomalies between image regions. | ELA alone does NOT prove manipulation. Sensitive to compression history, uniform textures, and sharp natural edges. Emits `INSUFFICIENT_EVIDENCE` when indeterminate. | 100% Native Python 3.12, NumPy, Pillow, SciPy | **Low** (Clean extension of existing forensic signal modules). |

---

## 3. In-Depth Scientific Review of Candidate Approaches

### 3.1 Generator Attribution: Feasibility, Modalities & Limitations
Can metadata, image dimensions, aspect ratios, and Fourier signatures genuinely identify individual generative models?

#### The Scientific Reality:
- **Direct Provenance (Highest Confidence):** Cryptographically signed C2PA / CAI manifests containing valid assertions from Adobe Firefly, Microsoft Designer, or Leica camera hardware offer tamper-evident provenance. However, social media platforms (Twitter/X, Instagram, WhatsApp) strip these manifests upon upload.
- **Metadata Clues (High Confidence When Present, Easily Forged or Stripped):** PNG text chunks (`parameters`, `workflow`, `prompt`) frequently contain unambiguous markers from `Automatic1111`, `ComfyUI`, `InvokeAI`, `NovelAI`, or `Midjourney`. While highly informative, metadata is trivially stripped by web re-encoding or can be spoofed by a determined adversary.
- **Heuristic Indicators (Moderate-to-Low Confidence):**
  - *Canonical Dimensions & Aspect Ratios:* SDXL defaults to canonical buckets ($1024 \times 1024$, $1152 \times 896$, $896 \times 1152$, $1216 \times 832$). Midjourney frequently outputs distinct aspect ratios ($16:9$, $4:5$, $2:3$, $1:1$ at $1024 \times 1024$ or $2048 \times 2048$ with specific v5/v6 upscalers). However, authentic camera crops can coincidentally match these dimensions.
  - *Fourier Grid Harmonics:* Transposed convolutions and latent VAE decoders (e.g. SD VAE $8\times$ downsampling) introduce subtle periodic lattice harmonics visible as spikes in the 2D FFT power spectrum. However, common bicubic resizing, sharpening, and JPEG grid compression ($8 \times 8$ DCT blocks) also induce periodic frequency artifacts.
- **Architectural Policy:**
  - Generator identification must never be treated as a single binary verdict.
  - The engine must separate findings into the four evidence tiers.
  - If direct or metadata evidence is missing and heuristics are ambiguous, the engine must return:
    $$\text{generator\_attribution} = \text{UNKNOWN} \quad (\text{Confidence: } 0.0)$$

### 3.2 Manipulation Detection: Forensic Capabilities & ELA Limitations
Can Error Level Analysis (ELA) and noise residuals prove manipulation?

#### The Scientific Reality:
- **What ELA Actually Measures:** ELA measures the degree of compression error when an image is saved at a known JPEG quality (e.g. $Q=95$) compared against its input raster. In a JPEG image that has been saved once uniformly, all regions should reach a stable error level. If a new element is pasted in from a different source or generated via inpainting, its compression error rate may differ from the surrounding background.
- **Why ELA Alone Does NOT Prove Manipulation:**
  1. *Sharp High-Contrast Natural Edges:* Legitimate photographic edges (e.g., dark hair against white sky, text overlays, building silhouettes) naturally generate high high-frequency DCT error, producing false positive "hot spots."
  2. *Uniform Low-Texture Regions:* Clear blue skies or solid studio backdrops have near-zero high-frequency detail and produce dark, zero-error regions regardless of whether they were edited.
  3. *Repeated Global Recompression:* If a composite or inpainted image is resaved multiple times at the same quality or converted to PNG/WebP, the error levels equalize, rendering ELA blind (false negative).
- **Required Six-Tier Manipulation Classification:**
  Rather than an overconfident binary claim, the engine must support six distinct states:
  1. `FULL_SYNTHESIS`: Global synthetic characteristics detected across all backbones; no localized composite seam found.
  2. `LOCAL_INPAINTING`: Localized cluster of severe ELA and noise variance discontinuity embedded within a largely homogeneous, camera-consistent background.
  3. `IMAGE_SPLICING`: Discontinuous noise variance and color covariance between discrete macro-regions, indicating multi-source compositing.
  4. `RETOUCHING`: Minor, smooth localized compression variances without sharp boundary discontinuities.
  5. `NO_MANIPULATION_EVIDENCE_DETECTED`: Uniform compression decay and consistent noise variance throughout all quadrants.
  6. `INSUFFICIENT_EVIDENCE`: Image format is uncompressed, resolution is below threshold, or severe multi-pass compression destroys residual signals.

### 3.3 Confidence Scoring & Calibration Audit
Are the current parameters $T = 1.20$ and $\rho = 0.68$ mathematically calibrated?

#### Audit Finding:
- **Status:** **PROVISIONAL HEURISTIC BASELINES.**
- The temperature parameter $T = 1.20$ was selected heuristically to soften overconfident transformer logits near $0.0$ and $1.0$.
- The covariance penalty $\rho = 0.68$ was chosen based on initial empirical correlation estimates between Swin and ViT backbones on a limited internal set.
- **Neither parameter has been certified via formal calibration validation.** Therefore, presenting output probabilities as "statistically calibrated posterior probabilities" is scientifically inaccurate.

#### Required Validation Protocol for True Calibration:
To formally claim calibrated probabilities, AICF must execute a calibration study:
1. **Benchmark Datasets:** Evaluate on a stratified, held-out test split of $\ge 2,000$ images across:
   - Modern Diffusion: SD v1.5, SDXL, Midjourney v5/v6, FLUX.1, DALL-E 3.
   - Authentic Camera: RAISE dataset (uncompressed RAW camera captures), ImageNet val set, diverse mobile phone captures with real EXIF.
2. **Metrics to Compute & Publish:**
   - **Expected Calibration Error (ECE):**
     $$\text{ECE} = \sum_{m=1}^{M} \frac{|B_m|}{N} \left| \text{acc}(B_m) - \text{conf}(B_m) \right|$$
     (Target: $\text{ECE} < 0.05$ across 10 bins).
   - **Brier Score:** Mean squared difference between predicted probability and actual binary label (Target: $<0.08$).
   - **Reliability Diagrams:** Visual plotting of empirical accuracy vs. mean predicted confidence.
- **Interim Terminology:** In all reports, UI elements, and API documentation, scores must be clearly designated as **"Ensemble Forensic Scores (Provisional Calibration)"** rather than certified probabilities.

---

## 4. Recommended Model Architecture & Roadmap

```
                       [ Input Image Raster & Raw Bytes ]
                                      |
       +------------------------------+------------------------------+
       |                              |                              |
       v                              v                              v
[ Engine 1: Deep Vision ]     [ Engine 2: Forensic Signal ]  [ Engine 3: Hive-Style Intelligence ]
  - Swin-B ViT (Primary)        - 2D Fourier (FFT) Spectra     - Latent Signature Attribution
  - ViT-Base (Gated Secondary)  - Laplacian Noise Residuals      * 4-Tier Evidence Separation
  - Model Registry Telemetry    - Block-Discontinuity (16x16)    * Emits UNKNOWN if absent
    * Logits, Probs, Dim, Dev   - EXIF / C2PA Verification     - Manipulation Classifier
                                                                 * 6-Tier Forensic Taxonomy
                                                                 * Emits INSUFFICIENT_EVIDENCE
                                      |
                                      v
                      [ Provisional Ensemble Aggregator ]
                        - Temperature Scaling (T = 1.20, Provisional)
                        - Covariance Penalty (rho = 0.68, Provisional)
                        - Model Registry Telemetry Standard (Logits, Probs, Dim, Device)
                        - Categorical Evidence Strength (STRONG / MODERATE / WEAK / INCONCLUSIVE)
                        - Uncertainty Drivers & Disagreement Analysis Narrative
                                      |
                                      v
                     [ Standardized Forensic Report & API ]
```

### Justification for Phase 2:
1. **High Speed & Low Memory:** Maintains local inference execution targets ($\sim 180$ms CPU latency, $<15$ MB added RAM).
2. **Air-Gapped & Zero-Cost:** Zero external API bills, zero network egress, fully functional in private corporate networks.
3. **Scientifically Honest:** Accurately informs users of the distinction between direct cryptographic proof, metadata clues, and statistical heuristics, with zero false claims of certainty.
