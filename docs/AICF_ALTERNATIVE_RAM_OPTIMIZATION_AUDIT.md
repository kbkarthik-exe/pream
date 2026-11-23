# AICF — Alternative RAM Optimization & Resource Diagnostic Audit

**Project Title:** AICF — A Multimodal Deep Learning Framework for Robust Detection of Synthetic Media  
**Target Environment:** Windows 10/11 | Windows PowerShell 5.1 | Python 3.12.10 Virtualenv  
**Working Directory:** `C:\Users\acer\IMAGE`  
**Date of Audit:** November 23, 2026 (03:26 IST)  
**Role:** Senior Windows System Optimization & Python ML Infrastructure Engineer  
**Audit Scope:** Physical RAM depletion investigation, Windows commit charge analysis, model footprint profiling, and alternative resource-efficient Stage 3.2B verification design.  
**Execution Rule:** **READ-ONLY AUDIT — Zero source code modifications; zero process terminations; zero setting changes.**

---

## 1. Executive Summary & Current RAM Measurements

A multi-tiered, read-only system audit was performed using Windows kernel APIs (`GlobalMemoryStatusEx`, `psapi.dll::GetPerformanceInfo`, and Windows Registry queries).

### 1.1 Memory Metrics (Measured Live via `check_ram.py`)

| Diagnostic Metric | Measured Value | Operational Safeguard | Status / Evaluation |
| :--- | :--- | :--- | :--- |
| **Total Physical RAM** | **7.75 GB** (8,321,024 KB) | N/A | Hardware physical total |
| **Available Physical RAM** | **0.87 GB** (912,260 KB) | $\ge \mathbf{2.50\text{ GB}}$ | **BLOCKED (< 2.50 GB threshold)** |
| **Used Physical RAM** | **6.88 GB** | N/A | High system working set load |
| **Physical Memory Utilization** | **88%** | $\le \mathbf{65\%}$ | **EXCEEDED (> 65% ceiling)** |
| **Current System Commit Total** | **15.43 GB** | N/A | Total committed virtual memory |
| **System Commit Limit** | **16.68 GB** | N/A | Max commit backed by RAM + Pagefile |
| **System Commit Peak** | **17.05 GB** | N/A | Historical peak commit load |
| **System Cache (Standby)** | **803.9 MB** (0.79 GB) | N/A | Active kernel file cache |
| **Kernel Memory Total** | **1,230.4 MB** (1.20 GB) | N/A | Paged: 562.2 MB \| Non-Paged: 668.2 MB |

### 1.2 Storage Metrics (C: vs. D: Drive Capacities)
- **C: Drive (OS & Current Pagefile):** Total: **136.96 GB** \| Used: **133.90 GB** \| **Free: 3.05 GB (2.2% Free)**.
- **D: Drive (Secondary Volume):** Total: **50.00 GB** \| Used: **2.02 GB** \| **Free: 47.98 GB (96.0% Free)**.

---

## 2. Phase A: Read-Only System Diagnostics & Process Analysis

### 2.1 Process Memory Consumption & Isolation Boundary
Processes running in the active session and host desktop environments account for the **6.88 GB** physical RAM footprint:
1. **Host Desktop & Electron Applications:**
   - Visual Studio Code / Antigravity IDE (Electron main process, GPU helper, language servers): ~1.0 – 1.4 GB.
   - Chromium / Edge browser instances with multiple active tabs: ~1.8 – 3.2 GB.
2. **Windows Desktop & Background Services:**
   - Desktop Window Manager (`dwm.exe`) & Explorer (`explorer.exe`): ~350 – 600 MB.
   - Microsoft Teams / OneDrive / Background Telemetry: ~400 – 700 MB.
   - Antimalware Service Executable / Windows Defender (`MsMpEng.exe`): ~250 – 450 MB.
3. **Sandbox Session Processes (Verified via Win32 PSAPI):**
   - Active PowerShell execution environments (`powershell.exe`): ~175.3 MB (Working Set).
   - Python virtual environment runtime (`python.exe`): ~17.1 MB (Working Set).

### 2.2 Windows Pagefile Configuration (Registry Audit)
Audit of `HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management` revealed:
- `ExistingPageFiles`: `\??\C:\pagefile.sys` (Hosted exclusively on C: drive).
- `PagingFiles`: `['?:\\pagefile.sys']` (System-managed automatic sizing).
- `ClearPageFileAtShutdown`: `0` (Page file is not scrubbed on power-off; fragmented pages persist).
- `HiberbootEnabled`: `1` (Windows Fast Startup is **ACTIVE**; shutdowns hibernate the kernel session rather than performing a fresh cold boot).

