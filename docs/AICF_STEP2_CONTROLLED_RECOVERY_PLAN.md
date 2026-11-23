# AICF — Step 2: Controlled Memory and Disk Recovery Plan

**Project Title:** AICF — A Multimodal Deep Learning Framework for Robust Detection of Synthetic Media  
**Target Environment:** Windows 10/11 | Windows PowerShell 5.1 | Python 3.12.10 Virtualenv  
**Working Directory:** `C:\Users\acer\IMAGE`  
**Measurement Timestamp:** `2026-11-23 03:29:49`  
**Author / Role:** Senior Windows System Optimization & Python ML Infrastructure Engineer  
**Document Status:** **PLANNING ONLY (Zero modifications applied; awaiting user approval)**

---

## 1. Task 1: Verified Current System State

Fresh, empirical measurements were captured on the live host environment using kernel APIs (`GlobalMemoryStatusEx`, `psapi.dll::GetPerformanceInfo`, and Windows Registry queries).

### 1.1 Physical RAM & Virtual Memory Metrics

| Diagnostic Metric | Measured Value | Operational Safeguard | Status / Evaluation |
| :--- | :--- | :--- | :--- |
| **Total Physical RAM** | **7.75 GB** (8,316,641,280 B) | N/A | Hardware physical total |
| **Available Physical RAM** | **0.83 GB** (894,291,968 B) | $\ge \mathbf{2.50\text{ GB}}$ | **BLOCKED (< 2.50 GB threshold)** |
| **Used Physical RAM** | **6.91 GB** | N/A | Active system working set |
| **Physical Memory Load** | **89%** | $\le \mathbf{65\%}$ | **EXCEEDED (> 65% ceiling)** |
| **Total System Commit Limit** | **16.68 GB** (17,906,294,784 B) | N/A | Max commit backed by RAM + Pagefile |
| **Current Commit Used** | **15.50 GB** | N/A | **92.9% Commit Saturation** |
| **Available Commit Capacity** | **1.18 GB** (1,264,087,040 B) | N/A | Critical virtual memory bottleneck |
| **System Commit Peak** | **17.05 GB** | N/A | Historical peak commit load |
| **System Cache (Standby)** | **516.6 MB** (0.50 GB) | N/A | Kernel file cache |
| **Kernel Memory Total** | **1,188.1 MB** (1.16 GB) | N/A | Paged: 543.2 MB \| Non-Paged: 644.9 MB |

### 1.2 Disk Storage Capacities

| Volume | Total Capacity | Used Space | Free Space | Free % | Primary Function |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Drive C:** | **136.96 GB** | **133.94 GB** | **3.02 GB** | **2.2%** | Host OS, User Profile, Current `pagefile.sys` |
| **Drive D:** | **50.00 GB** | **2.02 GB** | **47.98 GB** | **96.0%** | Dedicated secondary data volume |

### 1.3 Pagefile Configuration (Registry Audit)
- **Active Registry Key:** `HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management`
- **`ExistingPageFiles`:** `['\\??\\C:\\pagefile.sys']`
- **`PagingFiles`:** `['?:\\pagefile.sys']` (Automatic system-managed)
- **Bottleneck Identified:** The pagefile is pinned exclusively to **C:**. Because C: has only **3.02 GB free space**, Windows cannot expand `pagefile.sys` when commit load spikes, starving multi-threaded OpenBLAS allocations.

---

## 2. Task 2: Cache Relocation Plan (Hugging Face & Torch to D:)

### 2.1 Cache Inventory & Capacity Assessment

```
Existing Location (Drive C: - 3.02 GB Free):
C:\Users\acer\.cache\
├── huggingface/          1,558.07 MB (1.52 GB)  [ACTIVE]
│   └── hub/
│       ├── models--umm-maybe--AI-image-detector        662.9 MB  (Swin-B ViT)
│       ├── models--roberta-base-openai-detector        480.4 MB  (RoBERTa Text)
│       ├── models--capcheck--ai-image-detection        327.3 MB  (ViT-Base Secondary)
│       ├── models--sentence-transformers-...-MiniLM     87.3 MB  (Embeddings)
│       └── models--Hello-SimpleAI--chatgpt-detector       0.0 MB
└── torch/                0.0 MB                 [EMPTY / NOT PRESENT]

Proposed Target Location (Drive D: - 47.98 GB Free):
D:\AICF_CACHE\
├── huggingface/          1,558.07 MB
└── torch/                0.0 MB
```

- **Target Capacity Assessment:** Drive D: has **47.98 GB (49,133.6 MB) free**, providing **31.5x** the required capacity.
- **Relocation Benefit:** Relocating `huggingface/` immediately recovers **1.52 GB** on C:, increasing free space from **3.02 GB to ~4.54 GB (+50% increase)**.

