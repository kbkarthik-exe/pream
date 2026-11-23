# A Multimodal Deep Learning Framework for Robust Detection of Synthetic Media

> **Detect. Analyze. Explain. Verify.**  
> **Official Title:** A Multimodal Deep Learning Framework for Robust Detection of Synthetic Media  
> **Platform Label:** Synthetic Media Detection Framework

An enterprise-grade digital forensics and synthetic content intelligence framework designed to analyze text, images, and videos for potential human or AI generation. Built with a decoupled, high-assurance architecture, the platform pairs deep forensic telemetry with accessible explanations and transparent confidence boundaries.

---

## 1. System Architecture

```
AICF Platform Architecture
├── Frontend (Next.js 16 + React 19 + TypeScript + Tailwind CSS v4)
│   ├── Black-and-Gold forensic UI system with responsive mobile drawer
│   ├── Authentication Pages: /login and /register
│   ├── Protected Main Dashboard: /dashboard (guarded with AuthGuard)
│   ├── Forensic Modality Modules:
│   │   ├── /dashboard/text   (AI Text Forensics & Synthetics Detection — VERIFIED)
│   │   ├── /dashboard/image  (AI Image Forensics & Generative Synthesis — VERIFIED)
│   │   ├── /dashboard/video  (AI Video Detection & Deepfake Analysis — PARTIAL / CONFIGURATION REQUIRED)
│   │   └── /dashboard/audio  (CANCELLED — AI Audio Detection Engine)
│   ├── Forensic Case Archive: /dashboard/reports (Filterable by modality, real DB records)
│   ├── Analyst Profile & Security: /dashboard/settings (Identity & credential updates)
│   ├── Reusable Result Card: ForensicResultCard (5 taxonomy classes, ethical confidence gates)
│   ├── Client state: AuthProvider React Context & dynamic Navbar/Sidebar
│   └── Next.js API rewrites proxying /api/v1 to FastAPI backend
│
├── Backend (Python 3.12 + FastAPI + Pydantic v2 + SQLAlchemy 2)
│   ├── Authentication Endpoints:
│   │   ├── POST  /api/v1/auth/register (Rate-limited, Argon2id)
│   │   ├── POST  /api/v1/auth/login    (Rate-limited, Argon2id, HttpOnly cookie)
│   │   ├── POST  /api/v1/auth/logout   (DB revocation, cookie deletion)
│   │   ├── GET   /api/v1/auth/me       (Protected profile endpoint)
│   │   ├── GET   /api/v1/auth/status   (Session check endpoint)
│   │   └── PATCH /api/v1/auth/profile  (Analyst profile & password updates)
│   ├── Dashboard & Resource Endpoints:
│   │   ├── GET   /api/v1/dashboard/stats (Real user-scoped counts from DB)
│   │       ├── Forensics Endpoints:
│   │   ├── POST  /api/v1/text/analyze       (Real RoBERTa + linguistic features, VERIFIED)
│   │   ├── GET   /api/v1/text/history       (User-scoped text history, VERIFIED)
│   │   ├── GET   /api/v1/text/analyses/{id}/pdf (Download authenticated Text PDF report, VERIFIED)
│   │   ├── POST  /api/v1/image/analyze      (Real Swin ViT + FFT + Laplacian, VERIFIED)
│   │   ├── GET   /api/v1/image/history      (User-scoped image history, VERIFIED)
│   │   ├── GET   /api/v1/image/{id}/pdf     (Download authenticated Image PDF report, VERIFIED)
│   │   └── GET   /api/v1/reports/{id}/pdf   (Download authenticated Case/Video PDF report, VERIFIED)
│   ├── Forensic PDF Generation Service:
│   │   ├── backend/app/services/pdf_generator.py (ReportLab 5.1.0 in-memory streaming engine)
│   │   ├── Signature AICF Obsidian & Gold brand styling (#0B0C10, #D4AF37, #12141A)
│   │   ├── Dynamic NumberedCanvas two-pass pagination ("Page X of Y")
│   │   └── Strict XML/HTML sanitization & mandatory scientific disclaimer blocks
│   ├── Sliding-window rate limiter with Retry-After headers
│   ├── Cryptographic session token generation (256-bit entropy, SHA-256 hashed in DB)
│   └── PostgreSQL async engine (asyncpg) with automated local SQLite fallback
│
├── Modular AI/ML Layer (Decoupled from API routes)
│   ├── BaseDetector interface with mandatory scientific disclaimers
│   ├── app/ml/text/   (RoBERTa-base-openai-detector + lexical statistics — VERIFIED)
│   ├── app/ml/image/  (Swin ViT + 2D FFT + Laplacian residual + C2PA/EXIF — VERIFIED)
│   ├── app/ml/video/  (Scaffolded BaseDetector interface — PARTIAL / CONFIGURATION REQUIRED)
│   └── app/ml/audio/  (CANCELLED — AI Audio Detection Engine)
│
└── Database (PostgreSQL / async SQLAlchemy)
    ├── users table            (Argon2id password hashes, analyst profiles)
    ├── user_sessions table    (Hashed tokens, expiration, IP & user-agent audit)
    ├── text_analyses table    (User-scoped text records, SHA-256, RoBERTa + lexical metrics)
    ├── image_analyses table   (User-scoped image records, SHA-256, Swin ViT + FFT + Laplacian)
    └── forensic_reports table (User-scoped investigation cases & audits)
```

