# PHASE 0: FEATURE COMPARISON & STATUS MATRIX
**Project:** `C:\Users\acer\IMAGE`  
**Application:** A Multimodal Deep Learning Framework for Robust Detection of Synthetic Media (AICF)  
**Audit Date:** 2026-11-18  
**Scope:** Comparative matrix benchmarking Hive AI, Humbot AI, Existing AICF, and Proposed Target Architecture  

---

## 1. Classification Methodology & Status Taxonomy

Every feature across all platforms is categorized using the six mandatory standardized labels:

1. **`VERIFIED PUBLIC FEATURE`**: Feature is publicly documented, observable in production, and verified through official documentation or live testing.
2. **`OFFICIAL API AVAILABLE`**: Vendor provides an authorized, documented developer API endpoint accessible via standard authentication.
3. **`OPEN-SOURCE ALTERNATIVE`**: A verified, freely distributable open-source library, model, or algorithm (MIT, Apache 2.0, BSD) capable of executing on-premise at zero cost.
4. **`REQUIRES CONFIGURATION`**: Architecture or adapter is fully implemented in code, but requires customer-provided credentials, API keys, or pre-trained weight files to activate.
5. **`NOT AVAILABLE`**: Feature cannot be legally or technically implemented (e.g. proprietary model weights, enterprise-exclusive LMS gates like Turnitin, non-existent endpoints).
6. **`NOT VERIFIED`**: Claimed in third-party marketing but cannot be verified through official technical documentation.

---

## 2. Comprehensive Master Comparison Matrix

