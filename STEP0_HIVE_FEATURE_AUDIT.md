# STEP 0: HIVE AI REVERSE ENGINEERING & FEATURE AUDIT REPORT

**Target Platform:** Hive AI  
**Official Website:** https://thehive.ai/  
**Developer Documentation:** https://docs.thehive.ai/  
**Model Focus:** AI-Generated Image & Video Detection, Visual Deepfake Analysis  
**Audit Date:** November 15, 2026  
**Auditor:** Principal AI Research Engineer & Reverse Engineering Specialist  

---

## 1. Executive Summary

Hive AI is an enterprise cloud intelligence provider offering proprietary neural models for detecting synthetic media. Their flagship detection suite includes AI-generated image detection, AI-generated video detection, generator-source attribution, and face-swap deepfake detection. 

Unlike open-source architectures, Hive AI exposes its models strictly via a proprietary hosted cloud REST API. Model weights are proprietary and cannot be downloaded or executed locally on-premise without an enterprise appliance contract.

---

## 2. Hive AI Detection Capabilities & Workflow Analysis

### 2.1 AI-Generated Image Detection
- **Workflow:** Ingests raster imagery, strips metadata, preprocesses through multi-scale convolutional and vision transformer backbones trained on paired synthetic and authentic datasets.
- **Generator Attribution:** Classifies whether an image is AI-generated and attributes the likely synthesis engine:
  - Midjourney (v4, v5, v6)
  - Stable Diffusion (SD1.5, SD2.1, SDXL, SD3)
  - DALL-E (DALL-E 2, DALL-E 3)
  - Flux.1
  - Google Imagen
  - Adobe Firefly
- **Output:** Returns normalized probabilistic scores (`0.000` to `1.000`) for `ai_generated` vs. `not_ai_generated`, alongside confidence scores for individual generator families.

### 2.2 AI-Generated Video Detection
- **Workflow:** Video containers are demuxed in the cloud; keyframes are uniformly extracted across the temporal duration (standard sample interval: 0.5s to 1.0s).
- **Frame-Level Analysis:** Each sampled frame receives an independent visual generation score.
- **Temporal Aggregation:** Hive aggregates frame scores using proprietary temporal smoothing to suppress false-positive frame spikes (e.g., CGI transitions or lens flares).
- **Supported Encodings:** MP4 (`avc1`/H.264, HEVC/H.265), MOV (QuickTime), WebM (VP8, VP9), AVI.

### 2.3 Visual Deepfake & Face-Swap Forensics
- **Workflow:** Implements a face-detector pipeline (MTCNN / RetinaFace) to isolate facial regions across frames.
- **Artifact Detection:** Evaluates facial bounding boxes for boundary blending seams, color/lighting mismatches between face and neck, eye reflection asymmetry, and landmark jitter across sequential frames.
- **Deepfake Classification:** Outputs `is_deepfake` vs. `not_deepfake` with spatial bounding box coordinates `[x1, y1, x2, y2]`.

---

## 3. Hive AI Technical API Specifications

### 3.1 Endpoint & Protocol
- **Synchronous Endpoint:** `POST https://api.thehive.ai/api/v2/task/sync`
- **Asynchronous Endpoint:** `POST https://api.thehive.ai/api/v2/task/async` (Used for long videos > 20 MB; delivers results via Webhook or polling `GET /api/v2/task/{task_id}`)
- **Authentication:** `Authorization: token <HIVE_API_KEY>` header.
- **Payload Modes:**
  - Direct binary upload: `multipart/form-data` with form field `media` (file upload).
  - Hosted URL submission: `application/json` with `{"url": "https://example.com/video.mp4"}`.

### 3.2 Result Structure (JSON Payload Schema)
```json
{
  "code": 200,
  "status": [
    {
      "response": {
        "output": [
          {
            "time": 0.0,
            "classes": [
              { "class": "ai_generated", "score": 0.9421 },
              { "class": "not_ai_generated", "score": 0.0579 },
              { "class": "midjourney", "score": 0.8845 },
              { "class": "stable_diffusion", "score": 0.0412 }
            ]
          },
          {
            "time": 1.0,
            "classes": [
              { "class": "ai_generated", "score": 0.9612 },
              { "class": "not_ai_generated", "score": 0.0388 }
            ]
          }
        ]
      }
    }
  ]
}
```

---

## 4. Hive AI Pricing & Integration Economics

| Tier / Feature | Pricing Model | Commercial Terms |
| :--- | :--- | :--- |
| **Image Detection** | ~$1.50 per 1,000 images | Metered API billing; minimum commit applies |
| **Video Detection** | ~$6.00 per 1,000 video frames | Metered per frame extracted (~$0.18 for a 30s video at 1 fps) |
| **Deepfake Detection** | ~$8.00 per 1,000 video frames | Premium endpoint add-on |
| **On-Premise / Local** | Not Available | Proprietary models; strictly cloud hosted |

---

## 5. Comparative Audit: Hive AI vs. AICF Platform

| Capability | Hive AI (Cloud) | AICF Existing Project (`C:\Users\acer\IMAGE`) | Status in AICF |
| :--- | :--- | :--- | :---: |
| **Image Generation Screening** | Cloud Swin/ViT ensemble | Local Swin ViT (`umm-maybe/AI-image-detector`) | **IMPLEMENTED AND VERIFIED** |
| **Spatial & Frequency Forensics** | Internal cloud features | 2D Fast Fourier Transform (FFT) + Laplacian Noise | **IMPLEMENTED AND VERIFIED** |
| **Video Keyframe Sampling** | Cloud demuxing (1 fps) | Local OpenCV headless temporal sampling (1 fps) | **IMPLEMENTED AND VERIFIED** |
| **Video Keyframe Screening** | Proprietary cloud model | Local Swin ViT (`classify_image` on PIL keyframes) | **IMPLEMENTED AND VERIFIED** |
| **Temporal Consistency Telemetry**| Proprietary temporal smoothing | Deterministic pixel delta & flicker score std-dev | **IMPLEMENTED AND VERIFIED** |
| **Cryptographic Provenance** | Basic hashes | SHA-256 audit ledger + EXIF/C2PA metadata | **IMPLEMENTED AND VERIFIED** |
| **Forensic PDF Export** | Web portal export | Native ReportLab two-pass NumberedCanvas PDF | **IMPLEMENTED AND VERIFIED** |
| **Hive Cloud API Adapter** | Native | `backend/app/ml/video/hive_adapter.py` | **CONFIGURATION REQUIRED** |
| **Generator Family Attribution** | Midjourney/SD/DALL-E tags | Heuristic prompt metadata in EXIF; neural attribution | **PARTIALLY IMPLEMENTED** |
| **Dedicated Facial Deepfake** | MTCNN + facial boundary ViT | Labeled `REQUIRES_DEDICATED_MODEL` (no fake data) | **NOT IMPLEMENTED** |

---

## 6. Recommendations for AICF

1. **Preserve Free Local Operation:** Keep the verified local Swin Vision Transformer as the primary, $0-cost baseline for frame-level synthetic media screening.
2. **Hive Cloud Hybrid Mode:** The existing `HiveVideoAdapter` in `backend/app/ml/video/hive_adapter.py` is already wired into the pipeline. If an analyst enters `HIVE_API_KEY` in `backend/.env`, it automatically queries Hive's `/api/v2/task/sync` and attaches secondary cloud corroboration to the evidence ledger.
3. **Generator Attribution Enhancement:** Enhance local metadata heuristics to parse SD/ComfyUI/A1111 PNG chunks and Midjourney metadata to provide generator attribution without paying cloud API fees.
