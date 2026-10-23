"""Deterministic spatial, frequency, and provenance feature extraction for image forensics."""

import re
from typing import Any

import numpy as np
from PIL import ExifTags, Image

# Known signatures of AI generators in metadata
AI_METADATA_PATTERNS = [
    re.compile(r"midjourney", re.IGNORECASE),
    re.compile(r"stable diffusion", re.IGNORECASE),
    re.compile(r"comfyui", re.IGNORECASE),
    re.compile(r"automatic1111", re.IGNORECASE),
    re.compile(r"dall[- ]?e", re.IGNORECASE),
    re.compile(r"novelai", re.IGNORECASE),
    re.compile(r"adobe firefly", re.IGNORECASE),
    re.compile(r"flux\.1", re.IGNORECASE),
    re.compile(r"--v\s+\d", re.IGNORECASE),
    re.compile(r"--ar\s+\d+:\d+", re.IGNORECASE),
]

# C2PA byte markers
C2PA_BYTE_SIGNATURES = [
    b"c2pa",
    b"jumb",
    b"urn:c2pa:",
    b"C2PA",
]


def extract_metadata_and_provenance(
    img: Image.Image, raw_bytes: bytes
) -> dict[str, Any]:
    """Safely extract EXIF tags, PNG textual metadata chunks, and C2PA markers.

    Returns structured provenance info while strictly separating provenance
    findings from machine learning probability scores.
    """
    exif_data: dict[str, Any] = {}
    software: str | None = None
    camera_make: str | None = None
    camera_model: str | None = None
    lens_model: str | None = None
    create_date: str | None = None
    ai_prompt_found: str | None = None
    ai_metadata_detected = False

    # 1. Parse EXIF data if present
    try:
        raw_exif = img.getexif()
        if raw_exif:
            for tag_id, value in raw_exif.items():
                tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                # Normalize values to safe serializable types
                if isinstance(value, bytes):
                    try:
                        str_val = value.decode("utf-8", errors="ignore").strip("\x00")
                        exif_data[tag_name] = str_val
                    except Exception:
                        exif_data[tag_name] = f"<{len(value)} bytes binary>"
                elif isinstance(value, (int, float, str, bool)):
                    exif_data[tag_name] = value
                else:
                    exif_data[tag_name] = str(value)

            software = exif_data.get("Software") or exif_data.get("ProcessingSoftware")
            camera_make = exif_data.get("Make")
            camera_model = exif_data.get("Model")
            lens_model = exif_data.get("LensModel")
            create_date = exif_data.get("DateTime") or exif_data.get("DateTimeOriginal")

            # Check UserComment or ImageDescription for AI indicators
            comment = exif_data.get("UserComment") or exif_data.get("ImageDescription") or ""
            for pat in AI_METADATA_PATTERNS:
                if pat.search(str(comment)) or (software and pat.search(str(software))):
                    ai_metadata_detected = True
                    ai_prompt_found = (
                        str(comment)[:200] if len(str(comment)) > 200 else str(comment)
                    )
                    break
    except Exception:
        exif_data["_exif_error"] = "EXIF parsing encountered non-standard tags"

    # 2. Check PNG textual chunks and info dictionary
    png_info: dict[str, str] = {}
    if hasattr(img, "info") and isinstance(img.info, dict):
        for k, v in img.info.items():
            if isinstance(v, (str, bytes)):
                v_str = v.decode("utf-8", errors="ignore") if isinstance(v, bytes) else str(v)
                png_info[str(k)] = v_str[:500]
                # Check for SD parameters, ComfyUI prompt or workflow
                if str(k).lower() in ("parameters", "prompt", "workflow", "comment"):
                    for pat in AI_METADATA_PATTERNS:
                        if pat.search(v_str):
                            ai_metadata_detected = True
                            if not ai_prompt_found:
                                ai_prompt_found = v_str[:200]
                            break

    # 3. Inspect raw bytes for C2PA Content Credentials markers
    has_c2pa = False
    c2pa_finding = "No embedded C2PA Content Credentials detected in container."
    for sig in C2PA_BYTE_SIGNATURES:
        if sig in raw_bytes[:10000] or sig in raw_bytes[-10000:]:
            has_c2pa = True
            c2pa_finding = "C2PA / JUMBF Content Credentials manifest detected in container."
            break

    # Provenance summary evaluation
    provenance_summary: str
    if ai_metadata_detected:
        provenance_summary = (
            f"Explicit AI generation metadata detected in image header "
            f"(Generator: {software or 'Prompt tags in payload'})."
        )
    elif camera_make and camera_model:
        provenance_summary = (
            f"Physical camera hardware metadata present ({camera_make} {camera_model}). "
            f"Note: EXIF can be preserved or forged."
        )
    elif has_c2pa:
        provenance_summary = (
            "Cryptographic C2PA provenance manifest present. "
            "Inspect content credentials for full historical signing chain."
        )
    else:
        provenance_summary = (
            "No camera EXIF or AI prompt metadata found in container. "
            "Typical for images shared on social media, messaging apps, or web-optimized renders."
        )

    return {
        "has_exif": bool(exif_data),
        "exif_summary": {
            "camera_make": camera_make,
            "camera_model": camera_model,
            "lens_model": lens_model,
            "software": software,
            "create_date": create_date,
        },
        "exif_raw": {k: str(v)[:120] for k, v in list(exif_data.items())[:15]},
        "png_info_keys": list(png_info.keys()),
        "has_ai_metadata": ai_metadata_detected,
        "ai_prompt_snippet": ai_prompt_found,
        "has_c2pa": has_c2pa,
        "c2pa_finding": c2pa_finding,
        "provenance_summary": provenance_summary,
    }


