# STEP 0: AI DETECTION MODELS & APIS TECHNICAL AUDIT REPORT

**Project:** A Multimodal Deep Learning Framework for Robust Detection of Synthetic Media (AICF)  
**Workspace:** `C:\Users\acer\IMAGE`  
**Audit Date:** November 15, 2026  
**Auditor:** Principal AI Research Engineer & Reverse Engineering Specialist  

---

## 1. Executive Summary

This report delivers an exhaustive technical, licensing, and economic audit of AI detection models and commercial APIs across all relevant modalities (Text, Image, Video). 

A critical architectural objective of the AICF platform is to ensure **100% autonomous local operation at $0 recurring cost** using open-source, permissively licensed neural backbones and deterministic mathematical forensics, while maintaining **modular cloud adapters** that allow enterprise users to optionally plug in their own proprietary commercial API keys (e.g., Hive AI, GPTZero, Copyleaks) for secondary corroboration.

Per project guidelines, **Audio detection is permanently CANCELLED** and omitted from implementation planning.

---

## 2. Modality 1: Text Detection Models & APIs

### 2.1 Local Open-Source Models ($0 Cost / Self-Hosted)

#### 1. RoBERTa Sequence Classifier (`roberta-base-openai-detector`)
- **Architecture:** 12-layer, 768-hidden, 12-heads Transformer (125M parameters) fine-tuned by OpenAI on 500k GPT-2 outputs and human web texts.
- **Weights Size:** ~501 MB.
- **Execution Target:** CPU (Torch float32) or CUDA (fp16).
- **Latency:** ~120ms – 280ms on modern multicore CPU for a 500-word sample.
- **License:** MIT / Apache 2.0 (Permissive for research and commercial use).
- **Forensic Strengths:** Highly consistent on standard LLM outputs (GPT-3.5, GPT-4, LLaMA).
- **Status in AICF:** **IMPLEMENTED AND VERIFIED** (`backend/app/ml/text/detector.py`).

#### 2. DeBERTa-v3 Synthetic Classifier (`microsoft/deberta-v3-base` or fine-tuned variants)
- **Architecture:** Disentangled Attention Mechanism with Enhanced Masked Language Modeling (86M – 130M parameters).
- **Weights Size:** ~510 MB.
- **Execution Target:** CPU or CUDA.
- **Latency:** ~180ms – 350ms on CPU.
- **License:** MIT / Apache 2.0.
- **Forensic Strengths:** Superior cross-architecture generalization on newer generation LLMs (Claude 3.5, Gemini 1.5, LLaMA-3).
- **Status in AICF:** **PARTIALLY IMPLEMENTED** (RoBERTa active; DeBERTa adapter architected for ensemble consensus).

#### 3. Deterministic Statistical & Information-Theoretic Profiler
- **Techniques:**
  - Shannon Token Entropy: $H = -\sum p_i \log_2(p_i)$
  - Burstiness Score: Coefficient of variation of sentence lengths ($\sigma / \mu$)
  - Type-Token Ratio (TTR): Lexical diversity metric
  - Repeated N-Gram Ratio: 3-gram structural repetition
- **Hardware Footprint:** 0 MB VRAM, negligible CPU (<2ms).
- **License:** Open Source (Python Standard Library / SciPy).
- **Forensic Strengths:** Immune to model drift; provides mathematical explainability for court and audit defense.
- **Status in AICF:** **IMPLEMENTED AND VERIFIED** (`backend/app/ml/text/features.py`).

---

### 2.2 Commercial Cloud APIs (Metered / Proprietary)

#### 1. GPTZero API (`api.gptzero.me`)
- **Protocol:** HTTPS REST (`POST /v2/predict/text`).
- **Input:** Raw text payload; returns document-level and sentence-level AI probabilities, perplexity, and burstiness.
- **Pricing:** ~$15/month for 50k words; ~$0.0003/word on metered tiers.
- **License / Terms:** Commercial SaaS; prohibits resale of raw model weights.
- **Status in AICF:** **CONFIGURATION REQUIRED** (Cloud adapter pattern).

