# AICF Phase 3 — Stage 3.2 Implementation Plan
## Unified Pipeline Orchestrator (Backend ML)

**Document:** Stage 3.2 Architectural Specification & Implementation Roadmap  
**Target Directory:** `C:\Users\acer\IMAGE`  
**Current Baseline Status:** Stage 3.1 PASS (81/81 regression tests passing, 8/8 baseline files verified bit-for-bit via SHA-256)  
**Execution Mode:** **PLANNING ONLY — NO CODE OR TEST MODIFICATIONS**  

---

## 1. Stage Objective & Measurable Acceptance Criteria

### 1.1 Objective
Create an independent, unified pipeline orchestrator module at:
`backend/app/ml/image/unified_pipeline.py`

This module acts as the central coordinator for image authenticity analysis. It receives verified image bytes, manages a single safe PIL Image decode lifecycle, and orchestrates three distinct analysis engines without allowing cross-contamination between synthetic generation probability and manipulation detection:

1. **Dimension A:** Existing AI Synthetic Media Detection (`ImageDetector.analyze_image_bytes`)
2. **Stage 1 Engine:** Generator Attribution Engine (`attribute_generator`)
3. **Dimension B:** Forensic Investigation & Manipulation Detection (`run_forensic_investigation`)

### 1.2 Measurable Acceptance Criteria
1. **Isolated Execution:** `unified_pipeline.py` is implemented as a standalone orchestrator without modifying `detector.py`, `ensemble.py`, `features.py`, `heatmap.py`, `hive_adapter.py`, or `generator_attribution.py`.
2. **Single-Decode Efficiency:** `pil_img` is decoded and loaded **once** after security validation and shared across Stage 1 attribution and Stage 2.4 forensics.
3. **Strict Dimension Decoupling (Non-Negotiable):**
   - $P(\text{AI})$ from Dimension A is **never** modified by findings in Dimension B.
   - The absence of manipulation seams in Dimension B **never** alters the AI synthetic classification.
   - Heuristic scores in Dimension B are explicitly labeled as `HEURISTIC_SCORE` (uncalibrated).
4. **Execution Fault Tolerance:** If any single component (e.g. C2PA parsing or CMFD) raises an unexpected exception, the orchestrator catches it, records a structured limitation/warning, marks that sub-module as `SKIPPED` or `FAILED`, and allows remaining pipelines to complete.
5. **Deterministic Serialization:** Produces a standardized dictionary ready for Pydantic validation (in Stage 3.3).
6. **Test Coverage:** Dedicated test suite `backend/tests/test_unified_pipeline.py` passes with >= 15 tests verifying orchestration, dimension decoupling, single-decode reuse, graceful degradation, and execution telemetry.
7. **Zero Baseline Regressions:** All 81 existing regression tests continue to pass 100%.
8. **Bit-for-Bit Hash Preservation:** All 8 protected baseline checkpoint files match their SHA-256 baseline hashes.

---

## 2. Exact Files Expected to Change

### 2.1 New Files to Create
| File Path | Purpose |
|---|---|
| `backend/app/ml/image/unified_pipeline.py` | Standalone unified analysis orchestrator and result packager |
| `backend/tests/test_unified_pipeline.py` | Focused unit and integration tests for the orchestrator |
| `docs/STAGE_3_2_IMPLEMENTATION_REPORT.md` | Verification report upon completion of Stage 3.2 |

### 2.2 Files Explicitly NOT Modified in Stage 3.2
| File Path | Protection Status | Reason |
|---|---|---|
| `backend/app/ml/image/detector.py` | **PROTECTED BASELINE** | Baseline ML inference backbone |
| `backend/app/ml/image/ensemble.py` | **PROTECTED BASELINE** | Baseline ensemble aggregation logic |
| `backend/app/ml/image/features.py` | **PROTECTED BASELINE** | Baseline FFT & Laplacian feature extractor |
| `backend/app/ml/image/heatmap.py` | **PROTECTED BASELINE** | Baseline Grad-CAM and ELA heatmaps |
| `backend/app/ml/image/hive_adapter.py` | **PROTECTED BASELINE** | Baseline external cloud adapter |
| `backend/app/ml/image/__init__.py` | **PROTECTED BASELINE** | Baseline module exports |
| `backend/app/ml/image/generator_attribution.py` | **STAGE 1 DELIVERABLE** | Preserved Stage 1 attribution algorithms |
| `backend/app/ml/image/forensics/*` | **STAGE 2 DELIVERABLE** | Preserved Stage 2 forensic algorithms |
| `backend/app/api/v1/endpoints/image.py` | **STAGE 3.1 ACTIVE** | Integrated in Stage 3.4 (not in Stage 3.2) |
| `backend/app/schemas/image_analysis.py` | **DEFERRED TO STAGE 3.3** | Pydantic schema extensions |
| `backend/app/models/image_analysis.py` | **DEFERRED TO STAGE 3.3** | SQLAlchemy ORM models |
| `backend/app/services/pdf_generator.py` | **DEFERRED TO STAGE 3.5** | PDF reporting service |
| `frontend/*` | **DEFERRED TO STAGE 3.6** | UI dashboard components |