---

## 2. Authentication & Forensic Security Rules

1. **Argon2id Password Hashing**: Passwords are never stored in plaintext. They are hashed using Argon2id (`time_cost=2`, `memory_cost=65536`, `parallelism=2`, `hash_len=32`).
2. **Server-Managed Sessions**: Session tokens are cryptographically generated (256 bits). Only the SHA-256 hash of the token is persisted in the database. Cookies are transmitted with `HttpOnly=True`, `SameSite=Lax`, and `Secure` in production.
3. **Cross-Account Authorization Isolation**: All forensic investigations are strictly scoped to the authenticated analyst. Accessing another user's private report is rejected with HTTP 403 Forbidden.
4. **Zero-Mock Statistics Integrity**: Dashboard statistics display strictly verified database counts (0 if empty). Simulated counts, random confidence scores, or fake AI predictions are strictly prohibited.
5. **Detection Result Contract**: When detection engines are unconfigured, the platform renders status `BLOCKED` with a prominent disclosure banner: *"Detection engine not configured yet."*
6. **Probabilistic Nature of Detection**: No detector is 100% accurate. All platform outputs present confidence distributions, feature signals, and methodological disclaimers rather than binary claims of certainty.

---

## 3. Directory Structure

```
IMAGE/
├── .gitignore                    # Comprehensive root gitignore
├── README.md                     # Platform documentation and execution guide
├── frontend/                     # Next.js TypeScript application
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx        # Root Layout with AuthProvider and Navbar
│   │   │   ├── page.tsx          # Platform landing page & modality showcase
│   │   │   ├── globals.css       # Obsidian & gold theme tokens & grid pattern
│   │   │   ├── login/page.tsx    # Live login page with validation & error handling
│   │   │   ├── register/page.tsx # Analyst registration page with password strength meter
│   │   │   └── dashboard/
│   │   │       ├── layout.tsx    # Responsive black-and-gold sidebar & drawer layout
│   │   │       ├── page.tsx      # Overview with real DB statistics & quick modules
│   │   │       ├── text/page.tsx # AI Text Detection & Perplexity analysis
│   │   │       ├── image/page.tsx# AI Image Detection & Frequency forensics
│   │   │       ├── video/page.tsx# AI Video Detection & Deepfake analysis
│   │   │       ├── audio/page.tsx# AI Audio Detection & Synthetic voice analysis
│   │   │       ├── reports/page.tsx# Case reports archive & modality filter
│   │   │       └── settings/page.tsx# Settings & Account Profile editor
│   │   ├── components/
│   │   │   ├── auth-guard.tsx    # Route protection guard with forensic loader
│   │   │   ├── navbar.tsx        # Dynamic navigation bar with auth status and logout
│   │   │   └── forensic-result-card.tsx # Reusable forensic result card & honest disclaimers
│   │   └── lib/
│   │       ├── api.ts            # Typed API client with credentials inclusion
│   │       └── auth-context.tsx  # React Context for authentication lifecycle
│   ├── next.config.ts            # Next.js configuration with backend API rewrites
│   ├── package.json              # Frontend dependencies and scripts
│   └── tsconfig.json             # TypeScript compiler settings
└── backend/                      # FastAPI Python application
    ├── app/
    │   ├── api/
    │   │   ├── deps.py           # get_current_user dependency with cookie validation
    │   │   └── v1/
    │   │       ├── endpoints/
    │   │       │   ├── auth.py   # Register, login, logout, me, status, profile patch
    │   │       │   ├── dashboard.py# User-scoped database metrics
    │   │       │   ├── health.py # Operational health check endpoint
    │   │       │   └── reports.py# User-scoped reports with modality filtering
    │   │       └── router.py     # Aggregated v1 router
    │   ├── core/
    │   │   ├── config.py         # Pydantic BaseSettings & environment configs
    │   │   ├── rate_limiter.py   # Sliding-window rate limiter
    │   │   └── security.py       # Argon2id hasher and token utilities
    │   ├── db/
    │   │   ├── base.py           # DeclarativeBase for SQLAlchemy models
    │   │   ├── init_db.py        # Database schema initialization
    │   │   └── session.py        # Async engine (PostgreSQL/SQLite) & get_db dependency
    │   ├── models/
    │   │   ├── report.py         # ForensicReport model
    │   │   ├── session.py        # UserSession model
    │   │   └── user.py           # User model
    │   ├── schemas/
    │   │   ├── auth.py           # Pydantic validation schemas for auth & profile
    │   │   ├── dashboard.py      # Dashboard statistics response schema
    │   │   ├── health.py         # HealthResponse schema
    │   │   └── report.py         # Report schemas
    │   ├── ml/                   # Modular AI/ML forensics architecture
    │   │   ├── base.py           # BaseDetector abstract contract
    │   │   ├── text/             # Text analysis module package
    │   │   ├── image/            # Image analysis module package
    │   │   ├── video/            # Video analysis module package
    │   │   └── audio/            # Audio analysis module package
    │   └── main.py               # FastAPI entrypoint, lifespan init, and CORS
    ├── tests/
    │   ├── conftest.py           # Hermetic test database & client fixtures
    │   ├── test_auth.py          # Comprehensive authentication & authorization tests (9 tests)
    │   ├── test_dashboard.py     # Real stats, accumulation, isolation & profile tests (5 tests)
    │   ├── test_health.py        # Service health check tests (2 tests)
    │   ├── test_text_analysis.py # Real RoBERTa inference, length & bounds, isolation tests (11 tests)
    │   ├── test_image_analysis.py# Real Swin ViT, FFT/Laplacian, dimensions & format tests (15 tests)
    │   └── test_integration_e2e_security.py # Full lifecycle E2E, horizontal isolation & rate limit (3 tests)
    ├── .env.example              # Environment variables template
    ├── pyproject.toml            # pytest, ruff, and mypy tool configurations
    └── requirements.txt          # Python dependencies
```

