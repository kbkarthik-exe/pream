# PHASE 0: RISK, ETHICS & OPEN-SOURCE LICENSE AUDIT
**Project:** `C:\Users\acer\IMAGE`  
**Application Title:** A Multimodal Deep Learning Framework for Robust Detection of Synthetic Media (AICF)  
**Audit Date:** 2026-11-18  
**Auditor:** Principal AI Research Engineer & Compliance Specialist  
**Standards:** Open-Source Initiative (OSI), CFAA Compliance, Safe Harbor & AI Ethics Governance  

---

## 1. Executive Summary

This audit assesses the intellectual property, commercial licensing, privacy governance, and ethical liability risks of the AICF platform. AICF operates as a defensive digital cyber-forensics platform. To maintain strict legal compliance, all components must adhere to open-source software licenses, respect third-party terms of service, avoid non-sanctioned scraping, and refrain from making unsupportable scientific claims.

---

## 2. Open-Source Model & Software Licensing Audit

All local machine learning models, libraries, and frameworks integrated into AICF operate under verified permissive open-source licenses:

| Software / Model Component | Upstream Author / Project | License Type | Permitted Commercial Use | Attribution Requirement |
| :--- | :--- | :--- | :---: | :--- |
| **`roberta-base-openai-detector`** | OpenAI / HuggingFace | **MIT License** | **YES** | Include copyright notice in documentation |
| **`microsoft/deberta-v3-base`** | Microsoft Corporation | **MIT License** | **YES** | Include copyright notice in documentation |
| **`umm-maybe/AI-image-detector`** | HuggingFace Community | **Apache 2.0** | **YES** | Include Apache 2.0 notice & state modifications |
| **`google/vit-base-patch16-224`** | Google LLC | **Apache 2.0** | **YES** | Include Apache 2.0 notice & state modifications |
| **MesoNet-4 Architecture** | Darius Afchar et al. | **Research / MIT** | **YES** | Include academic paper citation in dossier |
| **OpenCV Headless (`cv2`)** | OpenCV Team | **Apache 2.0** | **YES** | Permissive library integration |
| **PyTorch (`torch`, `torchvision`)**| Meta AI / Linux Foundation| **BSD-3-Clause** | **YES** | Include standard 3-clause BSD notice |
| **Transformers & Tokenizers** | HuggingFace Inc. | **Apache 2.0** | **YES** | Include Apache 2.0 notice |
| **FastAPI & Starlette** | Tiangolo / Encode | **MIT License** | **YES** | Include MIT notice |
| **ReportLab PDF Engine** | ReportLab Inc. | **BSD License** | **YES** | Permissive open-source community edition |
| **Next.js & React** | Vercel Inc. / Meta Platforms | **MIT License** | **YES** | Standard permissive web stack |
| **Tailwind CSS v4** | Tailwind Labs Inc. | **MIT License** | **YES** | Permissive styling framework |

---

## 3. Third-Party Cloud API Terms of Service & Legal Governance

AICF interfaces with third-party cloud detection services through official REST APIs only. Strict legal rules govern these integrations:

### 3.1 Authorized Public APIs
1. **Hive AI (`thehive.ai`):**
   - **Access Model:** Authorized public developer REST API (`/api/v2/task/sync`).
   - **Compliance Guarantee:** Queries are made strictly using user-provided API keys. No shared or proxied enterprise tokens are bundled.
   - **Data Governance:** User payload is transmitted over HTTPS only when the user explicitly triggers cloud analysis with affirmative consent.
2. **GPTZero (`gptzero.me`):**
   - **Access Model:** Authorized public developer REST API (`/v2/predict/text`).
   - **Compliance Guarantee:** Adheres to word-length limits and official rate-limiting headers. Keys are stored in an encrypted vault.
3. **Copyleaks (`copyleaks.com`):**
   - **Access Model:** Authorized enterprise REST API.
   - **Compliance Guarantee:** Uses official OAuth/token endpoints with user-provided credentials.

### 3.2 Non-Sanctioned Integrations (Strictly Prohibited)
1. **Turnitin:**
   - **Barrier:** Turnitin does not provide a public developer REST API. Access is legally restricted to accredited educational institutions under enterprise LMS/LTI contracts.
   - **Risk Assessment:** Attempting to automate Turnitin through headless browser scraping or session hijacking violates the Computer Fraud and Abuse Act (CFAA) and Turnitin's Terms of Service.
   - **AICF Stance:** **REJECTED.** AICF honestly labels Turnitin as `NOT AVAILABLE`.
2. **Scribbr & ZeroGPT Scraping:**
   - **Barrier:** Protected by Cloudflare Turnstile, CAPTCHAs, and anti-bot systems.
   - **Risk Assessment:** Scraping ad-supported consumer frontends is brittle, illegal, and causes unpredictable downtime.
   - **AICF Stance:** **REJECTED.** No unofficial scrapers will ever be bundled.

---

## 4. Ethical Boundaries & Anti-Forensics Rejection

### 4.1 Refusal to Implement Text Humanization / Paraphrasing
- **The Evasion Hazard:** Consumer tools like Humbot AI monetize automated paraphrasing to defeat AI detectors.
- **The Forensic Principle:** An evidentiary cyber-forensics platform must preserve truth, attribution, and non-repudiation. Developing evasion or paraphrasing features undermines the scientific credibility of forensic findings.
- **AICF Stance:** AICF strictly refuses to build or bundle text humanization, paraphrasing, or watermarking-removal capabilities.

---

## 5. Scientific Accuracy & Liability Risk Management

### 5.1 No 100% Accuracy Claims
- **Statistical Fact:** All machine learning classifiers are probabilistic estimators. No AI detection model achieves 100% precision or recall across unseen generative distributions.
- **Liability Mitigation:**
  - All UI cards, API responses, and PDF dossiers must include explicit scientific disclaimers:
    > *"Forensic assessment scores are probabilistic indicators and do not constitute absolute mathematical proof. Findings should be corroborated by human analysts in the context of broader case investigations."*
  - Wilson score 95% confidence intervals are displayed to communicate statistical uncertainty.

### 5.2 Mandatory Inconclusive Thresholding
- If multi-model signals conflict (e.g., RoBERTa predicts 90% AI while linguistics indicates high human entropy), or if confidence falls in the indeterminate range ($0.35 - 0.65$), the system must return **`INCONCLUSIVE`**.
- Forcing a binary verdict when evidence is weak creates unacceptable false-positive risks for users.

---

## 6. Privacy & Data Governance (Air-Gap Protection)

1. **Local-First Default:** All primary analyses execute within the local workstation boundary with zero outbound network calls.
2. **Zero Plaintext Key Leakage:** External API credentials are encrypted with PBKDF2-HMAC-SHA256 (100,000 iterations) and masked (`hiv_••••••••1234`).
3. **Mandatory Consent Enforcing:** The backend strictly rejects outbound cloud verification requests with HTTP 400 if `user_consent=False`.
4. **Permanent Audio Scope Exclusion:** Synthetic voice and audio forensics remain permanently cancelled, preventing unintended regulatory exposure to biometric voice data.