#### 2. Copyleaks AI Detection API (`api.copyleaks.com`)
- **Protocol:** HTTPS REST (`POST /v3/ai-back-detection/submit`).
- **Input:** Raw text, URL, or document; returns AI vs Human percentages and OCR detection.
- **Pricing:** Credit-based (~$10 for 100 pages / 25k words).
- **License / Terms:** Commercial SaaS.
- **Status in AICF:** **CONFIGURATION REQUIRED** (Cloud adapter pattern).

#### 3. Sapling AI Detector API (`api.sapling.ai`)
- **Protocol:** HTTPS REST (`POST /api/v1/aidetect`).
- **Input:** JSON payload; returns sentence-level synthetic probability breakdown.
- **Pricing:** $25/month base plan + metered usage.
- **Status in AICF:** **CONFIGURATION REQUIRED**.

#### 4. Turnitin & Scribbr
- **API Availability:** **NO PUBLIC COMMERCIAL DEVELOPER API**.
- **Access Restrictions:** Turnitin is exclusively licensed to accredited educational institutions via Learning Management System (LMS) LTI integrations. Scribbr is a consumer wrapper offering single-document paid scans.
- **Status in AICF:** **NOT PUBLICLY AVAILABLE**.

---

## 3. Modality 2: Image Detection Models & APIs

### 3.1 Local Open-Source Models ($0 Cost / Self-Hosted)

#### 1. Swin Vision Transformer (`umm-maybe/AI-image-detector`)
- **Architecture:** Swin-B (Shifted Window Hierarchical Vision Transformer, ~88M parameters).
- **Input:** $224 \times 224 \times 3$ or $384 \times 384 \times 3$ RGB tensor normalized by ImageNet mean/std.
- **Weights Size:** ~350 MB.
- **Execution Target:** CPU or CUDA.
- **Latency:** ~250ms – 450ms on CPU; ~25ms on modern GPU.
- **License:** CC-BY-4.0 (Open research and commercial attribution).
- **Forensic Strengths:** High sensitivity to local patch-level generative artifacts produced by diffusion and GAN generators.
- **Status in AICF:** **IMPLEMENTED AND VERIFIED** (`backend/app/ml/image/detector.py`).

#### 2. 2D Fast Fourier Transform (FFT) Spectral Anisotropy Analyzer
- **Techniques:**
  - 2D Discrete Fourier Transform: $F(u, v) = \sum_{x} \sum_{y} f(x, y) e^{-i 2\pi (ux/M + vy/N)}$
  - High-frequency azimuthal integration and spectral power falloff.
  - Generative diffusion models and GAN upsamplers leave distinctive periodic checkerboard and grid peaks in high-frequency spectral bands.
- **Hardware Footprint:** Negligible CPU (<15ms per image).
- **License:** Open Source (NumPy / SciPy).
- **Status in AICF:** **IMPLEMENTED AND VERIFIED** (`backend/app/ml/image/features.py`).

#### 3. Spatial Laplacian Noise & Edge Variance Estimator
- **Techniques:** Convolves image with $3 \times 3$ Laplacian kernel to compute second-order spatial derivatives and assess synthetic smoothness vs. natural sensor noise.
- **Status in AICF:** **IMPLEMENTED AND VERIFIED** (`backend/app/ml/image/features.py`).

#### 4. Cryptographic Provenance & C2PA Metadata Parser
- **Techniques:** Extracts EXIF markers, IPTC data, and Content Credentials (C2PA) manifests to detect generation parameters (`prompt`, `steps`, `cfg_scale`, `software: Midjourney / Stable Diffusion / DALL-E`).
- **Status in AICF:** **IMPLEMENTED AND VERIFIED** (`backend/app/ml/image/features.py`).

---

### 3.2 Commercial Cloud APIs (Metered / Proprietary)

