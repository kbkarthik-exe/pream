# AICF Phase 3 — Stage 3.1 Known Limitations & Remaining Roadmap

**Document:** Stage 3.1 Known Limitations, Architecture Constraints, and Phase 3 Remaining Roadmap  
**Target:** `C:\Users\acer\IMAGE`  
**Status:** Documented and Controlled  

---

## 1. Known Limitations of Stage 3.1 Ingestion Gate

### 1.1 WebP VP8X Extended Container Fallback
- **Limitation:** The custom pre-decode sniffer in `security_hardening.py` parses `VP8 ` (lossy) and `VP8L` (lossless) chunks directly from raw bytes. WebP files utilizing the extended chunk header (`VP8X`) return `None` from the pre-decode sniffer.
- **Security Mitigation:** When the sniffer returns `None`, execution safely falls back to Pillow's lazy `Image.open()`. Because `Image.MAX_IMAGE_PIXELS = 16,777,216` is strictly globally enforced, decompression bombs inside VP8X chunks are blocked by Pillow before raster decompression.
- **Future Enhancement:** Add explicit 24-bit canvas dimension parsing for `VP8X` chunks in a subsequent hardening cycle.

### 1.2 Formats Restricted by Policy
- **Policy:** By design, only `JPEG`, `PNG`, and `WEBP` (and `MPO` multi-picture JPEG extensions) are permitted for forensic ingestion.
- **Rejected Formats:** Vector formats (SVG), animated GIF, TIFF, BMP, and raw sensor formats (CR2, NEF, ARW) are rejected with `HTTP 422 UNSUPPORTED_FORMAT`.
- **Reason:** SVG carries XML/XSS/SSRF attack surfaces; multi-frame GIF and uncompressed TIFF present excessive raster decompression attack surfaces.

### 1.3 Vision Model Cold-Start Latency on Windows CPU
- **Observation:** On Windows AMD64 running on CPU without dedicated GPU acceleration, the first inference test that loads the Swin Transformer and ViT PyTorch weights takes approximately 22 to 25 seconds (and up to 130s on initial cold disk cache).
- **Mitigation in Unit Testing:** The newly added `test_stage3_1_security_gate.py` mocks `image_detector.analyze_image_bytes` so all 20 security tests execute in **3.84 seconds** without reloading PyTorch weights. The 21 production tests in `test_image_analysis.py` run real inference sequentially in **29.47 seconds**.

---

## 2. Phase 3 Remaining Integration Roadmap

With Stage 3.1 (Secure Ingestion Gate) verified and passing, the remaining stages of Phase 3 are:

```
┌─────────────────────────────────────────────────────────────────┐
│ Stage 3.1: Secure Ingestion Gate (COMPLETED & VERIFIED)         │
│  - Pre-decode sniffing, decompression bomb defense, format gate │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 3.2: Unified Pipeline Orchestrator                        │
│  - Create `unified_pipeline.py` orchestrating:                  │
│    * Dimension A: Swin+ViT AI Generation Detection              │
│    * Stage 1: Generator Attribution Engine                      │
│    * Dimension B: Forensic Investigation & Tampering Detection  │
│  - Shared single decoded PIL image (eliminates 3x re-decodes)   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 3.3: Extended Result Schemas & DB Schema Compatibility   │
│  - Extend `ImageAnalysisResponse` with dual verdicts            │
│  - Maintain 100% backwards compatibility for existing clients   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 3.4: Production API Route Integration                     │
│  - Connect `unified_pipeline.py` to `image.py` endpoint         │
│  - Persist dual verdicts and provenance in SQLite record        │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 3.5: PDF Generation Service Update                        │
│  - Render generator attribution badges and forensic tables      │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 3.6: Frontend Dashboard Integration                       │
│  - Dual verdict display, attribution cards, tampering heatmaps  │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 3.7: Final End-to-End Verification Audit                  │
│  - Full regression across backend, API, DB, PDF, and UI         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Current State & Safety Status
- No production files modified other than `backend/app/api/v1/endpoints/image.py`.
- No baseline files modified (`detector.py`, `ensemble.py`, `features.py`, `heatmap.py` untouched).
- Full 81 regression tests passing with 0 failures.
- Baseline backup untouched and preserved at `backups/phase2_baseline_checkpoint/`.
- Pre-Stage 3.1 backup untouched and preserved at `backups/stage3_1_pre_ingestion/image.py`.