---

## 3. Proposed Implementation Steps in Dependency Order

```
[ Step 0: Pre-Flight Safety & Checkpoint Verification ]
                         │
                         ▼
[ Step 1: Create Orchestrator (unified_pipeline.py) ]
  ├─ Ingestion Security Verification
  ├─ Single PIL Image Decode & Context Manager
  ├─ Dimension A Execution (ImageDetector)
  ├─ Stage 1 Execution (attribute_generator)
  ├─ Dimension B Execution (run_forensic_investigation)
  └─ Decoupled Result Assembly & Telemetry Packaging
                         │
                         ▼
[ Step 2: Author Dedicated Tests (test_unified_pipeline.py) ]
  ├─ Test Dimension Decoupling (Rule 1 & Rule 2)
  ├─ Test Single PIL Image Reuse
  ├─ Test Fault Isolation (Sub-Module Exception Resilience)
  ├─ Test Telemetry & Execution Timing
  └─ Test Heuristic Score Type Labeling
                         │
                         ▼
[ Step 3: Sequential Test Execution ]
  ├─ Run test_unified_pipeline.py in isolation
  └─ Verify execution time and memory bounds
                         │
                         ▼
[ Step 4: Full 96+ Test Regression Run ]
  ├─ 12 Stage 1 Tests
  ├─ 28 Stage 2.4 Tests
  ├─ 21 Baseline Image Tests
  ├─ 20 Stage 3.1 Security Gate Tests
  └─ 15+ New Stage 3.2 Orchestrator Tests
                         │
                         ▼
[ Step 5: Independent SHA-256 Hash Audit ]
                         │
                         ▼
[ Step 6: Complete Documentation & Reporting ]
```

---

## 4. Architectural Details of `UnifiedImagePipeline`

### 4.1 Orchestrator Class Design
```python
class UnifiedImagePipeline:
    """Orchestrates multi-dimensional AI image analysis and forensic investigation."""

    def __init__(self, detector: ImageDetector | None = None) -> None:
        self.detector = detector or image_detector

    def analyze(
        self,
        raw_bytes: bytes,
        file_name: str = "uploaded_image",
        max_pixels: int = 16_777_216,
        max_dimension: int = 8192,
        max_file_bytes: int = 10_485_760,
    ) -> dict[str, Any]:
        """Executes secure, single-decode, two-dimensional forensic analysis."""
        ...
```

### 4.2 Data Flow & Exception Isolation
```python
# 1. Security Gate
is_safe, reason, telemetry = validate_image_security(raw_bytes, max_pixels, max_dimension, max_file_bytes)
if not is_safe:
    raise ImageSecurityException(reason or "Validation failed")

# 2. Single Safe Decode
with Image.open(io.BytesIO(raw_bytes)) as pil_img:
    pil_img.load()

    # 3. Dimension A: Synthetic Media Detection (Protected Backbone)
    try:
        dim_a_result = self.detector.analyze_image_bytes(raw_bytes, file_name=file_name)
    except Exception as exc:
        dim_a_result = self._fallback_dimension_a(exc)

    # 4. Stage 1: Generator Attribution
    try:
        attribution_result = attribute_generator(pil_img, raw_bytes, file_name=file_name).to_dict()
    except Exception as exc:
        attribution_result = self._fallback_attribution(exc)

    # 5. Dimension B: Forensics & Manipulation Detection
    try:
        forensics_report = run_forensic_investigation(pil_img, raw_bytes)
        dim_b_result = asdict(forensics_report)
    except Exception as exc:
        dim_b_result = self._fallback_dimension_b(exc)

# 6. Decoupled Assembly
return self._assemble_unified_payload(dim_a_result, attribution_result, dim_b_result, timing_telemetry)
```

---

## 5. Security Considerations and Abuse Cases

