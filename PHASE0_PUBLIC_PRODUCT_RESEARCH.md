# PHASE 0: PUBLIC PRODUCT RESEARCH REPORT
**Project:** `C:\Users\acer\IMAGE`  
**Framework Title:** A Multimodal Deep Learning Framework for Robust Detection of Synthetic Media (AICF)  
**Research Date:** 2026-11-18  
**Focus Targets:** Hive AI (Visual Media Forensics) & Humbot AI (Text Detection & Paraphrasing)  
**Legal Framework:** Clean-Room Black-Box Analysis under US Copyright Law, CFAA, and Open-Source Licensing Compliance  

---

## 1. Executive Summary & Research Scope

The purpose of this research is to perform a rigorous, legally compliant, clean-room reverse-engineering and product audit of the publicly accessible features, workflows, data contracts, and user experiences of two prominent commercial platforms in the synthetic media domain:
1. **Hive AI (`thehive.ai`):** An enterprise-grade, cloud-hosted intelligence and visual content moderation platform specializing in AI-generated image detection, video keyframe analysis, generator-source attribution, and facial deepfake identification.
2. **Humbot AI (`humbot.ai`):** A consumer-focused platform marketed as an "Undetectable AI Humanizer & All-in-One Multi-Detector AI Checker," offering multi-engine text screening alongside sequence-to-sequence paraphrasing.

### Core Strategic Distinction & Positioning
```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             MARKET POSITIONING MAP                               │
├────────────────────────┬────────────────────────┬────────────────────────────────┤
│ Hive AI (Enterprise)   │ Humbot AI (Consumer)   │ AICF Platform (Forensic Lab)   │
├────────────────────────┼────────────────────────┼────────────────────────────────┤
│ • Closed-source Cloud  │ • Consumer Evasion     │ • Local-First, Air-Gapped      │
│ • Metered API Billing  │ • Paraphrasing / SEO   │ • $0-Cost Baseline Inference   │
│ • High-volume Ingest   │ • Simulated Detection  │ • Defensible Forensic Dossiers │
│ • Proprietary Weights  │ • No Evidence Ledger   │ • Multi-Signal Triangulation   │
│ • Zero Local Execution │ • Word Credit Packs    │ • Cryptographic Chain-of-Custody│
└────────────────────────┴────────────────────────┴────────────────────────────────┘
```

AICF does **not** seek to build a commercial evasion tool or a paywalled cloud clone. Instead, AICF synthesizes the forensic rigor of Hive AI's multi-frame visual screening with a multi-model consensus architecture inspired by multi-detector text platforms, while establishing an **air-gapped capable, privacy-preserving, mathematically defensible forensic workstation**.

---

## 2. Legal, Ethical, and Clean-Room Engineering Boundaries

In accordance with strict system rules and professional cybersecurity engineering ethics:
1. **Zero Proprietary Code Extraction:** No proprietary source code, internal decompiler outputs, private keys, or weights belonging to Hive AI or Humbot AI are extracted, reproduced, or decompiled.
2. **No Paywall or Access Control Bypasses:** Research is strictly restricted to publicly accessible product documentation, published API documentation, patent disclosures, academic literature, and authorized public developer portals.
3. **No Non-Sanctioned Scraping:** AICF does not implement web scraping wrappers against ad-supported or CAPTCHA-gated consumer portals (such as Turnitin or ZeroGPT). All external integrations must use documented, authorized REST APIs.
4. **Honest Architectural Truths:**
   - AICF explicitly disclaims 100% detection accuracy.
   - Fallback neutral scores (e.g., 0.50) are never fabricated as genuine neural predictions.
   - Unconfigured or missing models are honestly flagged as `UNAVAILABLE` or `CONFIGURATION REQUIRED`.
5. **Permanent Scope Boundary:** Audio and synthetic voice forensics remain **PERMANENTLY CANCELLED** across all pipelines, models, API routes, and user interfaces.

---