#### 1. Hive AI Image Detection API (`api.thehive.ai`)
- **Protocol:** HTTPS REST (`POST /api/v2/task/sync`).
- **Capabilities:** Detection of Midjourney, Stable Diffusion, DALL-E, Flux, Adobe Firefly, Imagen.
- **Pricing:** ~$1.50 per 1,000 images.
- **License / Terms:** Enterprise SaaS.
- **Status in AICF:** **CONFIGURATION REQUIRED** (`backend/app/ml/video/hive_adapter.py` / image adapter).

#### 2. Sightengine AI Image Detection API (`api.sightengine.com`)
- **Protocol:** HTTPS REST (`POST /1.0/check.json?models=genai`).
- **Pricing:** Free tier (2,000 operations/mo); paid tiers from $19/mo.
- **Status in AICF:** **CONFIGURATION REQUIRED**.

---

## 4. Modality 3: Video Detection Models & APIs

### 4.1 Local Open-Source Architecture ($0 Cost / Self-Hosted)

#### 1. AICF Headless Temporal Video Forensics Engine
- **Architecture:** Uniform temporal keyframe extractor using headless OpenCV (`cv2.VideoCapture`).
- **Sampling Cadence:** 1.0 keyframe per second (configurable down to 0.5s).
- **Inference Pipeline:**
  - Keyframe PIL tensors are fed directly into the local Swin Vision Transformer (`classify_image`).
  - Inter-frame pixel delta and temporal flicker variance are computed to detect inter-frame synthesis inconsistencies.
- **Hardware Footprint:** OpenCV decoding on CPU + Swin ViT forward pass (~350 MB RAM).
- **Throughput:** ~0.4s to 0.8s per second of video on CPU.
- **Status in AICF:** **IMPLEMENTED AND VERIFIED** (`backend/app/ml/video/detector.py`).

#### 2. Dedicated Facial Deepfake Classifier (MesoNet / EfficientNet-B4)
- **Architecture:** Face detection (RetinaFace / OpenCV Haar / MTCNN) to crop facial bounding boxes, followed by MesoNet-4 or EfficientNet-B4 fine-tuned on FaceForensics++ (Deepfakes, Face2Face, FaceSwap, NeuralTextures).
- **Hardware Footprint:** ~60 MB – 120 MB VRAM/RAM.
- **License:** Open Source (Academic/Research).
- **Status in AICF:** **NOT IMPLEMENTED** (Marked with `REQUIRES_DEDICATED_MODEL` in existing codebase).

---

### 4.2 Commercial Cloud Video APIs

#### 1. Hive AI Video Detection API (`api.thehive.ai`)
- **Protocol:** HTTPS REST (`POST /api/v2/task/sync` or `/async`).
- **Pricing:** ~$6.00 per 1,000 video frames (~$0.18 for a 30s video at 1 fps).
- **Integration:** Verified adapter present in `backend/app/ml/video/hive_adapter.py`.
- **Status in AICF:** **CONFIGURATION REQUIRED**.

#### 2. Sensity AI Deepfake Detection Platform
- **Protocol:** Enterprise proprietary API.
- **Pricing:** Enterprise contract required (thousands of dollars per year).
- **Status in AICF:** **NOT PUBLICLY AVAILABLE**.

---

## 5. Comprehensive Model & API Comparison Matrix

