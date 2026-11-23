# AICF — College Evaluator Demonstration Guide & Presentation Script

**Project:** AICF — A Multimodal Deep Learning Framework for Robust Detection of Synthetic Media  
**Target Audience:** Academic Evaluators, Project Reviewers, and Viva Examination Panels  
**Estimated Demonstration Time:** 10–15 minutes  

---

## 1. Quick Start Commands

To launch the platform for the demonstration, open two separate PowerShell windows:

### Terminal 1 — Backend API (FastAPI)
```powershell
cd C:\Users\acer\IMAGE
backend\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```
*Expected output: `INFO: Uvicorn running on http://127.0.0.1:8000`*

### Terminal 2 — Frontend UI (Next.js)
```powershell
cd C:\Users\acer\IMAGE\frontend
npm run dev
```
*Expected output: `Ready in ... ms | Local: http://localhost:3000`*

### Demonstration Credentials
- **URL:** [http://localhost:3000/login](http://localhost:3000/login)
- **Username:** `demo_analyst`
- **Password:** `SecurePassword123!`

---

## 2. Demonstration Flow: Step-by-Step Script

Follow this structured sequence to present a compelling, academically rigorous demonstration:

### Step 1: Project Introduction & Architecture (2 minutes)
- **Open:** [http://localhost:3000](http://localhost:3000)
- **Key Points to Explain:**
  1. *"AICF is an AI Content Forensics platform designed to detect synthetic media across multiple modalities: Text, Image, and Video."*
  2. *"Rather than relying on black-box predictions, AICF combines deep learning with multi-signal explainability: stylometrics for text, Fourier frequency and ELA heatmaps for images, and temporal optical consistency for video."*
  3. *"The platform follows strict epistemic honesty: classifications are probabilistic ('Likely AI-Generated', 'Likely Human', or 'Inconclusive') rather than absolute claims of truth."*

### Step 2: Analyst Authentication & Dashboard (1 minute)
- **Action:** Navigate to [http://localhost:3000/login](http://localhost:3000/login) and log in as `demo_analyst` / `SecurePassword123!`.
- **Explain:** Point out the session-based authentication, user isolation, and forensic investigation archive.

### Step 3: Modality A — Text Forensics Demonstration (3 minutes)
- **Navigate:** Click **Text Forensics** in the navigation bar ([/dashboard/text](http://localhost:3000/dashboard/text)).
- **Test 1 — Synthetic AI Text:**
  - Open `demo_samples/02_sample_ai_text.txt`.
  - Paste the text into the analysis box and click **Analyze Text**.
  - Show the result: Classification, AI Probability score, Perplexity/Burstiness telemetry, and sentence-level cadence highlights.
- **Test 2 — Authentic Human Text:**
  - Open `demo_samples/01_sample_human_text.txt`.
  - Click **Clear**, paste the human text, and click **Analyze Text**.
  - Highlight the difference in burstiness and syntactic variation.

### Step 4: Modality B — Image Forensics Demonstration (4 minutes)
- **Navigate:** Click **Image Forensics** in the navigation bar ([/dashboard/image](http://localhost:3000/dashboard/image)).
- **Test 1 — Synthetic Media Analysis:**
  - Drag and drop `demo_samples/04_sample_synthetic_image.jpg` into the upload zone.
  - Click **Run Forensic Analysis**.
  - Show the evaluation results:
    1. **Container Telemetry:** Dimensions, format, and cryptographic SHA-256 hash.
    2. **Vision Backbone:** Swin Vision Transformer classification and consensus score.
    3. **Frequency Domain (FFT):** High-frequency spectral anisotropy showing generative checkerboard artifacts.
    4. **Error Level Analysis (ELA) Heatmap:** Spatial compression discrepancy highlights.
    5. **Provenance & Metadata:** C2PA manifest presence check and EXIF camera metadata validation.
- **Test 2 — Real Camera Photograph:**
  - Click **Reset**, upload `demo_samples/03_sample_authentic_image.jpg`.
  - Explain how natural camera noise residuals and physical optics differ from generative diffusion outputs.

### Step 5: Modality C — Video Forensics Demonstration (3 minutes)
- **Navigate:** Click **Video Forensics** in the navigation bar ([/dashboard/video](http://localhost:3000/dashboard/video)).
- **Action:**
  - Drag and drop `demo_samples/05_sample_test_video.mp4`.
  - Click **Analyze Video**.
- **Key Technical Highlights to Show:**
  1. **Uniform Keyframe Sampling:** Explain that the engine extracts discrete temporal frames rather than loading the entire video into RAM, ensuring low memory consumption on resource-constrained hardware.
  2. **Frame-Level Screening:** Swin-ViT scores across individual keyframe timestamps.
  3. **Facial Deepfake Analysis:** MesoNet-4 facial boundary seam disparity detection.
  4. **Inter-Frame Temporal Consistency:** Optical difference heuristics detecting frame-to-frame flicker and anomalous transition spikes.
  5. **Multi-Signal Consensus Verdict:** Synthesis of spatial, facial, and temporal signals into an overall determination.

### Step 6: Case Reports & Audit Trails (1 minute)
- **Navigate:** Click **Case Reports** in the navigation bar ([/dashboard/reports](http://localhost:3000/dashboard/reports)).
- **Explain:** Show how investigations can be archived and exported as verifiable PDF audit reports containing cryptographic hashes, timestamped evidence, and legal disclaimers.

---

## 3. Explaining Classification Boundaries to Evaluators

When asked how AICF classifies media, present this precise framework:

| Classification | Meaning | Underlying Criteria |
|---|---|---|
| **Likely AI-Generated** | Strong synthetic markers detected across multiple independent signals. | $P(\text{AI}) \ge 0.65$ with corroborating frequency/stylometric anomalies. |
| **Likely Human / Authentic** | Consistent natural characteristics with absence of generative signatures. | $P(\text{AI}) \le 0.35$ with coherent physical camera/human noise patterns. |
| **Inconclusive** | Mixed signals, low resolution, recompressed container, or ambiguous confidence. | $0.35 < P(\text{AI}) < 0.65$ or image dimensions below forensic threshold. |

---

## 4. Key Answers for Viva & Evaluator Questions

**Q1: Why did you not implement Audio Detection?**  
*Answer:* "Audio deepfake detection was formally scoped out during Phase 0 architecture review to prioritize depth, explainability, and multi-signal robustness across the three primary visual and textual modalities. The UI explicitly denotes Audio as cancelled to maintain academic and technical integrity."

**Q2: How does the system prevent Out-Of-Memory crashes on standard hardware?**  
*Answer:* "AICF incorporates an operational resource safeguard. For video, it utilizes uniform temporal frame sampling rather than full video buffering. For images, heavy secondary transformer allocation is suspended when commit memory drops below safety limits, falling back gracefully to deterministic Fourier and noise residual features."

**Q3: Can your system detect manipulated images (splicing/copy-move) vs fully synthetic images?**  
*Answer:* "Yes. Dimension A classifies whole-image synthetic generation using Vision Transformers, while Dimension B evaluates local manipulation using Error Level Analysis (ELA), spectral frequency analysis, and metadata provenance. The two dimensions are mathematically decoupled so that local splicing findings never distort the generative probability."

---

## 5. Pre-Loaded Demonstration Samples

All demonstration media files are organized in the `demo_samples/` directory:

| Filename | Type | Purpose | Expected Signal |
|---|---|---|---|
| `01_sample_human_text.txt` | Text | Human essay snippet | High burstiness, varied sentence lengths |
| `02_sample_ai_text.txt` | Text | ChatGPT text snippet | Low burstiness, uniform sentence cadence |
| `03_sample_authentic_image.jpg` | Image | Natural camera photograph | Coherent sensor noise, standard EXIF |
| `04_sample_synthetic_image.jpg` | Image | AI-generated graphic | High-frequency spectral anisotropy |
| `05_sample_test_video.mp4` | Video | Multi-frame test clip | Uniform temporal sampling & frame scores |
