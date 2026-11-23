# AICF Phase 2 – Image Input Security Hardening & Decompression Defense

**Document ID:** `DOC-AICF-P2-SEC-001`  
**Date:** November 19, 2026  
**Status:** Completed & Validated (Stage 2.2)  
**Security Classification:** Cybersecurity & Defensive Engineering Specification  
**Reference Code:** `backend/app/ml/image/forensics/security_hardening.py`

---

## 1. Threat Overview: The Image Ingestion Attack Surface

Digital image forensic systems are prime targets for adversarial denial-of-service (DoS) and memory exhaustion attacks. An adversary submitting untrusted byte streams can exploit image parser vulnerabilities before any forensic algorithm or deep learning model executes.

The primary attack vectors addressed in Stage 2.2 include:

1. **Decompression Bombs (Zip-Bombs / Pixel Floods):** An extremely small compressed payload (e.g., a few kilobytes of highly compressed zlib/deflate data) that claims or expands into gigabytes of raw uncompressed pixel data (e.g., $100,000 \times 100,000$ RGBA pixels $\approx 40\text{ GB}$).
2. **Asymmetric Single-Axis Exhaustion:** An image with a normal pixel count but an extreme aspect ratio (e.g., $1 \times 500,000$ pixels) designed to break convolution kernels, matrix reshapes, or cause integer overflow in stride calculations.
3. **Parser Memory Leaks & Incomplete Stream Freeing:** Submitting incomplete or malformed byte streams that hold open file descriptors or intermediate memory allocations.
4. **Adversarial Polyglots:** Files crafted to appear as valid images to metadata extractors while containing malicious embedded payloads or corrupt chunks.

---

## 2. Hardened Security Architecture

To neutralize these threats, AICF Stage 2.2 introduces a **pre-decode binary validation gate** (`security_hardening.py`). This gate inspects raw file headers using byte-level stream parsing *before* invoking high-level image decoders (such as Pillow or OpenCV).

```
[ Untrusted Byte Stream ]
          |
          v
+--------------------------------------------------------------+
| 1. Stream Size Gate (Max 10 MB)                              |
+--------------------------------------------------------------+
          | Pass
          v
+--------------------------------------------------------------+
| 2. Pre-Decode Header Sniffer (Binary struct parsing)         |
|    - PNG  : Parse IHDR chunk (Width, Height)                 |
|    - JPEG : Parse SOF0 / SOF2 markers                        |
|    - WebP : Parse VP8 / VP8L bitstream header                |
+--------------------------------------------------------------+
          | Pass
          v
+--------------------------------------------------------------+
| 3. Safety Bounds Verification                                |
|    - Total Pixels <= 16.77 MegaPixels (4096 x 4096 equivalent)|
|    - Single Axis  <= 8,192 Pixels                            |
|    - Compression Ratio Check (Decompression Bomb Rejection)  |
+--------------------------------------------------------------+
          | Pass
          v
+--------------------------------------------------------------+
| 4. Safe PIL Decode with Strict Resource Caps                 |
|    - Image.MAX_IMAGE_PIXELS = 17,825,792                     |
+--------------------------------------------------------------+
          | Pass
          v
[ Forensic Analysis Pipeline (ELA, Noise, CMFD, Provenance) ]
```

---

## 3. Pre-Decode Dimension Sniffing Implementation

The binary sniffers in `backend/app/ml/image/forensics/security_hardening.py` read only the essential structural bytes without decompressing the scanline data.

### 3.1 PNG Format (ISO/IEC 15948)
- **Signature:** `\x89PNG\r\n\x1a\n` (8 bytes)
- **Chunk:** `IHDR` must immediately follow the signature.
- **Payload Extraction:**
  $$\text{Width} = \mathbf{struct.unpack}(">I", \text{raw}[16:20])[0]$$
  $$\text{Height} = \mathbf{struct.unpack}(">I", \text{raw}[20:24])[0]$$
- **Security Check:** If either dimension exceeds $8,192\text{ px}$ or the product exceeds $16,777,216\text{ px}$, the stream is rejected at byte 24, saving CPU and RAM.