---

## 4. Getting Started

### Backend Setup (FastAPI)

1. Activate the virtual environment:
   ```powershell
   .\backend\venv\Scripts\Activate.ps1
   ```
2. Install dependencies:
   ```powershell
   pip install -r .\backend\requirements.txt
   ```
3. Run the development server:
   ```powershell
   $env:PYTHONPATH="."
   .\backend\venv\Scripts\uvicorn backend.app.main:app --reload --port 8000
   ```
   - API Root: `http://localhost:8000/`
   - Interactive Swagger Docs: `http://localhost:8000/docs`
   - Health Check: `http://localhost:8000/api/v1/health`
   - Dashboard Stats: `http://localhost:8000/api/v1/dashboard/stats`

### Frontend Setup (Next.js)

1. Navigate to the frontend directory:
   ```powershell
   cd frontend
   ```
2. Run the development server:
   ```powershell
   npm run dev
   ```
   - Platform Gateway: `http://localhost:3000/`
   - Registration Portal: `http://localhost:3000/register`
   - Analyst Login: `http://localhost:3000/login`
   - Protected Dashboard: `http://localhost:3000/dashboard`
   - Text Forensics: `http://localhost:3000/dashboard/text`
   - Image Forensics: `http://localhost:3000/dashboard/image`
   - Video Forensics: `http://localhost:3000/dashboard/video`
   - Audio Forensics: `http://localhost:3000/dashboard/audio`
   - Reports Archive: `http://localhost:3000/dashboard/reports`
   - Settings & Profile: `http://localhost:3000/dashboard/settings`

