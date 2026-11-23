# PHASE 0: HUMBOT AI TECHNICAL FEATURE & REVERSE-ENGINEERING AUDIT
**Project:** `C:\Users\acer\IMAGE`  
**Target Platform:** Humbot AI (`https://humbot.ai/`)  
**Developer Documentation & API Portal:** `https://humbot.ai/api/`  
**Audit Date:** 2026-11-18  
**Auditor:** Principal AI Research Engineer & Reverse Engineering Specialist  
**Methodology:** Clean-room technical inspection of public pages, developer documentation, and public API schemas  

---

## 1. Executive Summary

Humbot AI is a commercial web service primarily marketed as an "Undetectable AI Humanizer & All-in-One Multi-Detector AI Checker." Its business model targets students, marketers, and web content creators seeking to bypass automated AI content detection systems (such as Turnitin, GPTZero, and Copyleaks) by automatically paraphrasing LLM-generated text.

As part of this conversion funnel, Humbot offers an aggregated "Multi-Model AI Checker" UI that presents side-by-side detection badges for multiple commercial engines.

Our reverse-engineering investigation highlights a fundamental operational divide:
1. **Commercial Purpose:** Humbot is designed for *detection evasion* (anti-forensics). In contrast, AICF is designed for *forensic attribution and truth verification* (defensive digital forensics).
2. **API Reality:** Humbot's published developer API is strictly a *humanization/paraphrasing API*. It does **not** provide a standalone detection API for evaluating raw text.
3. **Third-Party Detector Claims:** Several detectors prominently featured in Humbot's marketing (specifically **Turnitin**) do not offer public third-party commercial APIs. Claims of direct Turnitin verification in consumer web tools rely on internal heuristic proxy models or fragile browser automation wrappers that violate terms of service.

---

## 2. Publicly Verifiable Technical Features

### 2.1 The "All-in-One Multi-Detector" Workflow
- **Input Modality:** Web-based text entry accepting pasted payloads or file uploads (`.txt`, `.docx`, `.pdf`). Displays live character and word counters.
- **Aggregated Checker Grid:** Evaluates input text against up to 9 commercial AI detectors:
  - **GPTZero**
  - **Copyleaks**
  - **Turnitin**
  - **Winston AI**
  - **ZeroGPT**
  - **Crossplag**
  - **Scribbr**
  - **Writer**
  - **Sapling**
- **Output States:** Each detector card renders a simplified three-state status:
  - `AI Detected` (Red)
  - `Human-like / Passed` (Green)
  - `Mixed / Uncertain` (Yellow)
- **Bypass Probability Score:** Calculates an aggregate score representing the proportion of detectors that classified the text as human.

### 2.2 Text Humanization & Paraphrasing Engine
- **Core Technology:** Sequence-to-sequence fine-tuned language models prompted to disrupt characteristic LLM statistical signatures:
  - Eliminates low-entropy token sequences.
  - Artificially modulates sentence lengths to increase burstiness ($\sigma / \mu$).
  - Introduces informal syntax, colloquialisms, and varied transitional phrasing.
- **Rewriting Tiers:**
  - **Quick Mode:** Shallow lexical replacement using synonyms.
  - **Enhanced Mode:** Syntactic clause reordering and passive-to-active restructuring.
  - **Advanced Mode:** Deep semantic reconstruction designed to evade enterprise classifiers.
- **Claimed Language Support:** Publicly claims support for 50+ languages, though quality and bypass efficacy are heavily concentrated in English.

### 2.3 Limitations & Absence of Forensic Defensibility
- **Zero Evidentiary Rigor:** Humbot provides no cryptographic input ledgers (no SHA-256 hashes), no sentence-level token probability distributions, no mathematical entropy equations, and no exportable chain-of-custody PDF reports.
- **Evaluation Bias:** The multi-detector display is intentionally configured as a sales mechanism to demonstrate the "before and after" efficacy of its humanizer product.

---

## 3. Developer API Specification & Technical Limitations

### 3.1 Official Developer API Contracts
Humbot exposes an asynchronous REST API (`v2.0.0`):
- **Base URL:** `https://api.humbot.ai`
- **Authentication:** `Authorization: Bearer <HUMBOT_API_KEY>`
- **Task Submission (`POST /api/humbot/v2/create`):**
  - *Request Payload:*
    ```json
    {
      "text": "Artificial intelligence architectures demonstrate unprecedented capabilities in synthesizing syntax...",
      "mode": "advanced",
      "language": "en"
    }
    ```
  - *Response Schema:*
    ```json
    {
      "code": 200,
      "task_id": "hb_task_89214710",
      "status": "processing"
    }
    ```
- **Task Retrieval (`GET /api/humbot/v2/retrieve?task_id=hb_task_89214710`):**
  - *Response Schema:*
    ```json
    {
      "code": 200,
      "task_id": "hb_task_89214710",
      "status": "completed",
      "output_text": "AI models have shown amazing skills in putting words together...",
      "detection_preview": {
        "gptzero": "human",
        "turnitin": "human"
      }
    }
    ```

