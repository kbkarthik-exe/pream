# AICF — AI Content Forensics & Authenticity Intelligence Platform

> **Detect. Analyze. Explain. Verify.**

AICF is an enterprise-grade digital forensics and synthetic content intelligence platform designed to analyze text, images, videos, and audio for potential human or AI generation. Built with a decoupled, high-assurance architecture, the platform pairs deep forensic telemetry with accessible explanations and transparent confidence boundaries.

---

## 1. System Architecture

```
AICF Platform Architecture
├── Frontend (Next.js 16 + React 19 + TypeScript + Tailwind CSS v4)
│   ├── Black-and-Gold forensic UI system with responsive mobile drawer
│   ├── Authentication Pages: /login and /register
│   ├── Protected Main Dashboard: /dashboard (guarded with AuthGuard)
│   ├── Four Forensic Modality Modules:
│   │   ├── /dashboard/text   (AI Text Forensics & Synthetics Detection)
│   │   ├── /dashboard/image  (AI Image Forensics & Generative Synthesis)
│   │   ├── /dashboard/video  (AI Video Detection & Deepfake Analysis)
│   │   └── /dashboard/audio  (AI Audio & Synthetic Voice Clone Detection)
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
│   │   ├── GET   /api/v1/reports         (Filtered by modality, chronological)
│   │   ├── POST  /api/v1/reports         (Create user-owned case record)
│   │   └── GET   /api/v1/reports/{id}    (Strict cross-user isolation checks)
│   ├── Sliding-window rate limiter with Retry-After headers
│   ├── Cryptographic session token generation (256-bit entropy, SHA-256 hashed in DB)
│   └── PostgreSQL async engine (asyncpg) with automated local SQLite fallback
│
├── Modular AI/ML Layer (Decoupled from API routes)
│   ├── BaseDetector interface with mandatory scientific disclaimers
│   ├── app/ml/text/   (Perplexity, burstiness, syntax patterns)
│   ├── app/ml/image/  (Diffusion noise, frequency artifacts, EXIF)
│   ├── app/ml/video/  (Temporal consistency, facial coherence)
│   └── app/ml/audio/  (Acoustic spectrograms, vocoder traces)
│
└── Database (PostgreSQL / async SQLAlchemy)
    ├── users table            (Argon2id password hashes, analyst profiles)
    ├── user_sessions table    (Hashed tokens, expiration, IP & user-agent audit)
    └── forensic_reports table (User-scoped investigation cases)
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
    │   ├── test_auth.py          # Comprehensive authentication & authorization tests
    │   ├── test_dashboard.py     # Real stats, accumulation, isolation & profile tests
    │   └── test_health.py        # Service health check tests
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

## 5. Automated Verification Results

### Backend Quality Suite (All Executed and Verified)
- **Automated Pytest Suite (42 Tests)**:
  ```powershell
  $env:PYTHONPATH="."
  .\backend\venv\Scripts\pytest .\backend\tests -v
  ```
  *Result:*
  * Authentication suite: 9 tests — **PASSED**
  * Dashboard & isolation suite: 5 tests — **PASSED**
  * Health suite: 2 tests — **PASSED**
  * Step 4 AI Text detection regression suite: 11 tests — **PASSED**
  * Step 5 AI Image detection suite: 15 tests — **PASSED**
  * **42 passed in 45.57s (100% Pass Rate)**

- **Ruff Linter & Formatter**:
  ```powershell
  .\backend\venv\Scripts\ruff check .\backend
  ```
  *Result:* `All checks passed!`

- **Mypy Static Type Checking**:
  ```powershell
  .\backend\venv\Scripts\mypy --explicit-package-bases backend
  ```
  *Result:* `Success: no issues found in 52 source files`

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
  *Result:* `Compiled successfully. Prerendered static routes: /, /_not-found, /dashboard, /dashboard/text, /dashboard/image, /dashboard/video, /dashboard/audio, /dashboard/reports, /dashboard/settings, /login, /register (PASSED, 13/13 static routes)`

---

## 6. Documented Limitations & Next Steps (Step 05 Completed)

1. **Persistent PostgreSQL Daemon**: The application runs seamlessly against local PostgreSQL via `DATABASE_URL=postgresql+asyncpg://...`, with automatic SQLite fallback for zero-dependency local test execution.
2. **AI Text Forensics Engine (Step 04 Completed)**: Genuine fine-tuned RoBERTa sequence classification transformer (`roberta-base-openai-detector`) paired with burstiness, type-token ratio (TTR), repeated n-grams, and Shannon entropy.
3. **AI Image Forensics Engine (Step 05 Completed)**: Genuine fine-tuned Swin Vision Transformer (`umm-maybe/AI-image-detector`, CC-BY-4.0) paired with 2D Fast Fourier Transform (FFT) radial octant anisotropy, discrete Laplacian noise residual variance, EXIF/PNG prompt extraction, and C2PA Content Credentials inspection.
4. **Next Steps (Step 06 & Beyond)**: Video deepfake analysis (temporal coherence, optical flow) and audio voice clone detection (spectrograms, vocoder traces) remain scaffolded for subsequent milestone steps.
