# AICF Phase 2 — Stage 2.1: Independent Forensic Engine Quality Audit

**Project:** `C:\Users\acer\IMAGE`  
**Auditor:** Senior Digital Forensics Engineer & AI Security Auditor  
**Date:** 2026-11-19  
**Audit Target:** AICF Phase 2 — Stage 2 (`backend/app/ml/image/forensics/`, `backend/tests/test_image_forensics_stage2.py`, and baseline integration)  
**Strict Mandate:** AUDIT ONLY — ZERO SOURCE CODE MODIFICATIONS PERFORMED.

---

## 1. Executive Summary & Audit Verdict

This independent technical audit evaluated the implementation of **Stage 2: Advanced Image Forensics and Manipulation Detection** following the successful completion and execution of 14 Stage 2 tests, 12 Stage 1 tests, and 21 baseline regression tests (47 tests total).

### Overall Forensic Readiness Rating: **PASS WITH LIMITATIONS (ARCHITECTURAL & HEURISTIC SUCCESS, PENDING CRYPTOGRAPHIC & EMPIRICAL CERTIFICATION)**

```
+----------------------------------------------------------------------------------------------------+
|                                    AUDIT FINDINGS SUMMARY MATRIX                                   |
+------------------------------------+--------------------------+------------------------------------+
| Forensic Audit Section             | Audit Classification     | Primary Engineering Takeaway       |
+------------------------------------+--------------------------+------------------------------------+
| 1. C2PA Verification Audit         | INCOMPLETE               | Byte-marker scanner only; lacks    |
|                                    |                          | ASN.1/CMS cryptographic validation.|
| 2. Manipulation Detection Audit    | PASS WITH LIMITATIONS    | Functional ELA, edge-damping, noise|
|                                    |                          | gradient & CMFD; high-contrast risk|
| 3. Frequency Analysis Audit        | PASS WITH LIMITATIONS    | Correct 2D FFT & anisotropy;       |
|                                    |                          | thresholds are empirical heuristics|
| 4. Spatial Localization Audit      | PASS                     | Correct quadrant binning & bounding|
|                                    |                          | box coordinates; normalized [0, 1].|
| 5. Evidence Fusion Audit           | PASS                     | Complete separation of Dimension B;|
|                                    |                          | no double-counting; honest priors. |
| 6. Test Quality Audit              | PASS WITH LIMITATIONS    | Tests verify code logic, but use   |
|                                    |                          | synthetic fixtures (not wild data).|
| 7. Security Audit                  | PASS WITH LIMITATIONS    | Safe in-memory buffers; lacks      |
|                                    |                          | explicit decompression-bomb caps.  |
| 8. Preservation & Invariants Audit | PASS                     | 100% hash match on all protected   |
|                                    |                          | files and classify_image() contract|
+------------------------------------+--------------------------+------------------------------------+
```

---

## 2. Detailed Technical Audit by Dimension

### 2.1 Section 1: C2PA & Provenance Verification Audit
- **Inspected File:** `backend/app/ml/image/forensics/provenance_verifier.py` (Lines 1–143)
- **Classification:** **INCOMPLETE**

#### Forensic Findings:
1. **Byte-Marker Scanning vs. True JUMBF Parsing (Lines 44–53):**
   - The module detects C2PA by scanning raw byte buffers for fixed byte markers: `b"jumb"`, `b"c2pa"`, `b"c2as"`, `b"c2pa.claim"`, `b"c2pa.signature"`, `b"c2pa.assertions"`.
   - *Limitation:* It does **not** parse JUMBF superbox headers (LBox, TBox, description box, payload box) per ISO/IEC 19566-5, nor does it parse CBOR-encoded claims per the C2PA 1.3/2.0 specifications.
2. **Absence of Cryptographic Signature Verification (Lines 99–129):**
   - The code checks `sig_idx = raw_bytes.find(C2PA_SIGNATURE_MARKER)` and verifies that `len(sig_context) >= 32`. If present and not truncated, it assigns `ProvenanceStatus.CRYPTOGRAPHICALLY_VERIFIED`.
   - *Severe Limitation / Misclassification:* No cryptographic verification (RSA, ECDSA, Ed25519) is performed over the claim hash using an ASN.1/CMS or COSE_Sign1 signature structure. The status label `CRYPTOGRAPHICALLY_VERIFIED` is misleading because it represents **structural signature marker presence**, not validated public-key mathematical non-repudiation.
3. **No Certificate Chain or Trust Validation (Lines 55–65):**
   - No X.509 certificate parsing, CRL (Certificate Revocation List), or OCSP validation is implemented.
   - Claims are mapped via substring matching (`b"adobe:firefly"`, `b"dall-e"`, `b"microsoft designer"`), which can be spoofed by any non-signed byte injection.
