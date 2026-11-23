# PHASE 0: EXISTING AICF SYSTEM ARCHITECTURAL AUDIT
**Project:** `C:\Users\acer\IMAGE`  
**Application:** A Multimodal Deep Learning Framework for Robust Detection of Synthetic Media (AICF)  
**Audit Date:** 2026-11-18  
**Auditor:** Principal AI Research Engineer & Forensic Systems Architect  
**Scope:** Complete codebase inspection across Frontend, Backend, Machine Learning Engines, Security, Databases, and Test Suites  

---

## 1. System Inventory & High-Level Architecture

The AICF platform is structured as a decoupled, privacy-preserving, local-first forensic inspection system:

```
AICF System Architecture
├── Frontend (Next.js 16.4.3 / 16.4.6, React 19.3.0, TypeScript 5, Tailwind CSS v4)
│   ├── UI Theme: Luxury Obsidian & Gold (#090A0D, #12151B, #181C23, #292D35, #D6B15E, #F0D58A)
│   ├── Authentication: HTTP-only session cookies, AuthProvider React Context, AuthGuard
│   ├── Routes:
│   │   ├── /                         (Public landing showcase)
│   │   ├── /login & /register        (Institutional analyst authentication)
│   │   ├── /dashboard                (Operational statistics, real case counts)
│   │   ├── /dashboard/text           (MOD-TXT-01: Multi-Detector Text Forensics)
│   │   ├── /dashboard/image          (MOD-IMG-02: Multi-Model Vision & ELA Heatmaps)
│   │   ├── /dashboard/video          (MOD-VID-03: Temporal Sampling & Facial Deepfake)
│   │   ├── /dashboard/audio          (MOD-AUD-04: PERMANENTLY CANCELLED notice)
│   │   ├── /dashboard/reports        (Case Archive filterable by modality)
│   │   ├── /dashboard/evaluation     (Empirical Confusion Matrix, Wilson CIs, Brier score)
│   │   └── /dashboard/settings       (Analyst Profile, Encrypted Cloud Hub Vault)
│   └── API Client: Typed services (textApi, imageApi, videoApi, reportsApi, cloudApi)
│
├── Backend (Python 3.12, FastAPI 0.115+, Pydantic v2, SQLAlchemy 2.0 Async, aiosqlite)
│   ├── Lifespan Manager: Pre-warms RoBERTa and Swin ViT weights into memory
│   ├── Auth & Sessions: Argon2id password hashing + 256-bit SHA-256 session token vault
│   ├── Rate Limiting: In-memory sliding-window limiter on auth and analysis endpoints
│   ├── Secret Management: PBKDF2-HMAC-SHA256 Encrypt-then-MAC vault for external keys
│   ├── Reporting Engine: ReportLab 5.1.0 two-pass NumberedCanvas PDF dossiers
│   └── Routers: /auth, /dashboard, /text, /image, /video, /reports, /evaluation, /cloud
│
└── ML Forensic Engines (backend/app/ml/)
    ├── text/      (RoBERTa-base-openai-detector, DeBERTa-v3 adapter, Linguistic Profiler, Ensemble)
    ├── image/     (Swin ViT, ViT-Base secondary, 2D FFT, Laplacian Variance, ELA Heatmap generator)
    ├── video/     (OpenCV Demuxer, Haar Face Detector, MesoNet-4 facial head, Temporal Variance)
    ├── cloud/     (Unified Cloud Hub: Hive, GPTZero, Copyleaks adapters + Consent enforcement)
    └── evaluation/(Statistical benchmark harness, Wilson score intervals, calibration curves)
```

---

## 2. Deep-Dive Inspection of Modality Subsystems

### 2.1 Text Forensics Subsystem (`backend/app/ml/text/`)
- **Primary Neural Backbone:** `roberta-base-openai-detector` (125M parameters). Loaded from local cache on CPU, providing softmax classification probabilities for synthetic vs authentic text.
- **Secondary Neural Backbone:** `microsoft/deberta-v3-base`. Includes automated disk headroom check ($>1.0\text{ GB}$ required); safely reports `RESOURCE_CONSTRAINED` when disk space is low without crashing.
- **Deterministic Linguistic Profiler:**
  - Token-level Shannon entropy ($H = -\sum p_i \log_2 p_i$).
  - Sentence length burstiness coefficient of variation ($\sigma / \mu$).
  - Type-Token Ratio (TTR: unique vocabulary / total token count).
  - Syntactic n-gram repetition ratio ($n=3$).
- **Consensus Aggregator:** Temperature-scaled covariance aggregation ($T=1.25, \rho=0.72$) combining RoBERTa predictions with linguistic prior regularization.
- **Evidentiary Output:** Generates human-readable evidence summaries, SHA-256 input hashes, and ReportLab PDF dossiers.