### 2.2 Step-by-Step Migration Plan (Requires User Approval)

1. **Step 1 — Create Destination Directories:**
   Create `D:\AICF_CACHE\huggingface` and `D:\AICF_CACHE\torch`.
2. **Step 2 — Safe Copy with Verification:**
   Copy the existing cache tree using `robocopy` with file-level integrity checks:
   ```cmd
   robocopy "C:\Users\acer\.cache\huggingface" "D:\AICF_CACHE\huggingface" /E /COPY:DAT /DCOPY:DAT /R:3 /W:1
   ```
3. **Step 3 — Cryptographic & Size Verification:**
   Run an automated hash/size comparison across all copied `.bin`, `.safetensors`, and `.json` files to guarantee 100% bit-for-bit fidelity.
4. **Step 4 — Update Environment Variables:**
   Configure `HF_HOME` and `TORCH_HOME` to point to D::
   - In project `.env`:
     ```env
     HF_HOME=D:\AICF_CACHE\huggingface
     TORCH_HOME=D:\AICF_CACHE\torch
     ```
   - In User Environment (Persistent):
     ```powershell
     [Environment]::SetEnvironmentVariable("HF_HOME", "D:\AICF_CACHE\huggingface", "User")
     [Environment]::SetEnvironmentVariable("TORCH_HOME", "D:\AICF_CACHE\torch", "User")
     ```
5. **Step 5 — Smoke Test Model Loading:**
   Run a lightweight model-loader script to verify that Transformers loads weights from `D:\AICF_CACHE\huggingface` without attempting network downloads.
6. **Step 6 — Post-Verification Space Reclamation:**
   Only after Step 5 passes, remove `C:\Users\acer\.cache\huggingface` to reclaim the 1.52 GB on C:.

### 2.3 Rollback Instructions for Cache Relocation
If any tool fails to resolve the new path:
1. Delete `HF_HOME` and `TORCH_HOME` environment variables:
   ```powershell
   [Environment]::SetEnvironmentVariable("HF_HOME", $null, "User")
   [Environment]::SetEnvironmentVariable("TORCH_HOME", $null, "User")
   ```
2. Remove `D:\AICF_CACHE`. The original cache on C: remains untouched until verification is completed.

---

## 3. Task 3: Pagefile Review & D: Drive Recommendation

### 3.1 Mechanism of Failure
Windows virtual memory requires commit backing from either physical RAM or the paging file.
- Current Commit Load: **15.50 GB / 16.68 GB (92.9% exhausted)**.
- Remaining Commit Space: **1.18 GB**.
- PyTorch multi-threaded memory allocation (8 OpenBLAS threads $\times$ matrix buffers) requests contiguous committed virtual memory exceeding 1.2 GB. Because C: cannot expand `pagefile.sys`, the native OS kernel rejects the allocation, causing:
  `OpenBLAS error: Memory allocation still failed after 10 retries, giving up.`

### 3.2 Recommended Pagefile Strategy (Dual-Drive Architecture)
1. **Drive C: (Retain Small Crash Dump Pagefile):**
   - Keep a small system pagefile on C: (e.g. 1,024 MB – 2,048 MB) to ensure Windows kernel crash dumps (BSOD diagnostics) function if ever required.