def compute_frequency_domain_features(img: Image.Image) -> dict[str, float]:
    """Compute 2D Fast Fourier Transform (FFT) features on luminance.

    Latent diffusion models often exhibit distinctive high-frequency falloffs
    or regular spectral grid spikes resulting from upscaling convolution kernels.
    """
    # Convert to grayscale luminance
    gray = img.convert("L")
    w, h = gray.size

    # Resize to a canonical size for consistent spectral analysis (e.g., 256x256)
    target_dim = 256
    gray_resized = gray.resize((target_dim, target_dim), Image.Resampling.BILINEAR)
    arr = np.array(gray_resized, dtype=np.float32)

    # Compute 2D FFT and shift zero-frequency to center
    fft = np.fft.fft2(arr)
    fft_shifted = np.fft.fftshift(fft)
    magnitude = np.abs(fft_shifted)
    power = magnitude**2

    # Radial distribution of spectral power
    center_y, center_x = target_dim // 2, target_dim // 2
    y, x = np.ogrid[:target_dim, :target_dim]
    radius_from_center = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)

    max_radius = target_dim / 2.0
    total_power = float(np.sum(power)) + 1e-12

    # High-frequency power: outer 35% of radial spectrum
    high_freq_mask = radius_from_center > (max_radius * 0.65)
    high_freq_power = float(np.sum(power[high_freq_mask]))
    high_freq_ratio = round(high_freq_power / total_power, 4)

    # Mid-frequency power: between 25% and 65% of radial spectrum
    mid_freq_mask = (radius_from_center > (max_radius * 0.25)) & (
        radius_from_center <= (max_radius * 0.65)
    )
    mid_freq_power = float(np.sum(power[mid_freq_mask]))
    mid_freq_ratio = round(mid_freq_power / total_power, 4)

    # Low-frequency power: center 25% of radial spectrum
    low_freq_mask = radius_from_center <= (max_radius * 0.25)
    low_freq_power = float(np.sum(power[low_freq_mask]))
    low_freq_ratio = round(low_freq_power / total_power, 4)

    # Azimuthal spectral symmetry (measure peak variance across 8 radial octants)
    # Generative model upscalers often display cross or checkerboard grid spikes
    octant_powers: list[float] = []
    angle = np.arctan2(y - center_y, x - center_x)
    for i in range(8):
        theta_low = -np.pi + i * (2 * np.pi / 8)
        theta_high = theta_low + (2 * np.pi / 8)
        mask = (angle >= theta_low) & (angle < theta_high) & mid_freq_mask
        octant_powers.append(float(np.mean(power[mask])) if np.any(mask) else 0.0)

    octant_std = float(np.std(octant_powers))
    octant_mean = float(np.mean(octant_powers)) + 1e-12
    spectral_anisotropy = round(octant_std / octant_mean, 4)

    return {
        "low_freq_ratio": low_freq_ratio,
        "mid_freq_ratio": mid_freq_ratio,
        "high_freq_ratio": high_freq_ratio,
        "spectral_anisotropy": spectral_anisotropy,
    }


def compute_noise_residual_variance(img: Image.Image) -> dict[str, float]:
    """Compute local block noise residual variance using local Laplacian filter.

    Synthetic generative imagery typically exhibits unnaturally uniform noise
    distributions or lack of high-frequency sensor noise across flat regions.
    """
    gray = img.convert("L")
    w, h = gray.size
    arr = np.array(gray, dtype=np.float32)

    # Fast spatial filtering via slicing (inner pixels with discrete Laplacian weights)
    if arr.shape[0] > 4 and arr.shape[1] > 4:
        laplacian = (
            arr[:-2, 1:-1]
            + arr[2:, 1:-1]
            + arr[1:-1, :-2]
            + arr[1:-1, 2:]
            - 4.0 * arr[1:-1, 1:-1]
        )
        noise_var = float(np.var(laplacian))
        noise_std = float(np.std(laplacian))
    else:
        noise_var = 0.0
        noise_std = 0.0

    # Color channel cross-correlation (natural images have strong RGB covariance)
    rgb = img.convert("RGB")
    rgb_arr = np.array(rgb, dtype=np.float32)
    r = rgb_arr[:, :, 0].flatten()
    g = rgb_arr[:, :, 1].flatten()
    b = rgb_arr[:, :, 2].flatten()

    rg_corr = float(np.corrcoef(r, g)[0, 1]) if len(r) > 1 else 1.0
    rb_corr = float(np.corrcoef(r, b)[0, 1]) if len(r) > 1 else 1.0
    gb_corr = float(np.corrcoef(g, b)[0, 1]) if len(g) > 1 else 1.0
    avg_channel_corr = round((rg_corr + rb_corr + gb_corr) / 3.0, 4)

    return {
        "noise_variance": round(noise_var, 2),
        "noise_std": round(noise_std, 2),
        "channel_correlation": avg_channel_corr,
    }


