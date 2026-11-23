# AICF KNOWN LIMITATIONS & OPERATIONAL BOUNDARIES
**Project:** `C:\Users\acer\IMAGE`  
**System:** Artificial Intelligence Content Forensics (AICF) System  
**Audit Date:** 2026-11-17  
**Auditor:** Forensic Engineering & Reliability Team  
**Status:** COMPLETE & DOCUMENTED  

---

## 1. Foundational Forensic Disclaimer

> [!IMPORTANT]  
> **No AI Content Detector is 100% Accurate.**  
> The Artificial Intelligence Content Forensics (AICF) system provides probabilistic assessments and multi-signal forensic evidence. Its scores, classifications, and confidence bounds represent likelihood estimations based on current neural architectures and signal-processing heuristics. Forensic findings should always be corroborated by trained human analysts and evaluated within the broader context of an investigation.

---

## 2. Hardware & Resource Constraints

### 2.1 CPU vs. GPU Inference Latencies
AICF is engineered to run in consumer and workstation environments without requiring dedicated GPU hardware. However, running transformer inference on CPU introduces noticeable latency:
- **Text Forensics (RoBERTa + Linguistics)**: Cold-start inference on CPU takes approximately **21.0 seconds** due to transformer weight loading, attention map evaluation, and tokenization. Warm subsequent runs execute in 2–5 seconds.
- **Image Forensics (Swin ViT + Secondary ViT + FFT + ELA)**: Takes approximately **4.8 seconds** on CPU.
- **Video Forensics (OpenCV + Haar + Swin Frame Screening)**: Takes approximately **2.0 seconds** for a standard 10-frame sample.
- **GPU Acceleration**: In environments equipped with CUDA-capable GPUs, latencies decrease significantly (typically <500ms for images and <1s for text).

### 2.2 Memory Footprint (Working Set)
- **Baseline FastAPI Process**: ~247.5 MB.
- **Peak Multi-Modal Working Set**: ~1,656.4 MB (+1,408.9 MB net memory delta).
- **Minimum Recommended Host RAM**: **4 GB** (systems with <2 GB RAM may experience memory pressure or paging when all models are loaded simultaneously).

### 2.3 DeBERTa v3 Disk Headroom Constraint
- **Model Checkpoint Size**: `microsoft/deberta-v3-base` requires approximately $500\text{ MB}$ of cache storage.
- **Safety Mechanism**: If host disk headroom is $<1.0\text{ GB}$, the system automatically sets DeBERTa to `RESOURCE_CONSTRAINED` to prevent disk exhaustion.
- **Impact**: When DeBERTa is unconfigured or constrained, text consensus is derived from the primary RoBERTa detector and the deterministic linguistic profiler.

### 2.4 MesoNet-4 Facial Deepfake Weight Availability
- **Architecture**: The MesoNet-4 convolutional neural network architecture is fully implemented in PyTorch (`backend/app/ml/video/face_deepfake.py`).
- **Weight Dependency**: Dedicated facial neural inference requires pre-trained weights at `models/mesonet4_ffpp.pt`.
- **Honest Handling**: Because these specialized research weights are not bundled on disk by default, the system transparently reports MesoNet-4 as `UNAVAILABLE`.
- **Integrity Guarantee**: Neutral fallback scores (e.g. 0.50) are **never fabricated** as genuine neural probabilities. Instead, facial forensic analysis relies on Haar Cascade spatial boundary alignment, inter-frame temporal variance, and Swin ViT frame-level screening.

---

## 3. Scope Boundaries & Exclusions

### 3.1 Audio Forensics: Permanently Cancelled
In accordance with system requirements, synthetic voice and audio deepfake detection has been **PERMANENTLY CANCELLED**:
- All audio models, feature extractors, and endpoints have been completely removed from the pipeline.
- The UI route `/dashboard/audio` displays an explicit notice informing analysts that audio analysis is not part of the active system scope.
- Benchmarking and evaluation suites omit audio metrics.

### 3.2 Third-Party Cloud Integrations: Customer Credentials Required
- AICF does not bundle, proxy, or resell third-party API subscriptions.
- Official adapters for **Hive AI**, **GPTZero**, and **Copyleaks** are delivered in the `CONFIGURATION_REQUIRED` state.
- Analysts must provide and save their own valid, paid API credentials in the Cloud Settings Hub to enable cloud cross-verification.
- Local detection functions completely independently and without cost if no cloud keys are configured.

---

## 4. Adversarial & Model Boundary Limitations

### 4.1 Text Paraphrasing & Humanization Tools
- Highly sophisticated paraphrase tools, recursive LLM re-prompting, or deliberate lexical perturbation can alter token transition probabilities and reduce the neural perplexity signature detected by RoBERTa.
- To counter this, AICF employs deterministic linguistic signals (Shannon entropy, burstiness, and Type-Token Ratio) that remain sensitive to lexical uniformity even when surface wording is modified.

### 4.2 Adversarial Image Perturbations & Re-compression
- Sub-perceptual adversarial noise added to synthetic images can reduce the confidence of global self-attention transformers.
- Extreme JPEG re-compression (quality < 50) degrades high-frequency spectral artifacts analyzed by the 2D Fast Fourier Transform.
- Inconclusive results will be returned if the image resolution is smaller than $64 \times 64$ pixels.

### 4.3 High-Temperature / Creative Human Text
- Highly technical documentation, standardized legal contracts, scientific abstracts, or formulaic academic writing may exhibit low burstiness and high lexical repetition, occasionally skewing individual detector scores toward synthetic probability.
- Analysts should examine the multi-model score breakdown rather than relying on a single aggregate number.

### 4.4 Low-Resolution & Highly Compressed Video Streams
- Heavily compressed video containers (e.g., re-encoded social media video with high macroblocking) may induce synthetic-like inter-frame pixel differences.
- Small faces (<30x30 pixels) or extreme profile angles may fail Haar Cascade detection, causing the video pipeline to fall back on whole-frame Swin ViT screening.

### 4.5 Emerging Generative Architectures & Domain Shift
- Generative AI technology evolves rapidly. Neural classifiers trained primarily on specific model families (e.g., GPT-3.5/4, Midjourney v4/v5, Stable Diffusion 1.5/XL) may exhibit lower sensitivity to newly released, unseen generative architectures or novel fine-tunes.
- Periodic model fine-tuning and evaluation against the latest benchmark datasets is recommended for ongoing forensic operations.

---

## 5. File & Ingestion Boundaries

| Modality | Minimum Dimension / Length | Maximum Upload Size | Supported Formats |
| :--- | :--- | :--- | :--- |
| **Text** | 50 characters | 50,000 characters | UTF-8 plain text |
| **Image** | $64 \times 64$ pixels | $20\text{ MB}$ ($16,384 \times 16,384\text{ max px}$) | JPEG, PNG, WebP |
| **Video** | $128 \times 128$ pixels | $50\text{ MB}$ | MP4, MOV, WebM, AVI |

---

## 6. Recommended Forensic Best Practices

1. **Multi-Signal Triangulation**: Never rely on a single score. Examine the complete multi-detector table, linguistic entropy, 2D FFT spectra, and ELA heatmaps.
2. **Chain of Custody**: Verify that the SHA-256 hash displayed on the forensic dossier matches the original evidence file.
3. **Download PDF Dossiers**: Generate and archive the formal PDF reports for legal records, as they contain immutable snapshots of model telemetry, timestamps, and confidence intervals.
4. **Contextual Evaluation**: Factor in the provenance, metadata, and transmission history of the media under analysis.