### 3.2 JPEG Format (ITU-T T.81 / ISO/IEC 10918-1)
- **Signature:** `\xFF\xD8` (SOI marker)
- **Marker Traversal:** Walks the JPEG marker segments ($0xFF, \text{marker}$) reading the 16-bit segment length without decoding the entropy-coded entropy stream.
- **Target Markers:** Start of Frame (`SOF0` = $0xC0$, `SOF2` = $0xC2$, progressive).
- **Payload Extraction:**
  $$\text{Height} = \mathbf{struct.unpack}(">H", \text{raw}[idx+5:idx+7])[0]$$
  $$\text{Width} = \mathbf{struct.unpack}(">H", \text{raw}[idx+7:idx+9])[0]$$

### 3.3 WebP Format (RIFF Container / VP8)
- **Container:** `RIFF....WEBP`
- **Sub-formats Handled:**
  - `VP8 ` (Lossy): 16-bit little-endian dimensions at offset 26.
  - `VP8L` (Lossless): 14-bit packed bitstream dimensions at offset 21.

---

## 4. Decompression Bomb Detection Formula

Even if an image header claims valid dimensions, an attacker could craft a payload with an impossible compression ratio. 

The security engine evaluates the **expansion ratio**:

$$\text{Estimated Raw Uncompressed Bytes} = \text{Width} \times \text{Height} \times \text{Channels}$$

$$\text{Expansion Ratio} = \frac{\text{Estimated Raw Bytes}}{\max(\text{Length of Compressed Stream}, 1)}$$

### Safety Policy:
- If $\text{Total Pixels} > 4,000,000$ ($2000 \times 2000$) **AND** $\text{Expansion Ratio} > 120.0$, the image is classified as a suspected **Decompression Bomb**.
- Ingestion is aborted with `SecurityViolationError`, returning status `INSUFFICIENT_EVIDENCE` and logging a forensic security warning.

---

## 5. Quantitative Security Bounds

| Parameter | Conservative Bound | Rationale |
| :--- | :--- | :--- |
| **Max Payload File Size** | $10\text{ MB}$ ($10,485,760\text{ bytes}$) | Standard production web upload limit; prevents HTTP buffer flooding. |
| **Max Total Pixels** | $16,777,216\text{ px}$ ($16.7\text{ MP}$) | Matches $4096 \times 4096$ square; provides adequate resolution for high-end professional cameras while limiting 3-channel float32 memory to $\approx 200\text{ MB}$. |
| **Max Single-Axis Dimension**| $8,192\text{ px}$ | Prevents extreme aspect-ratio attacks (e.g. $1 \times 500,000$) that trigger algorithmic complexity spikes in 2D convolution and Fourier transforms. |
| **PIL Internal Safeguard** | `Image.MAX_IMAGE_PIXELS = 17,825,792` | Explicitly overrides PIL's default ($89,478,485\text{ px}$), ensuring PIL throws a `DecompressionBombError` if downstream libraries attempt to bypass pre-sniffing. |

---

## 6. Automated Security Test Verification

The hardened security subsystem is verified by dedicated automated tests in `backend/tests/test_image_forensics_stage2.py`:

1. **`test_16_decompression_bomb_pre_decode_rejection`:**
   - Constructs a synthetic 50-byte PNG file whose IHDR declares dimensions of $30,000 \times 30,000$ ($900\text{ MP}$, requiring $\approx 3.6\text{ GB}$ uncompressed RAM).
   - Validates that the pre-decode sniffer intercepts the file at byte 24, rejects ingestion, and does not allocate memory.
   - Result: **PASSED (0.01s)**.
2. **`test_17_oversized_single_axis_rejection`:**
   - Constructs a PNG file with dimensions $9,000 \times 100$ ($900\text{ kP}$ total, well below the pixel cap, but exceeding the $8,192\text{ px}$ single-axis limit).
   - Validates that the engine rejects the asymmetric axis before decompression.
   - Result: **PASSED (0.01s)**.
3. **`test_9_invalid_images` & `test_10_conflicting_evidence`:**
   - Validates that empty, truncated, or random pseudo-binary streams are safely handled without throwing uncaught exceptions or leaking file handles.
   - Result: **PASSED**.