---

## 5. Automated Verification Results (Step 08 Forensic Report Generation)

### Backend Quality Suite (All Executed and Verified)
- **Automated Pytest Suite (69 Tests)**:
  ```powershell
  $env:PYTHONPATH="."
  python -m pytest backend/tests -v
  ```
  *Result:*
  * Authentication suite: 9 tests — **PASSED**
  * Dashboard & isolation suite: 5 tests — **PASSED**
  * Health suite: 2 tests — **PASSED**
  * Step 4 AI Text detection regression suite: 11 tests — **PASSED**
  * Step 5 AI Image detection suite: 15 tests — **PASSED**
  * Step 7 E2E & Security integration suite: 3 tests — **PASSED**
  * Step 8 Forensic PDF Generation & Security suite: 12 tests — **PASSED**
  * Step 9 Model Evaluation, Wilson CI & Calibration suite: 12 tests — **PASSED**
  * **69 passed in 47.70s (100% Pass Rate)**

- **Model Evaluation & Benchmarking CLI**:
  ```powershell
  python -m backend.app.ml.evaluation.runner --modality all
  ```
  *Result:* Real empirical evaluation across Text (40 samples) and Image (20 samples) benchmarks, with honest transparent status for Video (MODEL UNAVAILABLE) and Audio (CANCELLED).

### Frontend Quality Suite (All Executed and Verified)
- **ESLint**:
  ```powershell
  cd frontend
  npm run lint
  ```
  *Result:* `0 errors, 0 warnings (PASSED)`

- **TypeScript Compiler**:
  ```powershell
  npx tsc --noEmit
  ```
  *Result:* `0 errors (PASSED)`

- **Next.js Production Build**:
  ```powershell
  npm run build
  ```
  *Result:* `Compiled successfully. Prerendered static routes: /, /_not-found, /dashboard, /dashboard/text, /dashboard/image, /dashboard/video, /dashboard/audio, /dashboard/reports, /dashboard/evaluation, /dashboard/settings, /login, /register (PASSED, 14/14 static routes)`

---

## 6. Feature Status & Roadmap (Steps 1–9)

