# STEP 0: HUMBOT AI REVERSE ENGINEERING & FEATURE AUDIT REPORT

**Target Platform:** Humbot AI  
**Official Website:** https://humbot.ai/  
**Developer Documentation & API:** https://humbot.ai/api/  
**Model Focus:** Multi-Detector AI Text Analysis & Text Humanization  
**Audit Date:** November 15, 2026  
**Auditor:** Principal AI Research Engineer & Reverse Engineering Specialist  

---

## 1. Executive Summary

Humbot AI is an online software platform primarily marketed as an "Undetectable AI Humanizer & Multi-Model AI Checker." Its primary consumer value proposition is rewriting/paraphrasing AI-generated text (from models such as ChatGPT, Claude, and Gemini) so that it bypasses commercial AI detection systems.

As part of this workflow, Humbot prominently features an aggregated "Multi-Detector AI Checker" panel on its user interface. The marketing claims that users can test text against numerous leading detectors simultaneously—including **GPTZero, Copyleaks, Turnitin, Winston AI, ZeroGPT, Crossplag, Scribbr, Writer, and Sapling**.

Our technical and architectural audit reveals a critical distinction between marketing presentation and software reality:
1. **Commercial Role:** Humbot is an evasion and paraphrasing platform, whereas AICF is an evidentiary digital-forensics platform.
2. **API Reality:** Humbot's official public API (v2.0.0) is exclusively for text humanization tasks (`/create` and `/retrieve`). Humbot does **not** provide a standalone, developer-facing multi-detector checking API.
3. **Third-Party Detector Integrations:** Several detectors advertised in Humbot's marketing (notably **Turnitin**) do not offer public third-party commercial APIs. Access to Turnitin is legally restricted to accredited academic institutions via Learning Management Systems (LMS/LTI integrations). Platforms that claim to show Turnitin scores either rely on internal heuristic proxy models trained to mimic Turnitin's score distributions or run non-sanctioned scraping wrappers subject to rate-limiting and Cloudflare bot challenges.

---

## 2. Humbot AI Feature Architecture & Workflow Analysis

### 2.1 The "All-in-One AI Checker" Interface
- **Marketed Capability:** Ingests a text snippet and presents side-by-side verdict cards for up to 9 distinct detection engines.
- **Visual Presentation:** Each detector card displays a classification state:
  - `AI Detected` (Red badge)
  - `Human-like` / `Passed` (Green badge)
  - `Mixed / Uncertain` (Yellow badge)
- **Aggregated Consensus:** Generates an overall bypass confidence percentage indicating the likelihood that the text will evade detection across standard automated screeners.

### 2.2 Text Humanization & Paraphrasing Engine
- **Core Technology:** Fine-tuned sequence-to-sequence transformers and instruction-tuned LLMs prompted to:
  - Disrupt characteristic LLM syntactic regularities (uniform perplexity and burstiness).
  - Inject lexical variability, informal idioms, and varied clause lengths.
  - Retain semantic meaning while modifying sentence structure.
- **Rewriting Modes:**
  - **Quick Mode:** Surface-level synonym replacement and clause reordering.
  - **Enhanced Mode:** Balanced restructuring designed for standard detectors (GPTZero, ZeroGPT).
  - **Advanced Mode:** Deep structural rewriting aimed at advanced enterprise checkers (Originality.ai, Turnitin).
- **Multilingual Support:** Supports rewriting across 50+ languages.

### 2.3 Evidentiary & Forensic Output
- **Absence of Forensic Rigor:** Humbot does **not** provide cryptographic SHA-256 input ledgers, token-level probability attributions, mathematical entropy calculations, or defensible forensic chain-of-custody PDF documentation.
- **Commercial Intent:** Designed for students, SEO copywriters, and marketers seeking to publish LLM-generated content without penalties.

---

## 3. Technical API Reverse Engineering & Third-Party Realities

### 3.1 Humbot Official Developer API (v2.0.0)
Humbot exposes an asynchronous REST API for developers to automate text humanization:

- **Protocol:** HTTPS REST
- **Base URL:** `https://api.humbot.ai` (or partner integration gateway)
- **Authentication:** `Authorization: Bearer <HUMBOT_API_KEY>`
- **Task Submission Endpoint:** `POST /api/humbot/v2/create`
  - *Payload:* `{"text": "...", "mode": "advanced", "language": "en"}`
  - *Response:* `{"code": 200, "task_id": "hb_task_89214710"}`
- **Task Retrieval Endpoint:** `GET /api/humbot/v2/retrieve?task_id=hb_task_89214710`
  - *Response:* `{"status": "completed", "output_text": "...", "detection_preview": {"gptzero": "human", "turnitin": "human"}}`

**Key Limitation:** The API is structured to consume words for paraphrasing. You cannot query Humbot's API solely to get independent detector scores on raw text without passing through their humanization pipeline.

### 3.2 Third-Party Detector Availability & Commercial Status