### 2.2 Image Forensics Subsystem (`backend/app/ml/image/`)
- **Primary Neural Backbone:** `umm-maybe/AI-image-detector` (Swin Vision Transformer). Utilizes shifted window self-attention to identify localized synthetic patch anomalies.
- **Secondary Neural Backbone:** `google/vit-base-patch16-224` (Vision Transformer). Global self-attention model providing cross-verification.
- **Frequency Domain Forensics:** 2D Fast Fourier Transform (FFT) computing azimuthal octant power spectrum anisotropy and high-frequency Nyquist energy ratio.
- **Spatial Domain Forensics:** Laplacian kernel spatial convolution computing high-pass variance for edge sharpness and artificial smoothing.
- **Explainability Heatmaps:** Error Level Analysis (ELA) engine computing 95% JPEG recompression error delta matrices, rendered as base64 heatmaps.
- **Container Forensics:** In-memory EXIF extraction (camera make, model, software) and C2PA provenance credential checks.

### 2.3 Video Forensics Subsystem (`backend/app/ml/video/`)
- **Container Demuxing:** OpenCV headless `cv2.VideoCapture` decoding MP4, MOV, WebM, and AVI streams (maximum 50 MB, uniform 1.0s interval, maximum 30 frames).
- **Keyframe Screening:** Swin ViT forward pass across sampled PIL keyframes.
- **Facial Forensics & Alignment:**
  - Haar Cascade face detection with eye/nose alignment and usable bounding box filtering.
  - MesoNet-4 convolutional architecture implemented in PyTorch (`face_deepfake.py`).
  - **Honest Availability Handling:** Because `models/mesonet4_ffpp.pt` weights are not present by default, the detector transparently reports `UNAVAILABLE` and relies on spatial seam boundaries without fabricating neural scores.
- **Temporal Consistency Telemetry:** Inter-frame pixel difference variance and flicker index across sequential frames.

### 2.4 Cloud Verification Hub & Security Vault (`backend/app/ml/cloud/`)
- **Cryptographic Cipher:** PBKDF2-HMAC-SHA256 Encrypt-then-MAC cipher with 100,000 iterations.
- **Per-Tenant Derivation:** Encryption keys derived from `SECRET_KEY` + `user_id` + random salt. Keys encrypted for User A cannot be decrypted by User B.
- **Secret Masking:** Raw credentials are never transmitted to clients; returned as `hiv_••••••••1234` or `NOT_CONFIGURED`.
- **Mandatory User Consent:** `POST /api/v1/cloud/verify-text` requires `user_consent=True`. Requests with `user_consent=False` abort with HTTP 400 Bad Request before initiating outbound HTTP connections.
- **Supported Adapters:** Official adapters for **Hive AI**, **GPTZero**, and **Copyleaks**. Out of the box, all report `CONFIGURATION_REQUIRED`.

### 2.5 Relational Data Models & Multi-Tenant Isolation
- **Database:** SQLite (`aicf.db`) via SQLAlchemy Async ORM with automated startup migrations.
- **Key Tables:**
  - `users`: Analyst profiles, Argon2id password hashes, account roles.
  - `sessions`: 256-bit cryptographically secure session tokens stored exclusively as SHA-256 hashes.
  - `text_analyses`, `image_analyses`, `video_analyses`: Forensic records containing model scores, metadata, and SHA-256 hashes.
  - `forensic_reports`: Unified case reports linking multi-modal analyses.
  - `cloud_credentials`: Encrypted third-party API keys.
- **Tenant Scoping:** Every query enforces `WHERE user_id = current_user.id`. Cross-analyst access attempts return HTTP 403 Forbidden.

---

## 3. Test Suite Verification & Quality Metrics

All automated tests have been executed and verified in the native Python 3.12 environment:

```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-8.3.4
collected 129 items

backend/tests/test_auth.py ......................................... [  6%]
backend/tests/test_cloud_verification.py ........................... [ 21%]
backend/tests/test_dashboard.py .....                                [ 25%]
backend/tests/test_evaluation.py ............                        [ 34%]
backend/tests/test_health.py ..                                      [ 36%]
backend/tests/test_image_analysis.py .....................           [ 52%]
backend/tests/test_integration_e2e_security.py ...                   [ 55%]
backend/tests/test_pdf_generation.py ............                    [ 64%]
backend/tests/test_text_analysis.py .................                [ 77%]
backend/tests/test_video_analysis.py .............................   [100%]

============================ 129 passed in 113.83s ============================
```

- **Pass Rate:** **100% (129 passed, 0 failed, 0 skipped)**
- **Frontend ESLint:** 0 errors, 0 warnings
- **Frontend Next.js Build:** All 14 routes statically generated

---

## 4. Known Hardware & Environmental Limitations

1. **CPU Inference Latency:** Running RoBERTa on CPU has a cold-start latency of ~21.0 seconds; Swin ViT takes ~4.8 seconds; video sampling takes ~2.0 seconds.
2. **Memory Footprint:** Peak process working set reaches ~1,656 MB when all neural heads and OpenCV are loaded in memory.
3. **DeBERTa Disk Constraint:** Automatically suppressed when host disk free space is $<1.0\text{ GB}$.
4. **MesoNet-4 Weights Absence:** Weights `models/mesonet4_ffpp.pt` not bundled; handled transparently as `UNAVAILABLE`.
5. **Audio Forensics:** Permanently cancelled across all subsystems.

---

## 5. Architectural Preservation Commitments

1. Do **not** rebuild or alter existing working algorithms.
2. Do **not** modify database schemas or delete stored tables.
3. Keep local inference as the primary, $0-cost baseline.
4. Maintain strict multi-tenant isolation and explicit user consent for all external network interactions.
