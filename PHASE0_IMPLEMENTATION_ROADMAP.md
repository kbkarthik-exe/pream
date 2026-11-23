# PHASE 0: IMPLEMENTATION ROADMAP & EVALUATION STRATEGY
**Project:** `C:\Users\acer\IMAGE`  
**Application Title:** A Multimodal Deep Learning Framework for Robust Detection of Synthetic Media (AICF)  
**Audit Date:** 2026-11-18  
**Governance Standard:** Zero-Mock, Empirical Verification, Staged Delivery  

---

## 1. Phased Development Roadmap

The development trajectory is partitioned into five distinct, non-overlapping phases. Each phase builds upon the verified foundation of preceding phases without rewriting existing working code:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AICF DEVELOPMENT ROADMAP                           │
├─────────┬───────────────────────────────────┬───────────────────────────────┤
│ Phase 0 │ Reverse-Engineering & Audit       │ Clean-room research, boundary │
│         │                                   │ definition, architecture plans│
├─────────┼───────────────────────────────────┼───────────────────────────────┤
│ Phase 1 │ Local Multi-Detector Text Ensemble│ RoBERTa + DeBERTa-v3 + Shannon│
│         │                                   │ entropy + burstiness + TTR    │
├─────────┼───────────────────────────────────┼───────────────────────────────┤
│ Phase 2 │ Multi-Model Image Forensics       │ Swin ViT + ViT + 2D FFT +     │
│         │                                   │ Laplacian + ELA heatmaps      │
├─────────┼───────────────────────────────────┼───────────────────────────────┤
│ Phase 3 │ Video Deepfake & Facial Forensics │ OpenCV demux + Haar alignment │
│         │                                   │ + MesoNet-4 + temporal jitter │
├─────────┼───────────────────────────────────┼───────────────────────────────┤
│ Phase 4 │ Optional Cloud Verification Hub   │ PBKDF2 vault + Hive/GPTZero/  │
│         │                                   │ Copyleaks + consent gating    │
├─────────┼───────────────────────────────────┼───────────────────────────────┤
│ Phase 5 │ Complete Acceptance Audit         │ 129 regression tests, build,  │
│         │                                   │ empirical latencies & memory  │
└─────────┴───────────────────────────────────┴───────────────────────────────┘
```

---

## 2. Phase-by-Phase Technical Milestones & Deliverables

### Phase 1: Local Multi-Detector Text Ensemble
- **Objective:** Upgrade text forensics into an explainable multi-model consensus system.
- **Key Tasks:**
  1. Preserve primary RoBERTa detector (`roberta-base-openai-detector`).
  2. Implement secondary DeBERTa-v3 adapter with host disk free-space verification ($>1.0\text{ GB}$).
  3. Implement deterministic linguistic feature extraction (Shannon entropy, sentence burstiness, Type-Token Ratio, 3-gram repetition).
  4. Build temperature-scaled covariance consensus aggregator ($T=1.25, \rho=0.72$).
  5. Calibrate output verdicts: `LIKELY AI-GENERATED`, `LIKELY HUMAN`, `INCONCLUSIVE`.
  6. Update text API responses, database persistence, and ReportLab PDF dossiers.
- **Acceptance Criterion:** 17 automated tests in `test_text_analysis.py` pass cleanly.

### Phase 2: Multi-Model Image Forensics & Heatmaps
- **Objective:** Upgrade image forensics into a dual-transformer and spectral signal consensus engine.
- **Key Tasks:**
  1. Preserve primary Swin Vision Transformer (`umm-maybe/AI-image-detector`).
  2. Implement secondary ViT global self-attention detector (`google/vit-base-patch16-224`).
  3. Implement 2D Fast Fourier Transform (FFT) octant anisotropy and high-frequency ratio.
  4. Implement spatial Laplacian variance kernel convolution for edge blur detection.
  5. Build Error Level Analysis (ELA) engine computing Q=95 JPEG compression artifact heatmaps.
  6. Update image API responses, database models, and ReportLab image PDF dossiers.
- **Acceptance Criterion:** 21 automated tests in `test_image_analysis.py` pass cleanly.

### Phase 3: Advanced Video Deepfake Detection & Facial Forensics
- **Objective:** Upgrade video processing with temporal keyframe screening and facial deepfake analysis.
- **Key Tasks:**
  1. Preserve headless OpenCV stream demuxing (1.0s interval, max 30 frames, 50MB limit).
  2. Preserve Swin ViT frame-by-frame screening.
  3. Implement Haar Cascade face detection with eye and nose alignment.
  4. Implement MesoNet-4 facial deepfake architecture in PyTorch (`face_deepfake.py`).
  5. Implement honest weight handling: report `UNAVAILABLE` when `models/mesonet4_ffpp.pt` is missing without fabricating neural scores.
  6. Implement temporal consistency differencing (inter-frame variance and flicker score).
  7. Combine frame screening, facial deepfake, and temporal variance into video consensus aggregator.
  8. Update video API responses, database models, and ReportLab video PDF dossiers.
- **Acceptance Criterion:** 29 automated tests in `test_video_analysis.py` pass cleanly.

### Phase 4: Optional Cloud Verification Hub & Secret Vault
- **Objective:** Provide secure, consent-gated third-party cloud cross-verification.
- **Key Tasks:**
  1. Implement PBKDF2-HMAC-SHA256 authenticated Encrypt-then-MAC cipher with per-user key derivation.
  2. Build official cloud adapters for Hive AI, GPTZero, and Copyleaks using official REST APIs.
  3. Enforce mandatory analyst consent (`user_consent=True`) on outbound endpoints; reject with HTTP 400 if False.
  4. Implement raw secret masking (`hiv_••••••••1234` or `NOT_CONFIGURED`) in all API responses.
  5. Guarantee complete air-gapped local functionality when cloud keys are unconfigured.
  6. Build Settings & Security Hub UI for credential management.
- **Acceptance Criterion:** 19 automated tests in `test_cloud_verification.py` pass cleanly.

### Phase 5: Complete Acceptance Audit & Forensic Hardening
- **Objective:** Comprehensive integration, security, and performance verification.
- **Key Tasks:**
  1. Execute full 129-test backend regression suite (`pytest backend/tests/ -q`).
  2. Execute frontend ESLint and Next.js production build (`npm run build`).
  3. Measure actual empirical inference latencies and peak working set memory via PSAPI.
  4. Execute penetration testing across cross-tenant IDOR, SQL injection, path traversal, and XSS.
  5. Capture full-resolution acceptance screenshots across all 14 routes.
  6. Generate master audit deliverables (`FINAL_SYSTEM_AUDIT.md`, `FINAL_TEST_REPORT.md`, `SECURITY_AUDIT.md`, `KNOWN_LIMITATIONS.md`).
- **Acceptance Criterion:** 129/129 tests pass, zero regressions, zero warnings.

---

## 3. Rigorous Empirical Evaluation & Validation Strategy

To prevent fabricated benchmarks or false accuracy claims, AICF adheres to a scientifically defensible evaluation protocol:

### 3.1 Dataset Separation & Partitioning
- **Independent Labeled Corpuses:**
  - **Text:** Balanced benchmark corpus comprising synthetic texts (GPT-3.5, GPT-4, Claude 3, Llama 3) and authentic human texts (Wikipedia, arXiv, Reuters, human essays).
  - **Image:** Curated evaluation sets from Midjourney v5/v6, Stable Diffusion XL, DALL-E 3, and authentic camera photographs (COCO, RAISE).
  - **Video:** Real video sequences paired with synthetic clips and FaceForensics++ deepfakes.
- **Partitioning:** Strict three-way split: 70% Training, 15% Validation (for temperature scaling and threshold tuning), and 15% Held-Out Test (evaluated only once for final reporting).

### 3.2 Evaluation Metrics Formulation
1. **Precision:**
   $$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}}$$
2. **Recall (Sensitivity):**
   $$\text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}}$$
3. **F1-Score:**
   $$\text{F1} = 2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$
4. **False Positive Rate (FPR):**
   $$\text{FPR} = \frac{\text{FP}}{\text{FP} + \text{TN}}$$
5. **False Negative Rate (FNR):**
   $$\text{FNR} = \frac{\text{FN}}{\text{TP} + \text{FN}}$$
6. **Brier Score (Probabilistic Calibration):**
   $$\text{BS} = \frac{1}{N} \sum_{i=1}^{N} (f_i - o_i)^2$$
7. **Expected Calibration Error (ECE):**
   $$\text{ECE} = \sum_{m=1}^{M} \frac{|B_m|}{N} \left|\text{acc}(B_m) - \text{conf}(B_m)\right|$$

### 3.3 Robustness & Stress Testing
- **Adversarial Text Perturbation:** Test resilience against paraphrasing, synonym insertion, and recursive prompting.
- **Image Compression Stress:** Evaluate detector degradation across JPEG quality tiers ($Q = 95, 80, 60, 40$).
- **Spatial Transformation:** Test resilience against image cropping, resizing, and Gaussian blur.
- **Inconclusive Threshold Handling:** If detector signals conflict or confidence lies in the indeterminate zone ($0.35 - 0.65$), the system must return **`INCONCLUSIVE`** rather than guessing.
