# AICF — STEP 05 Implementation Plan: Real AI Image Detection Engine

## Overview
Implement a production-grade, genuine AI image detection system in the existing AICF platform, continuing from Steps 1–4 without rebuilding or degrading existing capabilities.

---

## 1. Phase Breakdown

### Phase 1: Audit & Foundation Verification (Completed)
- **Frontend Stack**: Next.js 16 + React 19 + TypeScript + Tailwind CSS v4.
- **Backend Stack**: Python 3.12 + FastAPI + SQLAlchemy 2 + SQLite/PostgreSQL + Pydantic v2 + Argon2id.
- **Model Stack**: PyTorch 2.14.1, Hugging Face Transformers 5.20.2, Pillow 13.0.0, NumPy 2.5.4.
- **Model Selected**: `umm-maybe/AI-image-detector` (Swin Transformer for Image Classification, fine-tuned on synthetic vs. real imagery, CC-BY-4.0).
- **Execution**: Verified CPU execution and forward pass with torch inference mode.
- **Baseline Git Checkpoint**: Committed baseline snapshot `c436e31`.

### Phase 2: AI Image Forensics Interface
- Complete `frontend/src/app/dashboard/image/page.tsx` with black-and-gold forensic aesthetic.
- Drag-and-drop zone, file browser, file size and pixel dimension calculations, image preview thumbnail, clear/remove actions.
- Multi-stage telemetry indicators ("Decoding raster payload", "Executing Swin Transformer inference", "Fourier FFT analysis", "Provenance inspection").
- Structured forensic result panels, provenance card, evidence breakdown, save-to-case action, and historical investigation drawer.

### Phase 3 & 4: Image Forensics Engine Service & Analysis Results
- Create `backend/app/ml/image/features.py` for deterministic spatial & frequency forensics:
  - 2D Fast Fourier Transform (FFT) high-frequency spectral distribution.
  - Local noise residual variance (Error Level Analysis / block variance).
  - EXIF metadata parser, generative AI prompt indicators (SD/Midjourney/DALL-E), and C2PA markers.
- Create `backend/app/ml/image/detector.py` implementing `BaseDetector`:
  - Singleton model loader for `umm-maybe/AI-image-detector`.
  - Calibrated decision thresholds: `LIKELY AI-GENERATED` (>= 0.70), `LIKELY HUMAN` (<= 0.30), `INCONCLUSIVE` (between 0.30 and 0.70 or low-res gate).
  - Robust error handling returning `BLOCKED` on missing weights without fake data.

### Phase 5 & 6: Metadata, Provenance, Security & Privacy
- Parse EXIF, PNG chunks, and C2PA markers while keeping provenance distinct from model probability.
- Server-side validation: Max 15MB file size, Max 16MP dimensions, magic-byte format validation (JPEG, PNG, WebP).
- In-memory decoding with Pillow; no permanent storage of user images; cryptographic SHA-256 for audit trails.
- Strict authentication via `get_current_user` and user-scoped data access.

### Phase 7: Database & History Persistence
- Create `backend/app/models/image_analysis.py` (`ImageAnalysisRecord`).
- Link to `User` model and integrate with `/dashboard/stats` and case reports archive.
- Expose `POST /api/v1/image/analyze`, `GET /api/v1/image/history`, and `GET /api/v1/image/{id}`.

### Phase 8 & 9: Testing & Evaluation
- Implement automated test suite `backend/tests/test_image_analysis.py` covering all 15 required test scenarios.
- Run frontend linter, TypeScript compiler, Next.js build, and backend Pytest suite (confirming zero regressions in Step 4 text detection).
- Document model card, license, hardware requirements, and evaluation metrics.