## 3. Hive AI: Public Product Architecture & Workflow Audit

### 3.1 Product Purpose & Target Audience
Hive AI serves enterprise platforms, social networks, and media conglomerates. It operates as an automated content moderation firewall, screening millions of images, videos, and texts per day against synthetic generation, deepfake manipulation, and policy violations.

### 3.2 Public Workflows & User Experience
- **Interactive Web Demo:** Allows users to drag and drop single images or videos. Uploaded media is analyzed in the cloud, returning a categorical verdict (`Likely AI-Generated` vs `Likely Not AI-Generated`) and individual class confidence percentages.
- **Generator Family Attribution:** Displays likelihood percentages across known generative architectures:
  - Midjourney (v4, v5, v6)
  - Stable Diffusion (SD 1.5, SD 2.1, SDXL, SD3)
  - DALL-E (DALL-E 2, DALL-E 3)
  - Flux.1
  - Google Imagen / Adobe Firefly
- **Video Inspection Workflow:**
  - Ingests MP4, MOV, WebM containers up to several hundred megabytes.
  - Demuxes the video and samples keyframes at fixed intervals (typically 1.0s or 0.5s).
  - Displays a temporal timeline scrubber showing frame-by-frame synthetic probability bars.
  - Applies proprietary temporal smoothing to suppress transient single-frame false positives.
- **Deepfake & Face-Swap Analysis:**
  - Extracts facial crops using automated face detection (MTCNN / RetinaFace).
  - Evaluates facial boundary blending seams, color consistency across neck/jawlines, and eye reflection symmetry.
  - Returns spatial bounding box coordinates `[x1, y1, x2, y2]` around flagged facial regions.

### 3.3 Public Developer API Contracts
Hive exposes documented REST endpoints for synchronous and asynchronous processing:
- **Synchronous Endpoint:** `POST https://api.thehive.ai/api/v2/task/sync`
- **Asynchronous Endpoint:** `POST https://api.thehive.ai/api/v2/task/async` (with webhook notification or polling via `GET /api/v2/task/{task_id}`)
- **Authentication:** HTTP header `Authorization: token <HIVE_API_KEY>`
- **Payload Schema:** `multipart/form-data` with `media` file field, or `application/json` with a public `url` string.
- **Response Structure:** A nested JSON object containing timestamped frame slices, class labels, and normalized floating-point confidence values (`0.0000` to `1.0000`).

### 3.4 Economic & Operational Constraints
- **Pricing:** Metered usage starting at ~$1.50 per 1,000 images and ~$6.00 to $8.00 per 1,000 video frames. Enterprise plans require substantial annual minimum spend commitments.
- **Zero Local Capability:** Hive does not offer an on-premise Docker container or offline binary. All media must leave the analyst's workstation and travel over the public internet to Hive's cloud infrastructure.

---

## 4. Humbot AI: Public Product Architecture & Workflow Audit

### 4.1 Product Purpose & Target Audience
Humbot AI primarily targets students, digital marketers, and freelance copywriters seeking to evade AI content detection algorithms (e.g., in universities or search engine algorithms). Its core feature is text "humanization" (automated paraphrasing), with a multi-detector checker marketed as a secondary verification tool.

### 4.2 Public Workflows & User Experience
- **Input Interface:** A large text area accepting paste or direct entry, featuring character and word counters, with preset sample text buttons.
- **The "All-in-One Multi-Detector" Panel:**
  - Ingests text and displays a grid of detection badges for up to 9 commercial detectors:
    - **GPTZero**, **Copyleaks**, **Turnitin**, **Winston AI**, **ZeroGPT**, **Crossplag**, **Scribbr**, **Writer**, **Sapling**.
  - Renders simple three-state badges: `AI Detected` (Red), `Human-like / Passed` (Green), or `Uncertain` (Yellow).
  - Calculates an aggregate "Bypass Confidence" score representing the fraction of detectors passed.
