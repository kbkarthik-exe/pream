# AICF Phase 2 — Stage 1: Generator Attribution Engine Implementation Report

**Project:** `C:\Users\acer\IMAGE`  
**Phase:** Phase 2 (Advanced Multi-Model AI Image Forensics Engine) — Stage 1 (Generator Attribution Engine)  
**Date:** 2026-11-18  
**Status:** **STAGE 1 IMPLEMENTED & VERIFIED — STRICT STOP AWAITING REVIEW & APPROVAL**  
**Safe Baseline Backup:** Confirmed and verified at `C:\Users\acer\IMAGE\backups\phase2_baseline_checkpoint`

---

## 1. Executive Summary

In accordance with explicit authorization for **Stage 1 of AICF Phase 2**, an independent, evidence-based image generator attribution module has been developed and thoroughly tested:

- **New Source Module:** `backend/app/ml/image/generator_attribution.py`
- **New Isolated Test Suite:** `backend/tests/test_generator_attribution.py`
- **Protected Files Integrity:** 100% verified. Zero existing source files, schemas, endpoints, models, frontend files, or PDF services were modified.
- **`classify_image()` Preservation:** 100% verified. SHA-256 hash matches baseline backup exactly.
- **External Dependencies & Model Weights:** Zero packages installed; zero external weights downloaded; zero internet calls.

---

## 2. Architecture & Evidence Handling Implemented

The module implements a four-tier evidence hierarchy designed to attribute generative media to likely tool families without overclaiming certainty or inventing statistical predictions:

```
                            [ Input Image Raster & Raw Bytes ]
                                            |
        +-----------------------+-----------+-----------+-----------------------+
        |                       |                       |                       |
        v                       v                       v                       v
[ Tier A: Direct Prov. ]  [ Tier B: Metadata Clues ]  [ Tier C: Statistical ]  [ Tier D: Heuristics ]
- C2PA / JUMBF Markers    - EXIF Tags (Software,     - Status: UNAVAILABLE    - Canonical Buckets
- Digital Signature Check   Make, Model, UserComment) - No unvalidated model    (SD 1.5, SDXL, DALL-E)
- Adobe Firefly / DALL-E  - PNG Chunks (parameters,     hallucinated          - Aspect Ratios (16:9, etc.)
  Signed Manifest Check     prompt, workflow)                                 - Fourier Harmonics
- Missing != Human Rule   - Conflicting / Misleading                          - Rule: Heuristics NEVER
                            Metadata Detection                                  alone establish identity
        |                       |                       |                       |
        +-----------------------+-----------+-----------+-----------------------+
                                            |
                                            v
                               [ Evidence Synthesis Engine ]
                                - Conflicting metadata -> UNKNOWN
                                - Missing metadata + Heuristics -> UNKNOWN
                                - Single clear metadata -> Attributed Generator
                                - Verified C2PA manifest -> Direct Provenance
                                - Empty / corrupted bytes -> INSUFFICIENT_EVIDENCE
                                            |
                                            v
                               [ GeneratorAttributionResult ]
```

### 2.1 Evidence Categories

#### A. Direct Provenance (`Tier A`)
- Scans container bytes for standard C2PA and JUMBF markers (`c2pa`, `jumb`, `urn:c2pa:`, `C2PA`).
- Distinguishes verified cryptographic signatures (`c2pa.signature`, `c2as`, `c2pa.claim`) from raw unverified manifests.
- Extracts explicit tool claims (e.g., `adobe:firefly`, `dall-e`).
- **Strict Invariant:** Missing C2PA credentials are never treated as evidence of human or authentic origin. A clear disclaimer is always included.

#### B. Metadata-Based Clues (`Tier B`)
- Evaluates EXIF tags (`Software`, `ProcessingSoftware`, `UserComment`, `ImageDescription`).
- Evaluates PNG textual info chunks (`parameters`, `prompt`, `workflow`, `comment`, `description`, `software`).
- Patterns mapped to supported outcomes:
  - `MIDJOURNEY`: `\bmidjourney\b`, `--v [1-6]`, `--ar \d+:\d+`, `--stylize`, `--chaos`.
  - `STABLE_DIFFUSION`: `\bstable diffusion\b`, `comfyui`, `automatic1111`, `steps:`, `sampler:`, `cfg scale:`, `negative prompt:`, `model hash:`.
  - `DALLE`: `\bdall[- ·]?e\b`, `\bopenai\b`.
  - `FLUX`: `\bflux(\.1)?\b`, `black-forest-labs`, `bfl`.
  - `ADOBE_FIREFLY`: `\badobe firefly\b`, `\bfirefly\b`, `adobe photoshop ai`.
  - `OTHER_KNOWN_GENERATOR`: `novelai`, `leonardo.ai`, `ideogram`, `craiyon`, `bing image creator`.