4. **No Claim-to-Asset Binding:**
   - The engine does not compute the hash of the image pixel data (jumbf:c2pa.hash.data) to verify that the container has not been altered post-signing.
5. **Positive Finding (Lines 78–82):**
   - The code strictly adheres to the negative-inference rule: missing C2PA credentials are explicitly documented as *not* implying human origin.

---

### 2.2 Section 2: Manipulation Detection Audit
- **Inspected File:** `backend/app/ml/image/forensics/manipulation_detector.py` (Lines 1–261)
- **Classification:** **PASS WITH LIMITATIONS**

#### Forensic Findings:
1. **Error Level Analysis (ELA) Implementation (Lines 51–77):**
   - Correctly recompresses in-memory at JPEG $Q=95$, computes pixel-wise channel maximum absolute error, and divides the image into $16 \times 16$ macro-blocks.
   - *Limitation:* Fixed $Q=95$ recompression is calibrated for high-quality originals. When an input image has an unknown original compression factor (e.g. $Q=70$), recompressing at $Q=95$ introduces uniform high error across the entire image, reducing sensitivity to localized edits.
2. **Edge-Mask Damping (Lines 61–68):**
   - Correctly calculates spatial gradient magnitude $\nabla I$ and applies damping:
     $$\text{Damping}(x, y) = \frac{1}{1.0 + 3.0 \cdot \nabla I_{\text{norm}}(x, y)}$$
   - *Positive:* Effectively prevents false positive ELA spikes along legitimate sharp photographic contours (e.g. dark hair against white sky).
   - *Limitation:* Finite differences via `np.gradient` are sensitive to sensor shot noise; a smoothed Sobel/Scharr filter would yield cleaner edge masks on noisy RAW sensors.
3. **Spatial Noise Residuals (Lines 126–172):**
   - Computes a discrete $3 \times 3$ Laplacian high-pass filter across luminance, divides the image into 4 quadrants, and measures the variance gradient ratio $\Delta \sigma^2 = \max(\sigma_q^2) / \min(\sigma_q^2)$.
   - *False-Positive Risk (Lines 152–153):* In natural photography with shallow depth of field (bokeh blur), the sharp subject in one quadrant naturally has high Laplacian variance while the blurred background in other quadrants has near-zero variance. This can trigger `noise_splicing_detected` ($\Delta \sigma^2 > 4.5$) on authentic camera portraits. The code correctly documents this in its `limitations` dictionary.
4. **Copy-Move Forgery Detection (Lines 185–231):**
   - Implements Fridrich's lexicographical block-sorting algorithm on $8 \times 8$ blocks using feature pairs $(\mu, \sigma)$ with spatial distance gating $\ge 3$ blocks ($24$ pixels).
   - *Limitation:* Using only two scalar features $(\mu, \sigma)$ per $8 \times 8$ block can generate false-positive matches on naturally repetitive textures (e.g. brick walls, textiles, grass, pavement). Standard forensic CMFD uses multi-dimensional DCT coefficients or SIFT/SURF keypoints with RANSAC affine verification.

---

### 2.3 Section 3: Frequency Analysis Audit
- **Inspected File:** `backend/app/ml/image/forensics/frequency_forensics.py` (Lines 1–157)
- **Classification:** **PASS WITH LIMITATIONS**

#### Forensic Findings:
1. **2D Fourier Transform (FFT) Implementation (Lines 44–50):**
   - Standard 2D Fast Fourier Transform `np.fft.fft2` with DC-centering via `np.fft.fftshift` and log-power spectrum `np.log1p(np.abs(fft_shift))`. Mathematically sound.
2. **Radial Power Bands (Lines 55–71):**
   - Concentric radial partitioning into Low ($r \le 0.25r_{\max}$), Mid ($0.25r_{\max} < r \le 0.65r_{\max}$), and High ($0.65r_{\max} < r \le r_{\max}$) bands normalized by total spectral power. Correct implementation.
3. **Azimuthal Anisotropy (Lines 73–84):**
   - Divides mid-high frequencies into 8 sectors of $45^\circ$ ($\pi/4$ rad) and computes standard deviation divided by mean of octant power. Accurately identifies non-uniform directional bias.
4. **Periodic Lattice Artifact Detection (Lines 86–99):**
   - Calculates the Z-score of the peak high-frequency power against high-frequency distribution. Flags when $Z > 4.5$ and anisotropy $> 0.45$.
   - *Limitation:* Thresholds are heuristic approximations derived from literature (Frank et al., ICML 2020), but have not been formally calibrated against large-scale ROC benchmarks of authentic camera images.