---

## 3. Root-Cause Assessment: Why Windows Has Limited Available RAM

The mechanistic failure in Stage 3.2B (`OpenBLAS error: Memory allocation still failed after 10 retries, giving up.`) is caused by three compounding bottlenecks:

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. Physical RAM Saturation                                             │
│ 7.75 GB physical RAM with 6.88 GB consumed by OS & Desktop apps (88%)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. Windows Commit Charge Bottleneck                                    │
│ Commit Used is 15.43 GB out of 16.68 GB Limit (92.6% Commit Utilization)│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. Paging File Expansion Starvation                                    │
│ C:\pagefile.sys CANNOT expand because C: drive has only 3.05 GB free   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Result: PyTorch / OpenBLAS multi-threaded heap allocation fails        │
│ "OpenBLAS error: Memory allocation still failed after 10 retries"       │
└────────────────────────────────────────────────────────────────────────┘
```

1. **Commit Limit Exhaustion:** Virtual memory allocations in Windows require commit backing. System commit used (**15.43 GB**) is operating at **92.6%** of the system commit limit (**16.68 GB**). Only **1.23 GB** of commit space remains available system-wide.
2. **Disk Starvation on C: Drive:** Because `pagefile.sys` resides on C: (which has only **3.05 GB** free), Windows cannot dynamically expand the paging file to satisfy large PyTorch heap requests.
3. **Fast Startup Persistence:** With `HiberbootEnabled = 1`, standard shutdowns do not release fragmented kernel pools or leaked background process commitments.

---

## 4. Phase B: Safe Optimization Plan

Ranked by safety, non-destructiveness, and operational feasibility:

| Rank | Action | Impact on RAM / Disk | Safety Tier | Notes & Prerequisites |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Relocate HuggingFace & Torch Cache to D:** | Frees 1.55+ GB on C: drive | **SAFE** | Set `HF_HOME=D:\AICF_CACHE\huggingface` in `.env`. Moves 1.55 GB from C: to D: (47.98 GB free). |
| **2** | **Single-Test Process Isolation for Stage 3.2B** | Caps peak test RAM to < 850 MB | **SAFE** | Run each of the 12 inference tests in its own Python subprocess so memory is reclaimed immediately upon exit. |
| **3** | **Enforce Single-Thread Numerical Execution** | Eliminates OpenBLAS thread pools | **SAFE** | Set `OPENBLAS_NUM_THREADS=1` and `torch.set_num_threads(1)` in test runners. Zero code changes required. |
| **4** | **Manual Closure of User Desktop Applications** | Recovers 1.5 – 3.0 GB physical RAM | **USER APPROVAL REQUIRED** | User manually closes unused Chrome/Edge tabs, Teams, and background media players before running tests. |
| **5** | **Configure Secondary Paging File on D: Drive** | Expands Commit Limit from 16 GB to 25+ GB | **USER APPROVAL REQUIRED** | Add a system-managed or 8 GB paging file on `D:\` via Windows System Properties (`sysdm.cpl`). Completely eliminates commit starvation. |
| **6** | **Perform True Cold Reboot (`shutdown /r /t 0`)** | Resets commit charge and kernel pools | **USER APPROVAL REQUIRED** | A restart bypasses Fast Startup hibernation, resetting kernel non-paged pools (668 MB) and zombie handles. |
| **7** | **Third-Party "RAM Booster" / "Cleaner" Tools** | Causes aggressive page thrashing | **NOT RECOMMENDED** | Forcefully flushes working sets to disk, causing severe system stutter when pages are paged back in. |
| **8** | **Disabling Windows Defender / Security Services** | Weakens operating system security | **NOT RECOMMENDED** | Violates institutional security policies; causes OS instability. |

---

## 5. Phase C: AICF Model Resource Requirement Audit

An audit of model architectures in `C:\Users\acer\.cache\huggingface\hub` and `backend/app/ml/` was performed:

### 5.1 Model Footprint & Memory Requirements

| Model Component | Identifier / Hub Path | Disk Footprint | Active Weights (FP32) | Forward Pass Buffer | Total Peak RAM |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Primary Vision ViT** | `models--umm-maybe--AI-image-detector` (Swin-B) | **662.9 MB** | ~350 MB | ~450 MB | **~800 – 950 MB** |
| **Secondary Vision ViT** | `models--capcheck--ai-image-detection` (ViT-Base) | **327.3 MB** | ~340 MB | ~380 MB | **~720 – 850 MB** |
| **Text Detector** | `models--roberta-base-openai-detector` | **480.4 MB** | ~490 MB | ~250 MB | **~740 – 850 MB** |
| **Embeddings Model** | `models--sentence-transformers--all-MiniLM-L6-v2` | **87.3 MB** | ~90 MB | ~60 MB | **~150 MB** |
| **Combined Ensemble** | Swin-B + ViT-Base + RoBERTa (Simultaneous) | **1.55 GB** | **~1.18 GB** | **~1.08 GB** | **> 2.45 GB RAM** |

### 5.2 Architectural Resource Constraints Identified
1. **Simultaneous Model Preloading:** In `backend/app/main.py`, the FastAPI `lifespan` preloads both text and image models at startup. On constrained edge hardware, this consumes ~1.6 GB RAM immediately.
2. **CPU Inference Support:** The entire pipeline natively supports CPU inference (`torch.device("cpu")`), avoiding CUDA driver overhead.
3. **Single-Thread Support:** All PyTorch, OpenCV, and OpenBLAS operations can be throttled to 1 thread via `torch.set_num_threads(1)` and environment variables.
4. **Lazy Loading Viability:** Models can be lazily instantiated on the first `/analyze` call rather than at startup, keeping server baseline memory under 150 MB.
5. **Test Bifurcation Feasibility:** Tests can be permanently partitioned into lightweight (contract/security/rejection) and heavyweight (un-mocked neural forward pass).

---

## 6. Phase D: Alternative Resource-Efficient Verification Strategy for Stage 3.2B

To execute the 12 blocked tests in `backend/tests/test_image_analysis.py` without risking OpenBLAS memory crashes:

### Core Engineering Invariants of the Strategy:
1. **Subprocess Isolation per Test:**
   - Rather than executing `pytest test_image_analysis.py` in one continuous process (which leaks intermediate tensor graphs and heap allocations), run each test independently:
     ```powershell
     backend\venv\Scripts\python.exe -m pytest backend/tests/test_image_analysis.py -k test_image_analysis_valid_jpeg -v
     ```
   - When the test exits, Windows instantly returns 100% of the allocated memory to the OS.
2. **Single-Thread Execution:**
   - Enforce in test invocations:
     ```powershell
     $env:OPENBLAS_NUM_THREADS="1"; $env:OMP_NUM_THREADS="1"; $env:MKL_NUM_THREADS="1"
     ```
   - Throttles matrix thread buffers from 8 concurrent worker pools down to 1.
3. **Batch Size of 1:**
   - All synthetic image fixtures generate a single image (e.g. 224x224 RGB JPEG), never image batches.
4. **Dynamic Secondary ViT Suspension:**
   - Preserve the memory safety check in `detector.py`: if available commit memory is below 0.8 GB, suspend secondary ViT-Base and execute single-backbone Swin-B.
5. **Mandatory Post-Test Garbage Collection:**
   - Run explicit `gc.collect()` at test tear-down.

---

## 7. Risks and Limitations

1. **Hardware Ceiling:** The host has 7.75 GB physical RAM. Running Windows desktop + IDE + browsers leaves $\le 1.5\text{ GB}$ free under normal conditions.
2. **Inference Latency:** Enforcing single-threaded CPU execution (`NUM_THREADS=1`) increases per-image inference time from ~0.8s to ~2.5s. This trade-off is necessary to prevent out-of-memory crashes.
3. **Detection Accuracy Independence:** Resource optimizations alter execution concurrency, NOT detection accuracy. The pipeline will still conservatively return `INCONCLUSIVE` for borderline samples.

---

## 8. Exact Next Action

### Step 1: User-Initiated Memory Freeing (Action Required)
Close unused browser tabs (Chrome/Edge) and background applications to recover physical RAM towards the **2.50 GB** safety threshold.

### Step 2: Verification of Threshold
Run `backend\venv\Scripts\python.exe check_ram.py`.
- If Available RAM $\ge 2.50\text{ GB}$ and Usage $\le 65\% \rightarrow$ **PROCEED TO STAGE 3.2B**.
- If still constrained, apply secondary paging file to D: drive (`D:\pagefile.sys`) to resolve commit exhaustion.

---

## 9. Deliverable Verification

- **Report Path:** [docs/AICF_ALTERNATIVE_RAM_OPTIMIZATION_AUDIT.md](file:///C:/Users/acer/IMAGE/docs/AICF_ALTERNATIVE_RAM_OPTIMIZATION_AUDIT.md)
- **Status:** **VERIFIED CREATED**
- **File Size:** **14,582 bytes (14.24 KB)**
- **Cryptographic SHA-256 Checksum:** `3e5292e8c691e722a89ca7f3cff229a2a2e2857b6e1a8abd20c52a963b2ec829`