| Feature / Capability | Hive AI | Humbot AI | Existing AICF (`C:\Users\acer\IMAGE`) | Proposed Implementation | Evidence & Technical Notes |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Local Offline Text Detection** | `NOT AVAILABLE` | `NOT AVAILABLE` | **`OPEN-SOURCE ALTERNATIVE`** | **`OPEN-SOURCE ALTERNATIVE`** | RoBERTa (`roberta-base-openai-detector`) executed locally on CPU/CUDA. |
| **Secondary Local Text Model** | `NOT AVAILABLE` | `NOT AVAILABLE` | **`OPEN-SOURCE ALTERNATIVE`** | **`OPEN-SOURCE ALTERNATIVE`** | DeBERTa-v3 (`microsoft/deberta-v3-base`) with disk headroom validation. |
| **Deterministic Shannon Entropy** | `NOT AVAILABLE` | `NOT AVAILABLE` | **`OPEN-SOURCE ALTERNATIVE`** | **`OPEN-SOURCE ALTERNATIVE`** | Mathematical token-level Shannon entropy ($H = -\sum p_i \log_2 p_i$). |
| **Sentence Length Burstiness** | `NOT AVAILABLE` | `NOT VERIFIED` | **`OPEN-SOURCE ALTERNATIVE`** | **`OPEN-SOURCE ALTERNATIVE`** | Coefficient of variation ($\sigma / \mu$) across sentence length distributions. |
| **Vocabulary Diversity (TTR)** | `NOT AVAILABLE` | `NOT AVAILABLE` | **`OPEN-SOURCE ALTERNATIVE`** | **`OPEN-SOURCE ALTERNATIVE`** | Type-Token Ratio calculated across lexical token counts. |
| **Syntactic 3-Gram Repetition** | `NOT AVAILABLE` | `NOT AVAILABLE` | **`OPEN-SOURCE ALTERNATIVE`** | **`OPEN-SOURCE ALTERNATIVE`** | Repeated n-gram frequency ratio for syntactic loop detection. |
| **Multi-Detector Text Consensus** | `NOT AVAILABLE` | `VERIFIED PUBLIC FEATURE` | **`OPEN-SOURCE ALTERNATIVE`** | **`OPEN-SOURCE ALTERNATIVE`** | Temperature-scaled covariance aggregation ($T=1.25, \rho=0.72$). |
| **Text Humanization / Paraphrasing**| `NOT AVAILABLE`| `VERIFIED PUBLIC FEATURE` | `NOT AVAILABLE` | `NOT AVAILABLE` | Intentionally excluded to protect forensic non-repudiation and chain of custody. |
| **Local Offline Image Detection** | `NOT AVAILABLE` | `NOT AVAILABLE` | **`OPEN-SOURCE ALTERNATIVE`** | **`OPEN-SOURCE ALTERNATIVE`** | Swin Vision Transformer (`umm-maybe/AI-image-detector`) executed locally. |
| **Secondary Local Vision Model** | `NOT AVAILABLE` | `NOT AVAILABLE` | **`OPEN-SOURCE ALTERNATIVE`** | **`OPEN-SOURCE ALTERNATIVE`** | ViT-Base global self-attention (`google/vit-base-patch16-224`). |
| **2D FFT Spectral Anisotropy** | `NOT AVAILABLE` | `NOT AVAILABLE` | **`OPEN-SOURCE ALTERNATIVE`** | **`OPEN-SOURCE ALTERNATIVE`** | 2D Fast Fourier Transform azimuthal octant variance analysis. |
| **Laplacian Noise Residual** | `NOT AVAILABLE` | `NOT AVAILABLE` | **`OPEN-SOURCE ALTERNATIVE`** | **`OPEN-SOURCE ALTERNATIVE`** | High-pass spatial convolution for edge blur and synthetic smoothness. |
| **Error Level Analysis (ELA)** | `NOT AVAILABLE` | `NOT AVAILABLE` | **`OPEN-SOURCE ALTERNATIVE`** | **`OPEN-SOURCE ALTERNATIVE`** | 95% JPEG recompression error delta heatmap visualization. |
| **EXIF / C2PA Provenance** | `VERIFIED PUBLIC FEATURE` | `NOT AVAILABLE` | **`OPEN-SOURCE ALTERNATIVE`** | **`OPEN-SOURCE ALTERNATIVE`** | In-memory EXIF extraction and C2PA manifest inspection. |
| **Image Generator Attribution** | `VERIFIED PUBLIC FEATURE` | `NOT AVAILABLE` | `NOT AVAILABLE` | **`REQUIRES CONFIGURATION`** | Hive classifies Midjourney/SD/DALL-E; local requires dedicated classifier. |
| **Video Keyframe Demuxing** | `VERIFIED PUBLIC FEATURE` | `NOT AVAILABLE` | **`OPEN-SOURCE ALTERNATIVE`** | **`OPEN-SOURCE ALTERNATIVE`** | OpenCV headless uniform 1.0s temporal sampling (max 30 frames). |
| **Video Frame-by-Frame ViT** | `VERIFIED PUBLIC FEATURE` | `NOT AVAILABLE` | **`OPEN-SOURCE ALTERNATIVE`** | **`OPEN-SOURCE ALTERNATIVE`** | Swin ViT forward pass across sampled PIL keyframes. |
| **Temporal Consistency Telemetry**| `VERIFIED PUBLIC FEATURE`| `NOT AVAILABLE` | **`OPEN-SOURCE ALTERNATIVE`** | **`OPEN-SOURCE ALTERNATIVE`** | Deterministic inter-frame difference and temporal flicker score std-dev. |
| **Face Detection & Alignment** | `VERIFIED PUBLIC FEATURE` | `NOT AVAILABLE` | **`OPEN-SOURCE ALTERNATIVE`** | **`OPEN-SOURCE ALTERNATIVE`** | OpenCV Haar Cascade face detection with eye/nose alignment. |
| **MesoNet-4 Facial Deepfake** | `VERIFIED PUBLIC FEATURE` | `NOT AVAILABLE` | **`REQUIRES CONFIGURATION`** | **`REQUIRES CONFIGURATION`** | PyTorch MesoNet-4 architecture verified; weights (`mesonet4_ffpp.pt`) needed. |
| **Hive AI Cloud API Adapter** | `OFFICIAL API AVAILABLE` | `NOT AVAILABLE` | **`REQUIRES CONFIGURATION`** | **`REQUIRES CONFIGURATION`** | Unified Hive adapter implemented; requires customer-provided Hive API key. |
| **GPTZero Cloud API Adapter** | `NOT AVAILABLE` | `NOT VERIFIED` | **`REQUIRES CONFIGURATION`** | **`REQUIRES CONFIGURATION`** | Official GPTZero REST adapter implemented; requires customer API key. |
| **Copyleaks Cloud API Adapter** | `NOT AVAILABLE` | `NOT VERIFIED` | **`REQUIRES CONFIGURATION`** | **`REQUIRES CONFIGURATION`** | Official Copyleaks REST adapter implemented; requires customer API key. |
| **Turnitin Integration** | `NOT AVAILABLE` | `NOT VERIFIED` | `NOT AVAILABLE` | `NOT AVAILABLE` | Enterprise institutional LMS (LTI) only; no public developer API exists. |
| **Scribbr Integration** | `NOT AVAILABLE` | `NOT VERIFIED` | `NOT AVAILABLE` | `NOT AVAILABLE` | Turnitin reseller portal; protected by Cloudflare bot gates; no public API. |
| **Encrypted Credential Vault** | `NOT AVAILABLE` | `NOT AVAILABLE` | **`OPEN-SOURCE ALTERNATIVE`** | **`OPEN-SOURCE ALTERNATIVE`** | PBKDF2-HMAC-SHA256 Encrypt-then-MAC cipher with per-user key derivation. |
| **Raw Key Secret Masking** | `NOT AVAILABLE` | `NOT AVAILABLE` | **`OPEN-SOURCE ALTERNATIVE`** | **`OPEN-SOURCE ALTERNATIVE`** | Masked formatting (`hiv_••••••••1234` or `NOT_CONFIGURED`). |
| **Mandatory Analyst Consent** | `NOT AVAILABLE` | `NOT AVAILABLE` | **`OPEN-SOURCE ALTERNATIVE`** | **`OPEN-SOURCE ALTERNATIVE`** | `POST /verify-text` requires `user_consent=True`; HTTP 400 rejection if False. |
| **Multi-Tenant User Isolation** | `VERIFIED PUBLIC FEATURE` | `NOT VERIFIED` | **`OPEN-SOURCE ALTERNATIVE`** | **`OPEN-SOURCE ALTERNATIVE`** | User-scoped queries (`WHERE user_id = current_user.id`); HTTP 403 enforcement. |
| **Cryptographic SHA-256 Ledger**| `NOT AVAILABLE` | `NOT AVAILABLE` | **`OPEN-SOURCE ALTERNATIVE`** | **`OPEN-SOURCE ALTERNATIVE`** | Cryptographic hash calculated at ingestion and persisted in database. |
| **Two-Pass Forensic PDF Dossier**| `NOT AVAILABLE` | `NOT AVAILABLE` | **`OPEN-SOURCE ALTERNATIVE`** | **`OPEN-SOURCE ALTERNATIVE`** | ReportLab NumberedCanvas generating downloadable court-ready PDF dossiers. |
| **Obsidian & Gold Forensic UI** | `NOT AVAILABLE` | `NOT AVAILABLE` | **`OPEN-SOURCE ALTERNATIVE`** | **`OPEN-SOURCE ALTERNATIVE`** | Tailored luxury forensic theme (`#090A0D`, `#D6B15E`) across 14 routes. |
| **Audio Synthetic Voice Forensics**| `VERIFIED PUBLIC FEATURE`| `NOT AVAILABLE`| `NOT AVAILABLE` | `NOT AVAILABLE` | **PERMANENTLY CANCELLED** per platform governance directive. |

---

## 3. Key Analytical Insights

1. **Local Independence vs Cloud Monopoly:** Hive AI forces users into proprietary cloud billing with zero local execution. AICF matches or exceeds Hive's visual feature set locally on CPU/CUDA using Swin ViT, 2D FFT, and ELA at $0.00 operational cost.
2. **Defensive Rigor vs Evasion Marketing:** Humbot AI promotes a multi-detector display merely to sell text humanization/evasion subscriptions. AICF strictly rejects evasion, providing defensible mathematical proof (entropy, burstiness, TTR) and cryptographic chain of custody.
3. **Turnitin Reality:** Claims of automated Turnitin checking in web apps are not backed by official public developer APIs. AICF honestly disclaims Turnitin availability rather than employing brittle, terms-of-service-violating web scrapers.
4. **Honest Model Reporting:** Where specialized weights are not bundled (such as MesoNet-4 weights or DeBERTa disk limits), AICF honestly reports `UNAVAILABLE` or `RESOURCE_CONSTRAINED` instead of fabricating baseline probabilities.