5. **Resampling Indicators (Lines 103–128):**
   - Computes radial profile derivative differences and counts sign reversals. Detects non-monotonic oscillations characteristic of bicubic downsampling or affine resizing.

---

### 2.4 Section 4: Spatial Localization Audit
- **Inspected File:** `backend/app/ml/image/forensics/localization.py` (Lines 1–85)
- **Classification:** **PASS**

#### Forensic Findings:
1. **Coordinate Correctness (Lines 57–60):**
   - Global image offsets (`y_off`, `x_off`) are added to quadrant-local indices, correctly mapping back to absolute image coordinates: $(y_{\min}, x_{\min}, y_{\max}, x_{\max})$.
2. **Coordinate Normalization (Lines 63–66):**
   - Normalization divides coordinates by `height` and `width`, producing strictly bounded values in $[0.0, 1.0]$.
3. **Thresholding & Clustering (Lines 34–35, 54):**
   - Uses adaptive statistical thresholding $\tau = \mu_{\text{anomaly}} + 2.2 \cdot \sigma_{\text{anomaly}}$ and enforces a minimum cluster size (`min_cluster = max(48, int(area * 0.005))`). Prevents isolated pixel noise from generating spurious bounding boxes.
4. **Boundary & Empty Handling (Lines 24–32):**
   - Explicitly rejects images $< 32 \times 32$ pixels and uniform anomaly maps ($\sigma < 0.5$). Handled safely.

---

### 2.5 Section 5: Evidence Fusion Audit
- **Inspected File:** `backend/app/ml/image/forensics/evidence_fusion.py` (Lines 1–189)
- **Classification:** **PASS**

#### Forensic Findings:
1. **Independence of Result Dimensions (Lines 30–35, 144–179):**
   - The module strictly evaluates **Dimension B: Manipulation Analysis**.
   - It outputs exclusively one of the 5 allowed states:
     `SUSPECTED_INPAINTING`, `SUSPECTED_SPLICING`, `SUSPECTED_RETOUCHING`, `NO_MANIPULATION_EVIDENCE_DETECTED`, `INSUFFICIENT_EVIDENCE`.
   - Manipulation scores have **zero mathematical impact** on Dimension A synthetic probabilities ($P(\text{AI})$).
2. **No Double-Counting of Correlated Evidence (Lines 156–179):**
   - Verdict synthesis is implemented via an ordered, mutually exclusive `if ... elif ... else` hierarchy. Evidence signals are not summed as pseudo-probabilities.
3. **Severity & Reliability Distinction (Lines 125–140):**
   - Findings across metadata, provenance, frequency, and manipulation modules maintain explicit, typed `severity` and `reliability` attributes.
4. **No Pseudo-Calibration:**
   - Confidence values ($0.75, 0.70, 0.65, 0.55, 0.0$) are discrete heuristic tiers, not continuous pseudoprobabilities.
5. **Absence of Seams != Full Synthesis (Lines 42, 177–179):**
   - Clean images with no anomalies map strictly to `NO_MANIPULATION_EVIDENCE_DETECTED` with confidence $0.0$. The system never infers full AI synthesis from clean seams.

---

### 2.6 Section 6: Test Quality Audit
- **Inspected Files:**
  - `backend/tests/test_image_forensics_stage2.py` (14 tests)
  - `backend/tests/test_generator_attribution.py` (12 tests)
  - `backend/tests/test_image_analysis.py` (21 tests)
- **Classification:** **PASS WITH LIMITATIONS**

#### Forensic Findings:
1. **Code Logic & Boundary Verification (PASS):**
   - All 47 tests pass cleanly (100% pass rate). Tests verify empty uploads, corrupted files, missing metadata, conflicting metadata, C2PA signatures, ELA damping, and bounding box geometry.
2. **Synthetic vs. Empirical Benchmark Limitation (LIMITATION):**
   - The tests rely on **programmatically synthesized in-memory fixtures** (`Image.new()`, numpy random noise arrays, injected EXIF dicts).
   - *Forensic Audit Reality:* Passing 47 unit tests confirms that the Python code executes without crashing and respects architectural boundaries. However, it does **not** establish real-world statistical accuracy (Precision, Recall, ROC-AUC, FPR, FNR) on authentic photographic benchmark datasets (e.g., CASIA v2.0, NIST MFC, Columbia Image Splicing, or RAISE uncompressed camera captures).

---