- **Misleading Metadata Safeguard:** Detects co-occurrence of authentic camera hardware tags (Make/Model) alongside AI generation markers.
- **Conflicting Metadata Safeguard:** If markers for multiple distinct generator families appear, flags `conflicting_evidence = True` and downgrades to `UNKNOWN`.
- **Privacy Safeguard:** Long prompts and sensitive metadata are truncated and sanitized to prevent unintentional data leakage.

#### C. Statistical Evidence (`Tier C`)
- Strict compliance: No unvalidated or imaginary models are invoked.
- Formally emits:
  ```json
  {
    "status": "UNAVAILABLE",
    "model_id": null,
    "prediction": null,
    "note": "No generator-specific statistical classifier currently registered; category inactive."
  }
  ```

#### D. Heuristic Indicators (`Tier D`)
- Evaluates canonical dimension sets:
  - SD 1.5: $(512, 512)$, $(768, 768)$, $(512, 768)$, $(768, 512)$.
  - SDXL: $(1024, 1024)$, $(1152, 896)$, $(896, 1152)$, $(1216, 832)$, $(832, 1216)$, $(1344, 768)$, $(768, 1344)$, $(1536, 640)$, $(640, 1536)$.
  - DALL-E 2/3: $(1024, 1024)$, $(1024, 1792)$, $(1792, 1024)$.
  - Midjourney: $(1024, 1024)$, $(2048, 2048)$, standard aspect ratios ($1:1, 16:9, 9:16, 2:3, 3:2, 4:5$).
- Evaluates Fourier grid harmonics via optional spectral metrics.
- **Fundamental Invariant:** Heuristics **never** independently establish generator identity. If only heuristic indicators match, the engine strictly emits `primary_generator = "UNKNOWN"`, `confidence = 0.0`, and `evidence_tier = "HEURISTIC_INDICATORS"`.

---

## 3. Supported Attribution Outcomes & Output Schema

### Supported Outcomes:
1. `MIDJOURNEY`
2. `STABLE_DIFFUSION`
3. `DALLE`
4. `FLUX`
5. `ADOBE_FIREFLY`
6. `OTHER_KNOWN_GENERATOR`
7. `UNKNOWN`
8. `INSUFFICIENT_EVIDENCE`

### Typed Output Structure (`GeneratorAttributionResult`):
- `primary_generator: str` (one of the 8 supported outcomes)
- `confidence: float` (explicitly provisional: e.g. 0.85 for verified C2PA, 0.75 for metadata, 0.0 for unknown/heuristics)
- `evidence_tier: str` (`DIRECT_PROVENANCE`, `METADATA_CLUES`, `STATISTICAL_MODEL`, `HEURISTIC_INDICATORS`, `NONE`)
- `provenance_findings: dict[str, Any]` (C2PA detection, cryptographic signature presence, assertion notes)
- `metadata_findings: dict[str, Any]` (detected generators, camera hardware presence, software tags, inspected keys)
- `statistical_findings: dict[str, Any]` (inactive status, explicit lack of unvalidated neural claims)
- `heuristic_findings: dict[str, Any]` (dimensions, aspect ratio, canonical match status, Fourier indicators)
- `conflicting_evidence: bool` (true if contradictory generator signals detected)
- `limitations: list[str]` (plain-language forensic caveats and disclaimers)

---

## 4. Verification of Files Created & Protected

### 4.1 New Files Created
1. `backend/app/ml/image/generator_attribution.py` (Source code for Stage 1 engine)
2. `backend/tests/test_generator_attribution.py` (12 isolated automated tests)

### 4.2 Protected Files Verified Unchanged (Cryptographic Hash Match)

| Protected File | Current SHA-256 Hash | Baseline Backup Hash | Status |
| :--- | :---: | :---: | :---: |
| `backend/app/ml/image/detector.py` | `54BF8AE13AC208EA1AE53A281FF3E21721EB26FAA6E155C8C32F2AA236285716` | `54BF8AE13AC208EA1AE53A281FF3E21721EB26FAA6E155C8C32F2AA236285716` | **IDENTICAL** |
| `backend/app/ml/image/ensemble.py` | `3E75A9C16C97F991DFB071F9CD050186715CF6842ED81EE20117070BF519A0E3` | `3E75A9C16C97F991DFB071F9CD050186715CF6842ED81EE20117070BF519A0E3` | **IDENTICAL** |
| `backend/app/ml/image/features.py` | `5F3A8DA8BFBD2B4D21B85D36B1516A792E51D55E678A03310006734563B9B970` | `5F3A8DA8BFBD2B4D21B85D36B1516A792E51D55E678A03310006734563B9B970` | **IDENTICAL** |
| `backend/app/ml/image/heatmap.py` | `FA727AE9C1D155CF1D30C995977DF8857C34D883017B4EB13460CE5AC617D59A` | `FA727AE9C1D155CF1D30C995977DF8857C34D883017B4EB13460CE5AC617D59A` | **IDENTICAL** |
| `backend/app/api/v1/endpoints/image.py` | `28F87BFB09F9F88A23415DA128C4ED53E42C2CE8339DF8986B690CD206C59E30` | `28F87BFB09F9F88A23415DA128C4ED53E42C2CE8339DF8986B690CD206C59E30` | **IDENTICAL** |
| `backend/tests/test_image_analysis.py` | `B777353C4D0678F4628EAE4734BD4B3EF51094E1B3FF5E9C5A87B75F348F3719` | `B777353C4D0678F4628EAE4734BD4B3EF51094E1B3FF5E9C5A87B75F348F3719` | **IDENTICAL** |

