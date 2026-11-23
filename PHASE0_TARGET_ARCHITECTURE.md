# PHASE 0: TARGET SYSTEM FORENSIC ARCHITECTURE
**Project:** `C:\Users\acer\IMAGE`  
**Application Title:** A Multimodal Deep Learning Framework for Robust Detection of Synthetic Media (AICF)  
**Audit Date:** 2026-11-18  
**Architecture Paradigm:** Local-First, Privacy-Preserving, Air-Gapped Capable Multi-Modal Cyber-Forensics  

---

## 1. Architectural Principles & Zero-Trust Posture

The AICF target architecture is founded upon five non-negotiable operational principles:

1. **Local-First Precedence:** Primary neural classification and signal processing run completely on-premises at zero recurring cost without internet connectivity.
2. **Transparent Availability & Scientific Honesty:** If a neural model is missing weights or constrained by host resources, it honestly reports `UNAVAILABLE` or `RESOURCE_CONSTRAINED`. Neutral fallback scores are **never** fabricated.
3. **Optional Third-Party Corroboration:** Commercial cloud APIs (Hive AI, GPTZero, Copyleaks) operate strictly as secondary, non-authoritative corroborators. Keys are encrypted at rest, and requests require explicit analyst consent per transaction.
4. **Permanent Audio Cancellation:** Synthetic voice and audio forensics remain **PERMANENTLY CANCELLED** across all pipelines, models, and endpoints.
5. **Defensible Chain of Custody:** Every analyzed payload is hashed with SHA-256 upon ingestion and immortalized in database records and two-pass ReportLab PDF dossiers.

---

## 2. Component Architecture Breakdown

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 AICF FORENSIC CONSOLE                                  │
│                       (Next.js 16.4.x + React 19 + Tailwind v4)                        │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ HTTP / JSON (Port 8000)
┌───────────────────────────────────────────▼────────────────────────────────────────────┐
│                                 FASTAPI FORENSIC GATEWAY                               │
│           (Lifespan Pre-Warming, Argon2id Auth, In-Memory Sliding-Window Limiter)      │
└─────┬───────────────────┬───────────────────┬───────────────────┬────────────────┬─────┘
      │                   │                   │                   │                │
┌─────▼─────┐       ┌─────▼─────┐       ┌─────▼─────┐       ┌─────▼─────┐    ┌─────▼─────┐
│   TEXT    │       │   IMAGE   │       │   VIDEO   │       │   CLOUD   │    │  REPORT   │
│ FORENSICS │       │ FORENSICS │       │ FORENSICS │       │    HUB    │    │  ENGINE   │
└─────┬─────┘       └─────┬─────┘       └─────┬─────┘       └─────┬─────┘    └─────┬─────┘
      │                   │                   │                   │                │