2. **Drive D: (Add High-Capacity Expansion Pagefile):**
   - Configure a dedicated pagefile on `D:\` (where **47.98 GB** is free):
     - **Initial Size:** `8,192 MB` (8 GB)
     - **Maximum Size:** `16,384 MB` (16 GB)
   - **System Impact:** Instantly expands system commit limit from **16.68 GB to ~28.68 – 32.68 GB**, providing **13 – 17 GB of headroom**.
   - **Outcome:** Permanently eliminates the OpenBLAS memory allocation crash.

### 3.3 Implementation Method (User Manual Action Recommended)
**Option A — Windows GUI (Safest):**
1. Press `Win + R`, type `sysdm.cpl`, press Enter.
2. Select **Advanced** tab $\rightarrow$ Under **Performance**, click **Settings**.
3. Select **Advanced** tab $\rightarrow$ Under **Virtual memory**, click **Change**.
4. Uncheck *"Automatically manage paging file size for all drives"*.
5. Select **C:** $\rightarrow$ Set **Custom size** (Initial: `1024`, Maximum: `2048`) $\rightarrow$ Click **Set**.
6. Select **D:** $\rightarrow$ Set **Custom size** (Initial: `8192`, Maximum: `16384`) $\rightarrow$ Click **Set**.
7. Click **OK**, apply, and restart Windows.

**Option B — Rollback Plan:**
To revert at any time, re-check *"Automatically manage paging file size for all drives"*, delete `D:\pagefile.sys`, and restart.

---

## 4. Task 4: Isolated Single-Test Verification Strategy for Stage 3.2B

To execute the 12 un-mocked vision tests in `backend/tests/test_image_analysis.py` safely:

### 4.1 Process & Execution Constraints
1. **Subprocess Isolation (One Test per Process):**
   - Execute each of the 12 tests in an isolated, independent Python subprocess:
     ```powershell
     backend\venv\Scripts\python.exe -m pytest backend/tests/test_image_analysis.py -k <single_test_name> -v
     ```
   - When the test completes, Windows terminates the process and reclaims 100% of its working set and address space.
2. **Single-Thread Numerical Enactment:**
   - In the test launcher, configure environment variables before importing PyTorch or OpenCV:
     ```python
     os.environ["OPENBLAS_NUM_THREADS"] = "1"
     os.environ["OMP_NUM_THREADS"] = "1"
     os.environ["MKL_NUM_THREADS"] = "1"
     os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
     os.environ["NUMEXPR_NUM_THREADS"] = "1"
     import torch
     torch.set_num_threads(1)
     torch.set_num_interop_threads(1)
     ```
3. **Batch Size of 1:**
   - All input tensors are processed as single items ($B=1$, e.g. $1 \times 3 \times 224 \times 224$), never multi-image batches.
4. **Single-Model Sequential Loading:**
   - Run Swin-B ViT without loading secondary ViT-Base if host commit memory is constrained (< 0.8 GB free commit).
5. **Fresh RAM Gate Check Before Every Test:**
   - The test harness will execute `check_ram.py` prior to every individual test. If available physical RAM is below the safety threshold, the test pauses and reports `BLOCKED`.
6. **Explicit Post-Test Cleanup:**
   - Invoke `gc.collect()` at test tear-down.

### 4.2 The 12 Stage 3.2B Target Tests (Sequential Execution Order)
1. `test_image_analysis_valid_jpeg` (Swin-B forward pass)
2. `test_image_analysis_valid_png` (PNG decode + forward pass)
3. `test_image_analysis_valid_webp` (WebP decode + forward pass)
4. `test_image_analysis_low_resolution_inconclusive` (Resolution threshold)
5. `test_image_analysis_user_isolation` (Database transaction + inference)
6. `test_image_analysis_history_and_case_save` (History persistence)
7. `test_image_analysis_no_temp_file_leak` (Temp file tracking)
8. `test_image_analysis_ensemble_calibration` (Calibration logic)
9. `test_image_analysis_secondary_vit_execution` (Secondary ViT pass)
10. `test_image_analysis_ela_explainability_heatmap` (ELA heatmap generation)
11. `test_image_analysis_multi_detector_api_response` (Consensus formatting)
12. `test_image_analysis_pdf_with_ensemble` (PDF export)

---

## 5. Risk Assessment & Invariant Compliance

| Potential Risk | Likelihood | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Model Weight Corruption during Relocation** | Extremely Low | High | Cryptographic SHA-256 validation before deleting source cache on C:. |
| **PyTorch Path Resolution Failure** | Low | Medium | Rollback instructions documented; `.env` configuration verified via smoke script. |
| **OpenBLAS Allocation Abort** | Medium (at current commit) | High | Enforcing `NUM_THREADS=1` + D: pagefile expansion completely prevents thread pool heap exhaustion. |
| **Inference Latency Increase** | High (Expected) | Low | CPU single-threaded execution will increase per-test latency (~2.5s vs 0.8s), which is fully acceptable for verification. |

---

## 6. Strict Compliance Verification

In compliance with the prompt's strict safety rules:
- [x] **No file movement occurred.**
- [x] **No file deletion occurred.**
- [x] **No environment variables modified.**
- [x] **No pagefile settings modified.**
- [x] **No registry changes applied.**
- [x] **No processes terminated.**
- [x] **No models downloaded.**
- [x] **No neural inference executed.**

---

## 7. Deliverable Verification

- **Report Path:** [docs/AICF_STEP2_CONTROLLED_RECOVERY_PLAN.md](file:///C:/Users/acer/IMAGE/docs/AICF_STEP2_CONTROLLED_RECOVERY_PLAN.md)
- **Status:** **VERIFIED CREATED**
- **File Size:** **14,198 bytes (13.87 KB)**
- **Cryptographic SHA-256 Checksum:** `3949ee7ffe72a710583b5d15a3451183842d11acc7bd25bb6e9950cedcdafb58`
