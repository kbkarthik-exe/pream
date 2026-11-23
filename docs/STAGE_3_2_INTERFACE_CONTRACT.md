# AICF Phase 3 — Stage 3.2 Interface Contract & Pre-Implementation Review

**Document:** Stage 3.2 Architectural Specification & Interface Contract  
**Project:** `C:\Users\acer\IMAGE`  
**Review Date:** November 19, 2026  
**Status:** **PLANNING ONLY — NO PYTHON FILES OR TESTS CREATED/MODIFIED**  
**Final Recommendation:** **READY FOR IMPLEMENTATION**  

---

## 1. Subsystem Inspection & Exact Signatures

A comprehensive static analysis of the three core analysis modules and the security gate was performed.

### 1.1 Module A: Vision Transformer AI Detector
- **File:** `backend/app/ml/image/detector.py` (Lines 323–380)
- **Class / Instance:** `ImageForensicsDetector` / `image_detector`
- **Method Signature:**
  ```python
  def analyze_image_bytes(
      self,
      image_bytes: bytes,
      file_name: str = "uploaded_image",
  ) -> dict[str, Any]
  ```
- **Input Types:**
  - `image_bytes`: `bytes` (raw binary payload of the image)
  - `file_name`: `str` (optional container name, defaults to `"uploaded_image"`)
- **Output Type:** `dict[str, Any]` containing:
  - `status`: `"SUCCESS" | "INCONCLUSIVE" | "FAILED"`
  - `classification`: `"LIKELY AI-GENERATED" | "LIKELY HUMAN" | "INCONCLUSIVE"`
  - `confidence_score`: `float | None`
  - `ai_probability`: `float | None`
  - `human_probability`: `float | None`
  - `raw_score`: `float | None`
  - `model_name`: `str` (`"Swin-B+ViT"`)
  - `model_version`: `str` (`"2.0.0"`)
  - `file_hash`: `str` (SHA-256)
  - `file_name`: `str`
  - `file_size_bytes`: `int`
  - `image_width`: `int`
  - `image_height`: `int`
  - `image_format`: `str`
  - `processing_time_ms`: `float`
  - `evidence`: `list[dict[str, Any]]`
  - `provenance`: `dict[str, Any]`
  - `fft_features`: `dict[str, Any]`
  - `noise_features`: `dict[str, Any]`
  - `detector_scores`: `list[dict[str, Any]]`
  - `ensemble`: `dict[str, Any] | None`
  - `heatmap`: `dict[str, Any] | None`
  - `limitations`: `list[str]`
- **Exceptions & Fault Modes:** Catches internal decode errors; returns `status="FAILED"` for empty or unparseable bytes. Can raise `RuntimeError` if torch model fails unexpectedly.
- **Side Effects:** Loads Swin and ViT PyTorch weights on first call. High CPU/GPU memory footprint during forward pass.

### 1.2 Module B: Generator Attribution Engine
- **File:** `backend/app/ml/image/generator_attribution.py` (Lines 123–140)
- **Function Signature:**
  ```python
  def attribute_generator(
      image: Image.Image | None,
      raw_bytes: bytes,
      file_name: str | None = None,
  ) -> GeneratorAttributionResult
  ```
- **Input Types:**
  - `image`: `PIL.Image.Image | None` (optional pre-opened Pillow instance)
  - `raw_bytes`: `bytes` (raw binary file stream)
  - `file_name`: `str | None` (optional filename)
- **Output Type:** `GeneratorAttributionResult` (dataclass) with fields:
  - `generator_name`: `str | None`
  - `generator_family`: `str | None`
  - `matched_rules`: `list[str]`
  - `attribution_confidence`: `float` (0.0 to 1.0)
  - `evidence_snippets`: `list[str]`
  - `software_tag`: `str | None`
  - `prompt_clues`: `list[str]`
  - `workflow_graph_present`: `bool`
  - `c2pa_tool_attribution`: `str | None`
  - `outcome`: `"EXPLICIT_ATTRIBUTION" | "HEURISTIC_ATTRIBUTION" | "UNKNOWN_OR_NATURAL"`
  - `attribution_summary`: `str`
  - Method: `.to_dict() -> dict[str, Any]`