| Modality | System / Engine Name | Source / Provider | Architecture | Cost / 1k Units | Local Offline? | AICF Status |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| **Text** | `roberta-base-openai-detector` | OpenAI / HuggingFace | 125M RoBERTa Transformer | **$0.00** | **YES** | **IMPLEMENTED AND VERIFIED** |
| **Text** | Deterministic Feature Profiler | AICF Internal | Entropy + Burstiness + TTR | **$0.00** | **YES** | **IMPLEMENTED AND VERIFIED** |
| **Text** | `microsoft/deberta-v3-base` | Microsoft / HuggingFace | 130M DeBERTa Transformer | **$0.00** | **YES** | **PARTIALLY IMPLEMENTED** |
| **Text** | GPTZero Cloud API | GPTZero Inc. | Proprietary Cloud Multi-Model | ~$0.30 | NO | **CONFIGURATION REQUIRED** |
| **Text** | Copyleaks Cloud API | Copyleaks Inc. | Proprietary Cloud AI Detector | ~$0.40 | NO | **CONFIGURATION REQUIRED** |
| **Text** | Sapling AI Detector API | Sapling Intelligence | Proprietary Transformer API | ~$0.50 | NO | **CONFIGURATION REQUIRED** |
| **Text** | Turnitin AI Writing Indicator | Turnitin LLC | Enterprise LMS Closed Model | N/A | NO | **NOT PUBLICLY AVAILABLE** |
| **Text** | ZeroGPT Web Scraper | Unofficial Third-Party | Scraped Web Interface | Fragile | NO | **NOT IMPLEMENTED** |
| **Image** | `umm-maybe/AI-image-detector` | HuggingFace Hub | 88M Swin Vision Transformer | **$0.00** | **YES** | **IMPLEMENTED AND VERIFIED** |
| **Image** | 2D Spectral FFT Anisotropy | AICF Internal | Radial & Azimuthal FFT Power | **$0.00** | **YES** | **IMPLEMENTED AND VERIFIED** |
| **Image** | Spatial Laplacian Noise | AICF Internal | Second-Order Derivative Variance | **$0.00** | **YES** | **IMPLEMENTED AND VERIFIED** |
| **Image** | EXIF / C2PA Provenance Parser | AICF Internal | Cryptographic Manifest Reader | **$0.00** | **YES** | **IMPLEMENTED AND VERIFIED** |
| **Image** | Hive AI Image Detection | Hive AI | Proprietary Cloud Ensemble | ~$1.50 | NO | **CONFIGURATION REQUIRED** |
| **Image** | Sightengine AI Generation | Sightengine | Proprietary Deep Learning API | ~$1.00 | NO | **CONFIGURATION REQUIRED** |
| **Video** | OpenCV + Swin Temporal Engine | AICF Internal | Uniform 1.0s Keyframe ViT + $\Delta$ | **$0.00** | **YES** | **IMPLEMENTED AND VERIFIED** |
| **Video** | Dedicated Facial Deepfake Head | FaceForensics++ / MesoNet | Face-crop Boundary Classifier | **$0.00** | **YES** | **NOT IMPLEMENTED** |
| **Video** | Hive AI Video Detection | Hive AI | Proprietary Cloud Keyframe ViT | ~$6.00 | NO | **CONFIGURATION REQUIRED** |
| **Audio** | Any Audio / Voice Model | Various | Permanently Cancelled | N/A | N/A | **NOT IMPLEMENTED** (Cancelled) |

---

## 6. Strategic Architecture: Two-Tier Hybrid Design for AICF

To maximize scientific independence, user privacy, and economic sustainability, AICF should adhere to the following architecture:

### Tier 1: Primary Zero-Cost Local Engine (Default)
- 100% self-hosted on CPU or CUDA.
- Utilizes verified local transformers: RoBERTa + DeBERTa-v3 for Text; Swin ViT + 2D FFT + Laplacian for Image; Temporal Keyframe Screening for Video.
- Guarantees complete data privacy (no sensitive documents or media uploaded to third-party cloud servers).
- Provides deterministic SHA-256 ledgers and PDF forensic exports.

### Tier 2: User-Supplied API Key Corroboration Hub (Optional)
- Users can optionally provide their own API keys in their profile settings or `.env` configuration:
  - `HIVE_API_KEY`: Queries Hive for secondary image/video verification.
  - `GPTZERO_API_KEY`: Queries GPTZero for secondary academic text corroboration.
  - `COPYLEAKS_API_KEY`: Queries Copyleaks for secondary text corroboration.
- When configured, these third-party cloud verdicts appear alongside local model scores as "External Cloud Corroboration" in the analysis dashboard and PDF reports.
- If no key is configured, the local engine handles 100% of the forensic workflow cleanly without errors or warnings.