| Target Detector | Public Developer API Available? | Licensing / Access Model | Cost / Restrictions | Feasibility in AICF |
| :--- | :---: | :--- | :--- | :--- |
| **RoBERTa / DeBERTa** | **YES (Open Source)** | HuggingFace Hub (Apache 2.0 / MIT) | **$0.00 (Self-hosted on CPU/CUDA)** | **IMPLEMENTED & VERIFIED** in AICF |
| **Deterministic NLP (Entropy/Burstiness)** | **YES (Open Source)** | Local Python Math / SciPy | **$0.00 (Offline, Deterministic)** | **IMPLEMENTED & VERIFIED** in AICF |
| **GPTZero** | **YES (Official)** | Proprietary REST API (`api.gptzero.me`) | Paid subscription (~$0.0003/word); API Key required | **CONFIGURATION REQUIRED** (Cloud Adapter) |
| **Copyleaks** | **YES (Official)** | Proprietary REST API (`api.copyleaks.com`) | Paid credit packages (~$0.005/page); API Key required | **CONFIGURATION REQUIRED** (Cloud Adapter) |
| **Sapling AI** | **YES (Official)** | Proprietary REST API (`api.sapling.ai`) | Paid monthly tier ($25+/mo); API Key required | **CONFIGURATION REQUIRED** (Cloud Adapter) |
| **Turnitin** | **NO** | Enterprise Institutional LMS Only (LTI) | Restricted to universities; no public developer API | **NOT PUBLICLY AVAILABLE** |
| **Scribbr** | **NO** | Web Consumer Front-End for Turnitin | Per-document fee; anti-bot Cloudflare protection | **NOT PUBLICLY AVAILABLE** |
| **Winston AI** | **YES (Official)** | Proprietary REST API | Paid monthly credits; API Key required | **CONFIGURATION REQUIRED** (Cloud Adapter) |
| **ZeroGPT** | **NO Official API** | Unofficial scraper / ad-supported portal | Scraping breaks frequently; anti-bot CAPTCHA | **NOT IMPLEMENTED** (Violates ToS) |

---

## 4. Humbot AI Pricing & Economics

| Tier | Word Limit | Monthly Price | Annual Price | Effective Cost / Word |
| :--- | :--- | :--- | :--- | :--- |
| **Free Trial** | ~80 – 300 words total | $0.00 | $0.00 | N/A (Evaluator only) |
| **Basic** | ~3,000 words / month | $12.00 / mo | $9.99 / mo | ~$0.0040 / word |
| **Pro** | ~30,000 words / month | $29.00 / mo | $19.99 / mo | ~$0.0009 / word |
| **Unlimited** | Unlimited / Fair-Use | $59.00 / mo | $39.99 / mo | Fixed monthly cost |
| **API Packages** | 50,000 – 1,000,000+ words | Custom metered | Custom | Pay-as-you-go |

---

## 5. Comparative Audit: Humbot AI vs. AICF Platform

| Capability | Humbot AI | AICF Platform (`C:\Users\acer\IMAGE`) | Status in AICF |
| :--- | :--- | :--- | :---: |
| **Neural AI Text Classifier** | Internal blackbox | `roberta-base-openai-detector` (125M params on CPU) | **IMPLEMENTED AND VERIFIED** |
| **Linguistic Telemetry** | Hidden / Unexposed | Shannon entropy, TTR lexical diversity, repeated 3-grams | **IMPLEMENTED AND VERIFIED** |
| **Burstiness Modeling** | Proprietary metric | Coefficient of variation ($\sigma / \mu$) across sentence lengths | **IMPLEMENTED AND VERIFIED** |
| **Evidentiary Signal Attribution** | None (Binary badge) | Explicit indicator list explaining forensic drivers | **IMPLEMENTED AND VERIFIED** |
| **Cryptographic Audit Ledger** | None | SHA-256 hash calculation and database persistence | **IMPLEMENTED AND VERIFIED** |
| **Forensic PDF Export** | None | ReportLab two-pass NumberedCanvas with ISO timestamps | **IMPLEMENTED AND VERIFIED** |
| **Multi-Model Local Ensemble** | Single internal model | Dual RoBERTa + DeBERTa-v3 consensus ensemble | **PARTIALLY IMPLEMENTED** (RoBERTa verified; DeBERTa ready) |
| **Commercial Cloud Adapters** | Bundled internally | Adapter slots for GPTZero, Copyleaks, Sapling | **CONFIGURATION REQUIRED** |
| **Turnitin Direct Verification** | Inferred / Simulated | Not integrated (Commercial enterprise barrier) | **NOT PUBLICLY AVAILABLE** |
| **Text Humanization / Evasion** | Core feature (3 modes) | Intentionally excluded (Forensic integrity requirement) | **NOT IMPLEMENTED** |

---

## 6. Strategic Recommendations for AICF

1. **Reject Evasion / Humanization:**
   - AICF is an AI Cyber-Forensics laboratory, not an evasion service. Preserving forensic integrity and non-repudiation requires refusing to implement text rewriters that defeat watermarking or deceive detectors.

2. **Implement a $0-Cost Local Multi-Model Ensemble:**
   - Instead of relying on fragile cloud scrapers or expensive metered APIs, AICF can provide genuine multi-model text consensus locally on CPU/CUDA:
     - **Detector A (Baseline):** Pretrained `roberta-base-openai-detector` (Currently **IMPLEMENTED AND VERIFIED**).
     - **Detector B (Secondary SOTA):** Fine-tuned `microsoft/deberta-v3-base` or DistilRoBERTa synthetic text classifier running locally.
     - **Detector C (Statistical):** Deterministic Perplexity & Burstiness Profiler using unigram/bigram token distribution.
   - Display a consensus breakdown card in the UI showing:
     - RoBERTa Confidence: `94.2%`
     - DeBERTa Confidence: `91.8%`
     - Statistical Burstiness: `0.14 (Uniform / AI-characteristic)`
     - Overall Ensemble Consensus: `LIKELY AI-GENERATED (93.0%)`

3. **Optional Cloud Corroboration Hub:**
   - Provide an optional settings panel where enterprise investigators can input their own API keys for **GPTZero** or **Copyleaks**.
   - If an API key is present, AICF asynchronously queries the cloud provider and embeds the official vendor score into the forensic evidence ledger and PDF report.
   - If no key is configured, the local ensemble operates with zero external dependencies and zero recurring cost.