- **Exceptions & Fault Modes:** Self-contained; catches internal metadata errors safely.
- **Side Effects:** None. Pure inspection of binary metadata chunks and image EXIF dictionary.

### 1.3 Module C: Forensic Investigation & Manipulation Detector
- **File:** `backend/app/ml/image/forensics/evidence_fusion.py` (Lines 25–40)
- **Function Signature:**
  ```python
  def run_forensic_investigation(
      image: Image.Image | None,
      raw_bytes: bytes,
  ) -> ForensicReport
  ```
- **Input Types:**
  - `image`: `PIL.Image.Image | None` (optional pre-opened Pillow instance)
  - `raw_bytes`: `bytes` (raw binary file stream)
- **Output Type:** `ForensicReport` (dataclass) with fields:
  - `manipulation_verdict`: `str` (`"NO_MANIPULATION_EVIDENCE_DETECTED" | "SUSPECTED_SPLICING" | "SUSPECTED_INPAINTING" | "SUSPECTED_RETOUCHING" | "INSUFFICIENT_EVIDENCE"`)
  - `confidence`: `float` (0.0 to 1.0; explicitly typed as uncalibrated heuristic score)
  - `confidence_type`: `str` (`"HEURISTIC_SCORE"`)
  - `evidence_strength`: `str` (`"NONE" | "WEAK" | "MODERATE" | "STRONG" | "DEFINITIVE"`)
  - `findings`: `list[EvidenceFinding]`
  - `suspicious_regions`: `list[SuspiciousRegion]`
  - `localization_notes`: `list[str]`
  - `disclaimers`: `list[str]`
  - `c2pa_status`: `dict[str, Any]`
  - `metadata_status`: `dict[str, Any]`
  - `frequency_status`: `dict[str, Any]`
  - `noise_status`: `dict[str, Any]`
  - `ela_status`: `dict[str, Any]`
  - `cmfd_status`: `dict[str, Any]`
  - `analysis_coverage`: `dict[str, bool]`
  - `processing_time_ms`: `float`
- **Exceptions & Fault Modes:** Catches all sub-tier exceptions internally; returns `INSUFFICIENT_EVIDENCE` if unparseable.
- **Side Effects:** In-memory 2D FFT, Laplacian convolutions, ELA differential computation, and block-matching matching.

### 1.4 Pre-Decode Security Gate
- **File:** `backend/app/ml/image/forensics/security_hardening.py` (Lines 86–95)
- **Function Signature:**
  ```python
  def validate_image_security(
      raw_bytes: bytes,
      max_pixels: int = 16_777_216,
      max_dimension: int = 8192,
      max_file_bytes: int = 10_485_760,
  ) -> tuple[bool, str | None, dict[str, Any]]
  ```
- **Output Type:** `tuple[is_safe: bool, rejection_reason: str | None, telemetry: dict[str, Any]]`

---

## 2. Image Decoding Analysis & Protected Baseline Constraints

### 2.1 Does `ImageDetector.analyze_image_bytes()` Perform Its Own Image Decoding?
**YES.** Inspection of `backend/app/ml/image/detector.py` lines 358–363 reveals:
```python
# 2. Decode and validate raster image safely with Pillow
try:
    pil_img = Image.open(io.BytesIO(image_bytes))
    pil_img.load()
    img_format = (pil_img.format or "UNKNOWN").upper()
    width, height = pil_img.size
```
Furthermore, `ImageForensicsDetector.analyze()` (lines 316–319) demonstrates that if passed a `PIL.Image`, it immediately converts it back to bytes:
```python
elif isinstance(payload, Image.Image):
    buf = io.BytesIO()
    payload.save(buf, format="PNG")
    return self.analyze_image_bytes(buf.getvalue(), file_name="image.png")
```

### 2.2 Is True Global Single-Decode Possible Without Modifying Protected Files?
**NO.** Because `detector.py` is a protected baseline file that strictly requires `raw_bytes` and unconditionally performs its own internal `Image.open()`, true global single-decode cannot be forced onto `detector.py` without violating the baseline preservation rule.