def build_image_evidence(
    ai_prob: float,
    human_prob: float,
    fft_features: dict[str, float],
    noise_features: dict[str, float],
    provenance: dict[str, Any],
) -> list[dict[str, Any]]:
    """Synthesize explainable evidence items combining ML and signal processing telemetry."""
    evidence: list[dict[str, Any]] = []

    # 1. Swin Vision Transformer Signal
    ai_pct = f"{(ai_prob * 100):.1f}%"
    human_pct = f"{(human_prob * 100):.1f}%"
    if ai_prob >= 0.70:
        vit_finding = (
            f"Deep spatial patch analysis indicates strong generative synthesis markers "
            f"({ai_pct} synthetic probability). Model identified characteristic latent "
            f"diffusion textural patterns in high-level feature representations."
        )
    elif ai_prob <= 0.30:
        vit_finding = (
            f"Deep spatial patch analysis aligns with authentic human photography "
            f"({human_pct} human/real probability). Textural coherence matches natural captures."
        )
    else:
        vit_finding = (
            f"Swin Vision Transformer produced an ambiguous classification "
            f"(Synthetic: {ai_pct}, Real: {human_pct}). Feature activations fall within the "
            f"epistemic boundary between synthetic generation and authentic photography."
        )
    evidence.append({
        "signal": "Swin Vision Transformer Deep Representation",
        "metric": f"AI: {ai_pct} / Human: {human_pct}",
        "finding": vit_finding,
    })

    # 2. 2D Fourier Spectral Grid Telemetry
    anisotropy = fft_features.get("spectral_anisotropy", 0.0)
    hf_ratio = fft_features.get("high_freq_ratio", 0.0)
    if anisotropy > 0.45:
        fft_finding = (
            f"Elevated spectral anisotropy ({anisotropy:.2f} CV) indicates non-uniform "
            f"directional frequency distribution, commonly associated with transposed convolution "
            f"checkerboard patterns in generative upscalers."
        )
    elif hf_ratio < 0.03:
        fft_finding = (
            f"Significant high-frequency attenuation (HF power: {hf_ratio * 100:.1f}%) observed, "
            f"consistent with autoencoder latent blur or aggressive smoothing filters."
        )
    else:
        fft_finding = (
            f"Radial power spectral distribution is relatively isotropic "
            f"(Anisotropy: {anisotropy:.2f}, HF ratio: {hf_ratio * 100:.1f}%), "
            f"consistent with optical camera lens MTF characteristics."
        )
    evidence.append({
        "signal": "2D Fast Fourier Transform (FFT) Power Spectrum",
        "metric": f"Anisotropy: {anisotropy:.2f} | HF Ratio: {(hf_ratio * 100):.1f}%",
        "finding": fft_finding,
    })

    # 3. High-Pass Noise Residuals & Sensor Noise
    noise_var = noise_features.get("noise_variance", 0.0)
    noise_sd = noise_features.get("noise_std", 0.0)
    if noise_var < 15.0:
        noise_finding = (
            f"Low Laplacian noise variance ({noise_var:.1f}) detected. Lack of natural sensor "
            f"shot noise in uniform regions is a common indicator of synthetic latent diffusion."
        )
    elif noise_var > 350.0:
        noise_finding = (
            f"High spatial gradient variance ({noise_var:.1f}) indicates sharp optical textures, "
            f"film grain, or post-processing sharpening."
        )
    else:
        noise_finding = (
            f"Moderate noise residual variance ({noise_var:.1f}) matches standard CMOS sensor "
            f"characteristics under typical illumination conditions."
        )
    evidence.append({
        "signal": "Laplacian Noise Residual Variance",
        "metric": f"Variance: {noise_var:.1f} | Noise SD: {noise_sd:.1f}",
        "finding": noise_finding,
    })

    # 4. Provenance & Container Telemetry
    evidence.append({
        "signal": "Metadata & Provenance Container Inspection",
        "metric": (
            "AI Prompt Found"
            if provenance.get("has_ai_metadata")
            else ("C2PA Manifest" if provenance.get("has_c2pa") else "Standard Header")
        ),
        "finding": provenance.get("provenance_summary", "Container metadata inspected."),
    })

    return evidence