- **Humanization / Paraphrasing Modes:**
  - **Quick Mode:** Shallow lexical replacement using synonyms.
  - **Enhanced Mode:** Syntactic clause reordering and sentence length modulation.
  - **Advanced Mode:** Deep semantic restructuring designed to disrupt uniform n-gram perplexity and burstiness.
- **Multilingual Support:** Publicly claims support for over 50 languages.

### 4.3 Technical API Reality vs. Marketing Presentation
A rigorous technical inspection of Humbot's developer documentation (`https://humbot.ai/api/`) reveals a major architectural constraint:
1. **Humanization-Only API:** Humbot's official API (v2.0.0) exposes endpoints exclusively for text rewriting (`POST /api/humbot/v2/create` and `GET /api/humbot/v2/retrieve`). There is **no public API** allowing developers to query independent detector scores on arbitrary raw text without running their paraphraser.
2. **Turnitin & Scribbr Non-Existence in Public APIs:** Turnitin does not provide a public developer REST API. Its integration is strictly limited to accredited higher-education institutions via LMS/LTI protocols. Commercial sites claiming "Turnitin scores" rely on internal proxy models trained on historical Turnitin outputs or brittle browser scraping that frequently fails.
3. **Forensic Void:** Humbot provides zero cryptographic hashing (no SHA-256), zero token-level entropy metrics, zero statistical dispersion telemetry, and zero PDF dossier generation.

---

## 5. Architectural Implications for AICF

| Capability | Hive AI Model | Humbot AI Model | AICF Architectural Decision |
| :--- | :--- | :--- | :--- |
| **Execution Domain** | 100% Cloud SaaS | 100% Cloud Web/API | **Local-First On-Premise (Air-gapped capable)** |
| **Operating Cost** | Metered ($/image, $/frame) | Subscription ($/word) | **$0.00 Base Cost (Free open-source models)** |
| **Text Detection** | Secondary feature | Consumer aggregator | **Multi-Model Local Ensemble (RoBERTa + DeBERTa + Linguistics)** |
| **Text Paraphrasing** | N/A | Core product | **REJECTED (Evasion defeats forensic integrity)** |
| **Image Detection** | Cloud ViT / CNN | N/A | **Swin ViT + Secondary ViT + 2D FFT + Laplacian + ELA** |
| **Video Detection** | Cloud Demux + 1 fps ViT | N/A | **OpenCV Uniform Sampling + Swin ViT + Temporal Variance** |
| **Deepfake Detection** | Cloud Face Bounding Box | N/A | **Haar Face Alignment + MesoNet-4 Architecture (Honest Weights)** |
| **Third-Party Hub** | Closed proprietary | Obfuscated proxies | **Encrypted PBKDF2 Vault + Explicit User Consent** |
| **Forensic Evidence** | JSON API response | Visual HTML badge | **Cryptographic SHA-256 + ReportLab PDF Dossiers** |

---

## 6. Synthesis & Phase 0 Deliverable Roadmap

This research establishes the empirical foundation for the subsequent Phase 0 audit documents:
- `PHASE0_HIVE_FEATURE_AUDIT.md`: Detailed technical deep-dive into Hive AI's image, video, and deepfake specifications.
- `PHASE0_HUMBOT_FEATURE_AUDIT.md`: Detailed technical deep-dive into Humbot AI's text detection, API constraints, and evasive design.
- `PHASE0_EXISTING_AICF_AUDIT.md`: Comprehensive audit of AICF's current codebase, models, tests, and database state.
- `PHASE0_FEATURE_COMPARISON.md`: Complete classification matrix with standardized acceptance statuses.
- `PHASE0_TARGET_ARCHITECTURE.md`: High-assurance engineering specifications for text, image, video, and ensemble engines.
- `PHASE0_IMPLEMENTATION_ROADMAP.md`: Staged, safe progression plan across development phases.
- `PHASE0_RISK_AND_LICENSE_AUDIT.md`: Legal, ethical, and licensing governance framework.