| Feature / Step | Status | Evidence & Details |
| :--- | :--- | :--- |
| **Step 01: Authentication & Authorization** | `VERIFIED` | Argon2id hashing, 256-bit entropy sessions, HttpOnly cookies, sliding-window rate limit (69/69 tests passing). |
| **Step 02: Dashboard & Reports Architecture** | `VERIFIED` | Real DB counts, zero-mock baseline, chronological reports filterable by modality, cross-user isolation. |
| **Step 03: Database & Migration Architecture** | `VERIFIED` | Async SQLAlchemy 2 with asyncpg (PostgreSQL) and SQLite local fallback (`aicf.db`), relational constraints. |
| **Step 04: AI Text Detection Engine** | `VERIFIED` | Genuine `roberta-base-openai-detector` transformer on CPU, entropy, TTR, burstiness, repeated n-grams. |
| **Step 05: AI Image Detection Engine** | `VERIFIED` | Genuine Swin ViT (`umm-maybe/AI-image-detector`), 2D FFT octant anisotropy, Laplacian residual, EXIF/C2PA. |
| **Step 06: AI Video Detection Engine** | `PARTIAL / CONFIGURATION REQUIRED` | Abstract `BaseDetector` scaffolded in `backend/app/ml/video/`; UI shows `isEngineConfigured={false}`. No video model configured or active pipeline endpoints. |
| **Step 07: Integration, Security & E2E Testing** | `VERIFIED` | 69-test automated suite passing, E2E analyst lifecycle verified, horizontal escalation prevented (HTTP 403), rate limiting verified (HTTP 429), safe error sanitization. |
| **Step 08: Explainable Forensic Report Generation** | `VERIFIED` | In-memory ReportLab 5.1.0 PDF generator, AICF Black-and-Gold brand theme, dynamic 2-pass "Page X of Y" canvas, strict XML/HTML escaping, IDOR protection, authenticated download endpoints for text, image, and case records. |
| **Step 09: Model Evaluation & Benchmarking** | `VERIFIED` | Empirical benchmarking on genuine inference engines; 2x2 confusion matrices, Precision, Recall, F1, FPR, FNR, 95% Wilson Score intervals, Brier Score, ECE calibration; reproducible CLI runner (`--modality all`), authenticated REST endpoints (`/api/v1/evaluation/*`), and interactive Dashboard Evaluation page (`/dashboard/evaluation`). |
| **Audio Detection Feature** | `CANCELLED` | **CANCELLED — AI Audio Detection Engine**. Audio routes and UI module marked cancelled; no audio models, APIs, or database tables created. |


---

## 7. Environment Variables & Model Configuration

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `SECRET_KEY` | `dev-insecure-secret-key-...` | Session HMAC and token encryption key (override in production) |
| `DATABASE_URL` | `postgresql+asyncpg://aicf:aicf_dev_password@localhost:5432/aicf_db` | Primary database URI. Automatically falls back to SQLite `aicf.db` if PostgreSQL is offline |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed browser origins |
| `COOKIE_NAME` | `aicf_session` | Name of the HttpOnly session cookie |
| `COOKIE_SECURE` | `False` | Enforce SSL for cookies (`True` in production HTTPS) |
| `TEXT_DETECTOR_MODEL_ID` | `roberta-base-openai-detector` | HuggingFace model ID for real AI text classification |
| `IMAGE_DETECTOR_MODEL_ID` | `umm-maybe/AI-image-detector` | HuggingFace model ID for Swin Vision Transformer |
| `MAX_TEXT_LENGTH` | `50000` | Maximum characters accepted for text analysis (chars) |
| `MAX_IMAGE_FILE_SIZE` | `15728640` | Maximum uploaded image file size (15 MB) |
| `MAX_IMAGE_DIMENSION` | `8192` | Maximum image width or height in pixels |

---

## 8. Known Limitations & Forensic Caveats

1. **Detection Probability Caveat**: All forensic classification models provide probabilistic assessments of synthetic indicators rather than definitive proof. Adversarial perturbations, paraphrasing, heavy compression, and unseen generative architectures can alter signal confidence.
2. **Video Detection**: Scaffolded interface only; requires video processing pipeline (e.g., OpenCV frame sampling, optical flow) and video transformer model weights to reach full operation.
3. **Audio Detection**: Formally cancelled per project direction.
4. **Hardware Acceleration**: Text and image models currently infer on CPU. GPU acceleration (CUDA) is supported when PyTorch with CUDA is configured in the environment.