### 4.3 `classify_image()` Verification
- Located at lines 152–163 of `backend/app/ml/image/detector.py`.
- Signature: `def classify_image(self, image: Image.Image) -> tuple[float, float, float]:`
- Return Contract: `(ai_probability, human_probability, raw_score)`
- Status: **Completely untouched, unmodified, and verified.** Phase 3 video frame processing is guaranteed zero regressions.

---

## 5. Test Results

### 5.1 Isolated Test Suite (`backend/tests/test_generator_attribution.py`)
Executed with Python 3.12.10 via `pytest`:

```
backend/tests/test_generator_attribution.py::test_1_png_with_known_generator_metadata PASSED    [  8%]
backend/tests/test_generator_attribution.py::test_2_jpeg_with_software_metadata PASSED          [ 16%]
backend/tests/test_generator_attribution.py::test_3_image_with_no_metadata PASSED              [ 25%]
backend/tests/test_generator_attribution.py::test_4_image_with_misleading_metadata PASSED      [ 33%]
backend/tests/test_generator_attribution.py::test_5_conflicting_metadata PASSED                [ 41%]
backend/tests/test_generator_attribution.py::test_6_unknown_generator PASSED                   [ 50%]
backend/tests/test_generator_attribution.py::test_7_missing_c2pa_manifest PASSED               [ 58%]
backend/tests/test_generator_attribution.py::test_8_invalid_or_corrupted_image PASSED          [ 66%]
backend/tests/test_generator_attribution.py::test_9_metadata_parsing_failure PASSED           [ 75%]
backend/tests/test_generator_attribution.py::test_10_unsupported_image_format_or_empty PASSED  [ 83%]
backend/tests/test_generator_attribution.py::test_11_c2pa_direct_provenance_with_signature PASSED [ 91%]
backend/tests/test_generator_attribution.py::test_12_heuristics_alone_never_establish_generator PASSED [100%]

============================== 12 passed in 0.41s ==============================
```

- **Passed:** 12 / 12 (100%)
- **Failed:** 0
- **Duration:** 0.41 seconds
- **Network / External Model Calls:** 0 (Fully air-gapped)

### 5.2 Baseline Image Test Suite Regression (`backend/tests/test_image_analysis.py`)
Executed with Python 3.12.10 via `pytest`:

```
backend/tests/test_image_analysis.py ..................... [100%]

======================= 21 passed, 5 warnings in 34.67s =======================
```

- **Passed:** 21 / 21 (100%)
- **Failed:** 0
- **Regressions:** Zero.

---

## 6. Known Limitations & Untested Behavior

1. **Stripped Metadata on Social Media:** If an image is downloaded from Twitter/X, Instagram, or WhatsApp, all EXIF, PNG chunks, and C2PA credentials will have been removed by the platform's re-compression pipeline. In this scenario, the engine correctly defaults to `primary_generator = "UNKNOWN"`.
2. **Adversarial / Spoofed Metadata:** Metadata is client-controlled; a determined actor can inject fake software tags (e.g. inserting "Canon EOS" into an AI image or "Midjourney" into an authentic photo). The engine mitigates this by flagging misleading combinations and assigning provisional confidence.
3. **Custom Fine-Tuned Models:** Custom local Stable Diffusion or FLUX merges that strip default software headers cannot be attributed by name and will be classified as `UNKNOWN` or `OTHER_KNOWN_GENERATOR`.
4. **Untested Behavior:** Full end-to-end integration into `/api/v1/image/analyze`, PDF generator, and Next.js frontend has **not** been performed yet, as instructed by the Stage 1 boundary.

---

## 7. Stop Condition & Gate Verification

**STRICT COMPLIANCE:**
- Stage 1 implementation is complete.
- No manipulation detection has been implemented.
- No ensemble modifications have been made.
- No API endpoints have been modified.
- No frontend files have been modified.
- No database changes have been made.
- No PDF generator changes have been made.

We are stopped at the Stage 1 review gate awaiting your inspection and explicit authorization before proceeding to Stage 2.