### 2.7 Section 7: Security Audit
- **Classification:** **PASS WITH LIMITATIONS**

#### Forensic Findings:
1. **Memory Safety & In-Memory Execution (PASS):**
   - All operations execute in memory via `io.BytesIO()`. Zero temporary files are written to disk, preventing file descriptor leaks, `/tmp` race conditions, and symlink attacks.
2. **Metadata Sanitization (PASS):**
   - String slices (`[:1000]`, `[:500]`, `[:50]`) truncate user comments, prompt graphs, and software headers, preventing log injection and memory bloat.
3. **Decompression Bomb Risk (PASS WITH LIMITATIONS):**
   - Pillow defaults to `Image.MAX_IMAGE_PIXELS = 89478485` (approx 89MP). While HTTP uploads are restricted to 10MB in `image.py`, a highly compressed PNG zip-bomb under 10MB could decompress into a multi-gigabyte raster if processed before Pillow's threshold.
   - *Recommendation:* Explicitly enforce a pre-decode raster dimension gate (`max_pixels = 4096 * 4096`).

---

### 2.8 Section 8: Preservation Audit & Cryptographic Verification
- **Classification:** **PASS**

All protected baseline files were rechecked against `backups/phase2_baseline_checkpoint/` using SHA-256 cryptographic hashes:

| File Path | Active SHA-256 Hash | Baseline Backup SHA-256 | Audit Status |
| :--- | :---: | :---: | :---: |
| `backend/app/ml/image/detector.py` | `54BF8AE13AC208EA1AE53A281FF3E21721EB26FAA6E155C8C32F2AA236285716` | `54BF8AE13AC208EA...` | **100% MATCH** |
| `backend/app/ml/image/ensemble.py` | `3726BD3084FFA97C...` | `3726BD3084FFA97C...` | **100% MATCH** |
| `backend/app/ml/image/features.py` | `D8BAF3331EAEF510...` | `D8BAF3331EAEF510...` | **100% MATCH** |
| `backend/app/ml/image/heatmap.py` | `B8772F642F210A7E...` | `B8772F642F210A7E...` | **100% MATCH** |
| `backend/app/api/v1/endpoints/image.py` | `1D096A00B1354DB2...` | `1D096A00B1354DB2...` | **100% MATCH** |
| `backend/tests/test_image_analysis.py` | `E0D095B0BF0D06A7...` | `E0D095B0BF0D06A7...` | **100% MATCH** |
| `backend/app/ml/image/generator_attribution.py` | `C04701D978436CF6...` | *Stage 1 Recorded* | **100% MATCH** |

- **`classify_image()` Signature & Return Contract:**
  - Location: Lines 152–163 of `backend/app/ml/image/detector.py`.
  - Signature: `def classify_image(self, image: Image.Image) -> tuple[float, float, float]:`
  - Return: `(ai_probability, human_probability, raw_score)`
  - Verification: **Completely untouched and verified identical.** Zero regression risk for Phase 3 video frame screening.

---

## 3. Prioritized Recommendations for Future Stages

1. **C2PA Engine Enhancement (For Stage 3/Production):**
   - Replace heuristic byte-marker detection with standard C2PA SDK bindings (e.g. `c2pa-python`) or integrate standard CMS/COSE cryptographic signature parsing with X.509 certificate chain validation.
   - Rename `CRYPTOGRAPHICALLY_VERIFIED` to `SIGNATURE_MARKER_DETECTED_UNVERIFIED` until full cryptographic verification is implemented.
2. **CMFD Multi-Feature Upgrade:**
   - Extend block features from scalar $(\mu, \sigma)$ to 8-coefficient DCT or SIFT keypoint clusters to eliminate false positives on natural periodic textures (brick walls, textiles).
3. **Decompression Bomb Defense:**
   - Enforce `Image.MAX_IMAGE_PIXELS = 16777216` ($4096 \times 4096$) prior to stream decoding.
4. **Empirical Forensic Calibration Benchmark:**
   - Execute an offline benchmark evaluation against CASIA v2.0 and RAISE datasets to establish empirical ROC-AUC, FPR, and FNR metrics.

---

## 4. Final Audit Sign-Off

**AUDIT CONCLUSION:**
Stage 2 implements a robust, modular, and mathematically sound heuristic forensic foundation with strict preservation of architectural boundaries, zero regressions in existing test suites, and 100% preservation of protected files. The known limitations identified in C2PA cryptographic depth, CMFD feature dimensionality, and benchmark validation have been thoroughly documented and classified.

**No source code has been modified. No dependencies have been installed. No modules have been integrated. Video detection has not been started.**

Audit completed and approved for presentation.