### 3.2 Key Technical Finding: No Standalone Detection API
Humbot does **not** provide an API endpoint of the form `POST /api/v1/detect` that allows a third-party developer to submit raw text and receive multi-detector scores without consuming words in their humanization engine. Calling Humbot's API rewrites the text, which is antithetical to forensic evidence preservation.

---

## 4. Reality of Marketed Third-Party Detectors

| Marketed Detector | Public Developer API? | Official Access Model | Cost / Barriers | Feasibility in AICF |
| :--- | :---: | :--- | :--- | :--- |
| **RoBERTa / DeBERTa** | **YES (Open Source)** | HuggingFace Hub (Apache 2.0 / MIT) | **$0.00 (Self-hosted on CPU/CUDA)** | **IMPLEMENTED & VERIFIED** in AICF |
| **Linguistic Profiler**| **YES (Open Source)** | Deterministic Python Math | **$0.00 (Offline, zero dependency)** | **IMPLEMENTED & VERIFIED** in AICF |
| **GPTZero** | **YES (Official)** | Public REST API (`api.gptzero.me`) | Paid tier (~$0.0003/word); API key | **CONFIGURATION REQUIRED** (Cloud Adapter) |
| **Copyleaks** | **YES (Official)** | Enterprise REST API (`api.copyleaks.com`)| Paid packages (~$0.005/page); API key | **CONFIGURATION REQUIRED** (Cloud Adapter) |
| **Turnitin** | **NO** | Enterprise Institutional LMS (LTI) | Restricted to universities; no public API | **NOT AVAILABLE (Cannot legally integrate)** |
| **Scribbr** | **NO** | Web Consumer Reseller for Turnitin | Pay-per-document portal; Cloudflare gate | **NOT AVAILABLE (Scraping prohibited)** |
| **ZeroGPT** | **NO Official API** | Ad-supported consumer portal | Frequent layout changes; anti-bot CAPTCHAs | **NOT AVAILABLE (Unreliable & non-compliant)** |
| **Sapling AI** | **YES (Official)** | Public REST API (`api.sapling.ai`) | Paid subscription ($25+/mo); API key | **CONFIGURATION REQUIRED** (Feasible) |
| **Winston AI** | **YES (Official)** | Public REST API | Paid credits; API key required | **CONFIGURATION REQUIRED** (Feasible) |

---

## 5. Architectural Implementation Mapping for AICF

```
┌─────────────────────────────────┬─────────────────────────────────┬─────────────────────────────────┐
│ HUMBOT AI CONSUMER FEATURE      │ AICF LOCAL REPLACEMENT          │ AICF OPTIONAL CLOUD ADAPTER     │
├─────────────────────────────────┼─────────────────────────────────┼─────────────────────────────────┤
│ Proprietary Black-Box Classifier│ Pretrained RoBERTa + DeBERTa-v3 │ (None needed; local is primary) │
│ Unexposed Perplexity Metrics    │ Shannon Token Entropy Math ($H$)│ (Not exposed by Humbot)         │
│ Hidden Burstiness Logic         │ Sentence Length Variance ($\sigma/\mu$)│ (Not exposed by Humbot)    │
│ Unexposed Vocabulary Diversity  │ Type-Token Ratio (TTR) Engine   │ (Not exposed by Humbot)         │
│ Multi-Detector Grid Display     │ Multi-Detector Local Consensus  │ Official GPTZero / Copyleaks    │
│ Text Humanization / Paraphrasing│ INTENTIONALLY REJECTED (Evasion)│ (Evasion defeats forensics)     │
│ Cryptographic Verification      │ SHA-256 Non-Repudiation Ledgers │ (Not provided by Humbot)        │
│ Chain-of-Custody PDF Reporting  │ ReportLab NumberedCanvas Engine │ (Not provided by Humbot)        │
└─────────────────────────────────┴─────────────────────────────────┴─────────────────────────────────┘
```

### Strategic Conclusions for AICF
1. **Defensive Integrity:** AICF must never implement text humanization, paraphrasing, or watermarking-removal features. Doing so violates forensic chain-of-custody principles.
2. **Local Multi-Detector Engine:** AICF achieves genuine multi-detector consensus by running multiple independent models locally:
   - **RoBERTa Sequence Classifier** (`roberta-base-openai-detector`)
   - **DeBERTa v3 Classifier** (`microsoft/deberta-v3-base`)
   - **Deterministic Linguistic Profiler** (Shannon entropy, burstiness, TTR, 3-grams)
3. **Authorized Cloud Corroboration:** AICF enables analysts to optionally configure official public APIs (**GPTZero** and **Copyleaks**) using their own API credentials, secured in an encrypted vault and triggered only with explicit consent.