┌─────▼───────────┐ ┌─────▼───────────┐ ┌─────▼───────────┐ ┌─────▼──────────┐ ┌──▼─────────┐
│ • RoBERTa (125M)│ │ • Swin ViT (B)  │ │ • OpenCV Demux  │ │ • PBKDF2 Vault │ │ • SHA-256   │
│ • DeBERTa-v3    │ │ • ViT-Base      │ │ • Haar Cascade  │ │ • Hive Adapter │ │ • ReportLab │
│ • Shannon Math  │ │ • 2D FFT Aniso  │ │ • MesoNet-4 Head│ │ • GPTZero Adpt │ │   Numbered  │
│ • Burstiness CV │ │ • Laplacian Var │ │ • Frame Differ. │ │ • Copyleaks Adp│ │   Canvas    │
│ • TTR & 3-grams │ │ • ELA Heatmaps  │ │ • Temporal Jitt.│ │ • Mandatory    │ │ • Evidentiary│
│ • Covar Ensemble│ │ • EXIF / C2PA   │ │ • Multi-Signal  │ │   Consent Gate │ │   Audit Log │
└─────────────────┘ └─────────────────┘ └─────────────────┘ └────────────────┘ └───────────┘
```

---

## 3. Subsystem Architectural Specifications

### A. Text Detection Engine (`MOD-TXT-01`)
- **Primary Neural Model:** `roberta-base-openai-detector` (125M parameters, sequence classification head). Loaded locally on CPU/CUDA.
- **Secondary Neural Model:** `microsoft/deberta-v3-base` fine-tuned for synthetic text discrimination. Enforces host disk free-space check ($>1.0\text{ GB}$).
- **Deterministic Information-Theoretic Profiler:**
  - Token-level Shannon entropy:
    $$H(X) = -\sum_{i=1}^{n} P(x_i) \log_2 P(x_i)$$
  - Sentence length burstiness coefficient of variation:
    $$B = \frac{\sigma_{\text{lengths}}}{\mu_{\text{lengths}}}$$
  - Lexical diversity (Type-Token Ratio):
    $$\text{TTR} = \frac{|\text{Vocabulary Unique}|}{|\text{Total Tokens}|}$$
  - Syntactic loop analysis: Repetitive 3-gram distribution ratio.
- **Payload Boundaries:** Min 50 characters, Max 50,000 characters.

### B. Image Detection Engine (`MOD-IMG-02`)
- **Primary Vision Backbone:** `umm-maybe/AI-image-detector` (Swin-Base patch4 window7 224). Shifted-window self-attention isolates localized synthetic spatial artifacts.
- **Secondary Vision Backbone:** `google/vit-base-patch16-224` (Vision Transformer). Global patch attention provides cross-backbone verification.
- **Frequency Domain Engine:** 2D Fast Fourier Transform (FFT) computing 8-octant azimuthal power spectrum anisotropy and high-frequency Nyquist energy ratio.
- **Spatial Domain Engine:** Laplacian kernel convolution ($\nabla^2 f$) computing high-pass variance for edge blur and artificial smoothness.
- **Explainability Engine:** Error Level Analysis (ELA) re-compressing at 95% JPEG quality to compute pixel-level compression artifact differentials, rendered as heatmaps.
- **Provenance Engine:** In-memory metadata parsing for EXIF (camera make, model, software) and C2PA credentials.
- **Payload Boundaries:** Max 20 MB, Max $16,384 \times 16,384$ px, JPEG/PNG/WebP.

### C. Video Detection Engine (`MOD-VID-03`)
- **Stream Ingestion & Demuxer:** Headless OpenCV `cv2.VideoCapture` decoding MP4, MOV, WebM, and AVI streams up to 50 MB.
- **Temporal Keyframe Sampler:** Uniform 1.0-second interval sampling extracting up to 30 candidate frames with immediate disk cleanup.
- **Keyframe Screener:** Passes extracted PIL frames through Swin ViT for individual visual manipulation scoring.
- **Facial Deepfake Engine:**
  - Haar Cascade face detection with eye and nose alignment.
  - MesoNet-4 convolutional neural network (`face_deepfake.py`).
  - When `models/mesonet4_ffpp.pt` weights are missing, honestly reports `UNAVAILABLE` and derives face consensus from spatial seam boundaries without fabricating neural scores.
- **Temporal Consistency Engine:** Inter-frame pixel difference variance and temporal flicker index across sequential frames.

### D. Multi-Model Ensemble Aggregation Engine
- **Consensus Mathematical Model:**
  $$P_{\text{calibrated}} = \sigma\left(\frac{1}{T} \sum_{m \in M} w_m \cdot \text{logit}(P_m) + \Delta_{\text{prior}}\right)$$
  Where $T = 1.25$ is the temperature scaling factor, $w_m$ represents detector covariance weights, and $\Delta_{\text{prior}}$ represents deterministic heuristic regularizers (entropy/FFT).
- **Wilson Score 95% Confidence Bounds:**
  $$\hat{p} \pm \frac{z}{1 + \frac{z^2}{n}} \sqrt{\frac{\hat{p}(1-\hat{p})}{n} + \frac{z^2}{4n^2}}$$
- **Verdict Categorization:**
  - $\ge 65.0\%$ Calibrated AI Likelihood: **`LIKELY AI-GENERATED`**
  - $\le 35.0\%$ Calibrated AI Likelihood: **`LIKELY HUMAN / REAL`**
  - $35.1\% - 64.9\%$ or Conflicting Models: **`INCONCLUSIVE / MIXED EVIDENCE`**

### E. Evidence & Non-Repudiation Reporting Engine
- **Cryptographic Non-Repudiation:** Computes raw SHA-256 hashes immediately upon file ingestion; hashes are stored in SQLite and displayed on reports.
- **ReportLab PDF Engine:** Two-pass `NumberedCanvas` generating formal forensic dossiers with visual telemetry tables, model breakdowns, and chain-of-custody timestamps.
- **HTML Injection Immunity:** All dynamic text parsed through `xml.sax.saxutils.escape()` before insertion into ReportLab flowables.

### F. User-Friendly Forensic Dashboard & UI
- **Design System:** Obsidian & Gold luxury aesthetic (`#090A0D`, `#12151B`, `#181C23`, `#292D35`, `#D6B15E`, `#F0D58A`).
- **Interactive Heatmap Viewer:** Tabbed visualizer switching between Original Capture, ELA Heatmap (Q=95), and High-Pass Noise Residuals.
- **Encrypted Cloud Hub Settings:** UI for storing optional third-party keys with client-side masking (`hiv_••••••••1234`) and explicit consent toggles.