### 2.3 Explicit Architectural Decision for Stage 3.2
1. **Protected Detector Untouched:** We will **never** modify `detector.py` or force unsafe monkeypatching. `detector.py` continues to receive `raw_bytes`.
2. **Inter-Module Single-Decode Sharing:** The orchestrator will open `pil_img = Image.open(io.BytesIO(raw_bytes))` **once** and pass that identical loaded instance to both:
   - `attribute_generator(image=pil_img, raw_bytes=raw_bytes)`
   - `run_forensic_investigation(image=pil_img, raw_bytes=raw_bytes)`
3. Both `attribute_generator` and `run_forensic_investigation` inspect `if image is not None:` and reuse the pre-opened raster and its `.info` metadata dictionary, eliminating 2 out of the 3 redundant image decodes.

---

## 3. Typed Result Contract

The unified orchestrator (`UnifiedImagePipeline.analyze()`) will return a strongly typed dataclass structure (serializable to dict via `.to_dict()`):

### 3.1 Dataclass Contract Specification
```python
from dataclasses import dataclass, field, asdict
from typing import Any

@dataclass
class DimensionAResult:
    status: str                          # "SUCCESS" | "INCONCLUSIVE" | "FAILED"
    classification: str                  # "LIKELY AI-GENERATED" | "LIKELY HUMAN" | "INCONCLUSIVE"
    confidence_score: float | None       # [0.0, 1.0] calibrated probability
    ai_probability: float | None         # [0.0, 1.0]
    human_probability: float | None      # [0.0, 1.0]
    raw_score: float | None              # [0.0, 1.0]
    model_name: str                      # "Swin-B+ViT"
    model_version: str                   # "2.0.0"
    detector_scores: list[dict[str, Any]]
    ensemble: dict[str, Any] | None
    heatmap: dict[str, Any] | None
    fft_features: dict[str, Any]
    noise_features: dict[str, Any]
    evidence: list[dict[str, Any]]
    limitations: list[str]
    processing_time_ms: float
    error: str | None = None

@dataclass
class AttributionResult:
    status: str                          # "SUCCESS" | "FAILED" | "SKIPPED"
    outcome: str                         # "EXPLICIT_ATTRIBUTION" | "HEURISTIC_ATTRIBUTION" | "UNKNOWN_OR_NATURAL"
    generator_name: str | None           # e.g. "Midjourney", "DALL-E 3", "Flux.1"
    generator_family: str | None         # e.g. "Diffusion", "Autoregressive"
    attribution_confidence: float        # [0.0, 1.0]
    software_tag: str | None
    prompt_clues: list[str]
    matched_rules: list[str]
    evidence_snippets: list[str]
    workflow_graph_present: bool
    c2pa_tool_attribution: str | None
    attribution_summary: str
    processing_time_ms: float
    error: str | None = None

@dataclass
class DimensionBResult:
    status: str                          # "SUCCESS" | "FAILED" | "SKIPPED"
    manipulation_verdict: str            # "NO_MANIPULATION_EVIDENCE_DETECTED" | "SUSPECTED_SPLICING" | ...
    heuristic_score: float               # [0.0, 1.0]
    confidence_type: str                 # "HEURISTIC_SCORE" (NEVER "CALIBRATED_PROBABILITY")
    evidence_strength: str               # "NONE" | "WEAK" | "MODERATE" | "STRONG" | "DEFINITIVE"
    findings: list[dict[str, Any]]
    suspicious_regions: list[dict[str, Any]]
    localization_notes: list[str]
    disclaimers: list[str]
    c2pa_status: dict[str, Any]
    analysis_coverage: dict[str, bool]
    processing_time_ms: float
    error: str | None = None

@dataclass
class UnifiedAnalysisResult:
    file_hash: str                       # SHA-256 of raw bytes
    file_name: str
    file_size_bytes: int
    image_width: int
    image_height: int
    image_format: str
    overall_status: str                  # "SUCCESS" | "PARTIAL" | "FAILED"
    dimension_a: DimensionAResult
    attribution: AttributionResult
    dimension_b: DimensionBResult
    total_processing_time_ms: float
    analysis_coverage: dict[str, bool]
    skipped_modules: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
```

---

## 4. Input Validation & Defense in Depth

The orchestrator guarantees that invalid or unvetted byte streams **never** reach downstream analysis code:

1. **Gate Pre-Condition:** `validate_image_security(raw_bytes, max_pixels, max_dimension, max_file_bytes)` is the very first line executed in `UnifiedImagePipeline.analyze()`.
2. **Immediate Rejection:** If `is_safe is False`, `UnifiedImagePipeline.analyze()` raises `ImageSecurityException(rejection_reason)`.
3. **Execution Blockade:** If the security check fails:
   - `ImageDetector.analyze_image_bytes` is **NEVER** called.
   - `attribute_generator` is **NEVER** called.
   - `run_forensic_investigation` is **NEVER** called.
   - Pillow raster decompression is **NEVER** performed.

---

## 5. Strict Independence Invariant Rules

To prevent forensic hallucinations, cognitive bias, and mathematical distortion, the orchestrator enforces five programmatic invariant rules:

| Invariant Rule | Architectural Enforcement |
|---|---|
| **Rule 1: No Forensic-to-AI Modulation** | Manipulation findings (`SUSPECTED_SPLICING`, `SUSPECTED_INPAINTING`, `SUSPECTED_RETOUCHING`) in Dimension B **never** increment, decrement, or adjust $P(\text{AI})$ in Dimension A. |
| **Rule 2: No Attribution-to-AI Modulation** | The presence of a generator attribution tag (e.g. Midjourney) in the attribution module **never** artificially forces $P(\text{AI})$ in Dimension A. Each dimension reports its own independent evidence. |
| **Rule 3: Absence of Seams != Proof of AI or Authenticity** | A `NO_MANIPULATION_EVIDENCE_DETECTED` finding in Dimension B **never** implies that the image is fully authentic camera footage or fully AI-generated. |
| **Rule 4: Explicit Heuristic Labeling** | `dimension_b.confidence_type` is permanently hardcoded to `"HEURISTIC_SCORE"`. It is forbidden from using `"CALIBRATED_PROBABILITY"`. |
| **Rule 5: C2PA Proof of Signer != Proof of Visual Truth** | C2PA verification confirms that a cryptographic credential was issued by a specific entity; it does **not** certify that the depicted scene is authentic reality. |

---

## 6. Deterministic Degradation & Failure Isolation

If any single analysis module raises an unhandled exception or encounters an error, the orchestrator isolates the failure to that module and continues executing the remainder of the pipeline:

```
                                  [ Uploaded Bytes ]
                                          │
                            [ validate_image_security ]
                                 /                \
                             [FAIL]              [PASS]
                               │                   │
                        [Raise SecErr]     [Single Safe Decode]
                                                   │
                   ┌───────────────────────────────┼───────────────────────────────┐
                   │                               │                               │
                   ▼                               ▼                               ▼
          [ Dimension A: AI ]            [ Attribution Engine ]          [ Dimension B: Forensics ]
          ┌─────────────────┐            ┌─────────────────┐             ┌─────────────────┐
          │ try: analyze()  │            │ try: attribute()│             │ try: forensic() │
          │ except: FALLBACK│            │ except: FALLBACK│             │ except: FALLBACK│
          └─────────────────┘            └─────────────────┘             └─────────────────┘
                   │                               │                               │
                   └───────────────────────────────┼───────────────────────────────┘
                                                   │
                                     [ Assemble Unified Payload ]
                   - overall_status = "SUCCESS" if all 3 ok, else "PARTIAL"
                   - skipped_modules records any failing subsystem
                   - warnings records sanitized error details
```

### Fallback Defaults:
- **Dimension A Failure:** `status="FAILED"`, `classification="INCONCLUSIVE"`, `confidence_score=0.0`, `error=sanitized_msg`.
- **Attribution Failure:** `status="FAILED"`, `outcome="UNKNOWN_OR_NATURAL"`, `attribution_confidence=0.0`, `error=sanitized_msg`.
- **Dimension B Failure:** `status="FAILED"`, `manipulation_verdict="INSUFFICIENT_EVIDENCE"`, `heuristic_score=0.0`, `error=sanitized_msg`.

---

## 7. Mock-Based Unit Test Matrix (16 Cases)

To ensure rapid, repeatable test execution without reloading the heavy Swin/ViT model weights on every test run, `backend/tests/test_unified_pipeline.py` will use mock-isolated fixtures:

| # | Test Name | Target Behavior | Expected Result |
|---|---|---|---|
| 1 | `test_01_orchestrator_initialization_defaults` | Instantiation without arguments | Uses default `image_detector` |
| 2 | `test_02_orchestrator_successful_valid_image` | Normal JPEG execution with all submodules | `overall_status == "SUCCESS"`, all 3 dimensions populated |
| 3 | `test_03_dimension_decoupling_splicing_does_not_affect_p_ai` | Dimension B reports SPLICING | `dim_a.ai_probability` unchanged |
| 4 | `test_04_dimension_decoupling_absence_of_seams_does_not_affect_p_ai` | Dimension B reports NO_MANIPULATION | `dim_a.classification` unchanged |
| 5 | `test_05_dimension_decoupling_attribution_does_not_affect_p_ai` | Attribution reports Midjourney | `dim_a.ai_probability` unchanged |
| 6 | `test_06_single_decode_pil_image_shared_between_attribution_and_forensics` | Verify object identity of `image` argument | `id(attr_img) == id(forensic_img)` |
| 7 | `test_07_c2pa_signed_manifest_does_not_claim_visual_authenticity` | C2PA signed valid manifest | Disclaimers present, no truth claim |
| 8 | `test_08_heuristic_score_explicitly_labeled` | Dimension B confidence score inspection | `confidence_type == "HEURISTIC_SCORE"` |
| 9 | `test_09_dimension_a_failure_graceful_degradation` | Detector raises `RuntimeError("OOM")` | `dim_a.status == "FAILED"`, B & Attr succeed, overall="PARTIAL" |
| 10 | `test_10_attribution_failure_graceful_degradation` | Attribution raises `ValueError` | `attr.status == "FAILED"`, A & B succeed, overall="PARTIAL" |
| 11 | `test_11_dimension_b_failure_graceful_degradation` | Forensics raises `MemoryError` | `dim_b.status == "FAILED"`, A & Attr succeed, overall="PARTIAL" |
| 12 | `test_12_empty_bytes_rejected_before_downstream_calls` | Input `b""` | Raises `ImageSecurityException`, downstream mocks not called |
| 13 | `test_13_decompression_bomb_rejected_before_downstream_calls` | 10000x10000 PNG IHDR | Raises `ImageSecurityException`, downstream mocks not called |
| 14 | `test_14_unsupported_format_rejected_before_downstream_calls` | GIF format input stream | Raises `ImageSecurityException`, downstream mocks not called |
| 15 | `test_15_timing_telemetry_collected` | Total processing time check | `total_ms >= dim_a_ms + dim_b_ms`, all non-negative |
| 16 | `test_16_serialization_to_dict_schema_compatible` | `.to_dict()` invocation | All values serializable (dicts, lists, primitives) |

---

## 8. Import Architecture, Shared State, and Thread Safety

### 8.1 Circular Import Analysis
- `unified_pipeline.py` will import from:
  - `backend.app.ml.image.detector`
  - `backend.app.ml.image.generator_attribution`
  - `backend.app.ml.image.forensics.evidence_fusion`
  - `backend.app.ml.image.forensics.security_hardening`
- **Result:** None of these four modules import `unified_pipeline.py`.
- **Export Discipline:** We will **not** modify `backend/app/ml/image/__init__.py` (which is a protected baseline file). Users/callers will import directly via `from backend.app.ml.image.unified_pipeline import UnifiedImagePipeline`.
- **Verdict:** **ZERO risk of circular imports.**

### 8.2 Shared State & Thread Safety
- `UnifiedImagePipeline` holds only a reference to `ImageDetector`.
- All methods are re-entrant and stateless per-analysis.
- Image objects are opened inside context managers (`with Image.open(...) as pil_img`) ensuring deterministic disposal.
- PyTorch forward inference under `torch.no_grad()` is thread-safe on CPU/CUDA.
- **Verdict:** **Thread-safe; no unsafe global state.**

---

## 9. Final Recommendation

### **READY FOR IMPLEMENTATION**

All architectural questions, signature mismatches, decode constraints, and failure modes have been rigorously evaluated and resolved. Implementation can proceed with high confidence and zero disruption to the existing baseline.