1. **Decompression Bomb Defense:** Ensured at the very entry point via `validate_image_security`. Zero raster decompression occurs if pre-decode dimensions exceed 16.7 MP or single axis exceeds 8192 px.
2. **Resource Exhaustion Defense:** If CMFD (Copy-Move Forgery Detection) receives a large image, it operates under the 4,000-candidate block threshold established in Stage 2.4.
3. **Information Leakage Prevention:** Errors inside sub-modules are caught, sanitized into structured telemetry messages, and never expose memory pointers (`0x...`), internal filesystem paths (`C:\`, `backend/app`), or raw stack traces.
4. **Adversarial Mismatch Defense:** Images disguised with invalid extensions or misleading MIME headers are processed solely by container signature and validated raster dimensions.
5. **Memory Containment:** `pil_img` is loaded within a strict Python context manager (`with Image.open(...) as pil_img`), ensuring underlying buffer handles are closed upon analysis completion.

---

## 6. Unit, Integration, and Regression Test Strategy

### 6.1 New Focused Tests (`test_unified_pipeline.py`)
1. `test_orchestrator_initialization_defaults`
2. `test_orchestrator_successful_valid_image` (with mocked detector to run in < 10 ms)
3. `test_orchestrator_dimension_decoupling_splicing_does_not_affect_p_ai`
4. `test_orchestrator_dimension_decoupling_absence_of_seams_does_not_affect_ai_verdict`
5. `test_orchestrator_single_image_decode_reused_in_attribution_and_forensics`
6. `test_orchestrator_c2pa_manifest_does_not_certify_factual_authenticity`
7. `test_orchestrator_heuristic_score_explicitly_labeled`
8. `test_orchestrator_dimension_a_failure_graceful_degradation`
9. `test_orchestrator_attribution_failure_graceful_degradation`
10. `test_orchestrator_dimension_b_failure_graceful_degradation`
11. `test_orchestrator_security_exception_propagation_on_invalid_input`
12. `test_orchestrator_decompression_bomb_rejected_instantly`
13. `test_orchestrator_empty_stream_rejected_instantly`
14. `test_orchestrator_timing_telemetry_collected`
15. `test_orchestrator_coverage_metrics_reported`

### 6.2 Full Regression Suite
- Run all 12 Stage 1 tests
- Run all 28 Stage 2.4 tests
- Run all 21 Baseline Image API tests
- Run all 20 Stage 3.1 Security Gate tests
- Run all 15+ Stage 3.2 Orchestrator tests
- **Target:** **96+ tests passing, 0 failures.**

---

## 7. Required Baseline Backups and Integrity Checks

Before creating `unified_pipeline.py`:
1. Verify `backups/phase2_baseline_checkpoint/` exists and is intact.
2. Verify `backups/stage3_1_pre_ingestion/` exists and is intact.
3. Compute SHA-256 for all 8 protected baseline files and verify 100% matches.
4. Verify all 81 tests pass before beginning implementation.

---

## 8. Rollback Strategy

Because Stage 3.2 creates a new independent file (`unified_pipeline.py`) and does not modify production endpoints or baseline files, rollback is trivial and non-destructive:

```powershell
# 1. Remove Stage 3.2 deliverables
Remove-Item -Force "backend\app\ml\image\unified_pipeline.py"
Remove-Item -Force "backend\tests\test_unified_pipeline.py"

# 2. Confirm 81-test baseline passes
backend\venv\Scripts\python.exe -m pytest backend/tests/test_generator_attribution.py backend/tests/test_image_forensics_stage2.py backend/tests/test_image_analysis.py backend/tests/test_stage3_1_security_gate.py -q
```

---

## 9. Risks, Unresolved Questions, and Explicit Stop Conditions

### 9.1 Risks and Mitigations
| Risk | Severity | Mitigation |
|---|---|---|
| **Windows CPU Latency during Real Tests** | High | Mock `ImageDetector.analyze_image_bytes` in unit tests of `unified_pipeline.py` so unit tests execute in milliseconds. Run real end-to-end inference only in integration tests. |
| **Process Interruption during Test Runs** | Medium | Execute test suites sequentially with single-worker processes; avoid parallel test runners (`pytest-xdist`). |
| **Coupling Leaks** | Critical | Enforce programmatic decoupling checks in unit tests asserting `math.isclose(res['ai_probability'], original_p_ai)` regardless of manipulation findings. |

### 9.2 Explicit Stop Conditions
STOP immediately if:
1. Any of the 8 protected baseline files differs by even 1 byte from the checkpoint.
2. Any of the 81 existing regression tests fails.
3. A proposal arises to modify `detector.py`, `ensemble.py`, `features.py`, or `heatmap.py`.
4. An external package installation appears necessary.
5. Memory allocation during image orchestration exceeds 250 MB on standard test fixtures.
