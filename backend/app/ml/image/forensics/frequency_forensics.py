"""Frequency-domain forensics: 2D Fourier (FFT) spectral analysis and resampling indicators."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from PIL import Image

from .schemas import EvidenceFinding, Reliability, Severity


def analyze_frequency_domain(
    image: Image.Image,
) -> tuple[dict[str, Any], list[EvidenceFinding]]:
    """Perform 2D Fourier spectral analysis to detect grid harmonics and resampling artifacts.

    Returns:
        tuple of (frequency_metrics_dict, list_of_evidence_findings)
    """
    findings: list[EvidenceFinding] = []

    # Convert to grayscale luminance array
    gray_img = image.convert("L")
    arr = np.array(gray_img, dtype=np.float32)

    h, w = arr.shape
    if h < 32 or w < 32:
        return {
            "status": "INSUFFICIENT_DIMENSIONS",
            "anisotropy_ratio": 0.0,
            "has_grid_harmonics": False,
        }, [
            EvidenceFinding(
                source="FREQUENCY_FOURIER",
                description="Image dimensions below minimum 32x32 threshold for Fourier spectral analysis.",
                severity=Severity.INFORMATIONAL,
                reliability=Reliability.HEURISTIC,
                limitations=["Frequency domain decomposition requires sufficient spatial extent."],
            )
        ]

    # Compute 2D Fast Fourier Transform
    fft = np.fft.fft2(arr)
    fft_shift = np.fft.fftshift(fft)
    magnitude_spectrum = np.abs(fft_shift)
    # Log power spectrum
    power_spectrum = np.log1p(magnitude_spectrum)

    cy, cx = h // 2, w // 2
    y_coords, x_coords = np.ogrid[:h, :w]
    radii = np.sqrt((x_coords - cx) ** 2 + (y_coords - cy) ** 2)
    max_radius = min(cx, cy)

    if max_radius < 8:
        max_radius = 8

    # 1. Radial Power Bands (Low, Mid, High frequencies)
    low_mask = radii <= (max_radius * 0.25)
    mid_mask = (radii > (max_radius * 0.25)) & (radii <= (max_radius * 0.65))
    high_mask = (radii > (max_radius * 0.65)) & (radii <= max_radius)

    total_power = float(np.sum(power_spectrum))
    low_power = float(np.sum(power_spectrum[low_mask])) / (total_power + 1e-9)
    mid_power = float(np.sum(power_spectrum[mid_mask])) / (total_power + 1e-9)
    high_power = float(np.sum(power_spectrum[high_mask])) / (total_power + 1e-9)

    # 2. 8-Octant Azimuthal Anisotropy
    angles = np.arctan2(y_coords - cy, x_coords - cx)  # [-pi, pi]
    octant_powers: list[float] = []
    for i in range(8):
        theta_min = -math.pi + i * (math.pi / 4.0)
        theta_max = theta_min + (math.pi / 4.0)
        oct_mask = (angles >= theta_min) & (angles < theta_max) & (radii > (max_radius * 0.20)) & (radii <= max_radius)
        oct_power = float(np.mean(power_spectrum[oct_mask])) if np.any(oct_mask) else 0.0
        octant_powers.append(oct_power)

    oct_mean = float(np.mean(octant_powers))
    oct_std = float(np.std(octant_powers))
    anisotropy_ratio = float(oct_std / (oct_mean + 1e-9))

    # 3. Detect Periodic Grid Harmonics (Lattice Spikes)
    # High-pass filter central DC component, then look for outlier peaks in high frequencies
    high_freq_region = power_spectrum[high_mask]
    has_grid_harmonics = False
    harmonic_zscore = 0.0
    if len(high_freq_region) > 50:
        hf_mean = float(np.mean(high_freq_region))
        hf_std = float(np.std(high_freq_region))
        hf_max = float(np.max(high_freq_region))
        harmonic_zscore = float((hf_max - hf_mean) / (hf_std + 1e-9))
        if harmonic_zscore > 4.5 and anisotropy_ratio > 0.45:
            has_grid_harmonics = True

    if has_grid_harmonics:
        findings.append(
            EvidenceFinding(
                source="FREQUENCY_FOURIER",
                description=(
                    f"Periodic lattice frequency spikes detected in 2D Fourier spectrum "
                    f"(Anisotropy ratio: {anisotropy_ratio:.3f}, Peak Z-score: {harmonic_zscore:.2f})."
                ),
                severity=Severity.MEDIUM,
                reliability=Reliability.STATISTICAL_SUPPORTED,
                limitations=[
                    "Grid harmonics frequently arise from neural upscalers and transposed convolutions, "
                    "but can also be caused by periodic geometric textures, screen captures, or repeated re-scaling.",
                    "Fourier spikes alone do not prove AI generation or manipulation."
                ],
                metadata={"anisotropy_ratio": round(anisotropy_ratio, 4), "harmonic_zscore": round(harmonic_zscore, 2)},
            )
        )

    # 4. Resampling / Interpolation Indicators
    # Resampling introduces periodic zeros or ripples in the derivative of the spectral profile
    radial_profile = []
    step = max(1, int(max_radius / 30))
    for r in range(0, int(max_radius), step):
        r_mask = (radii >= r) & (radii < r + step)
        val = float(np.mean(power_spectrum[r_mask])) if np.any(r_mask) else 0.0
        radial_profile.append(val)

    resampling_detected = False
    if len(radial_profile) > 10:
        diffs = np.diff(radial_profile)
        # Look for non-monotonic oscillatory reversals in high-frequency decay
        oscillations = int(np.sum(np.diff(np.sign(diffs)) != 0))
        if oscillations > 8:
            resampling_detected = True
            findings.append(
                EvidenceFinding(
                    source="FREQUENCY_RESAMPLING",
                    description="Spectral energy oscillations detected, indicating potential affine resizing or resampling.",
                    severity=Severity.LOW,
                    reliability=Reliability.HEURISTIC,
                    limitations=[
                        "Resampling is standard in camera digital zoom, thumbnail generation, and web optimization.",
                        "Does not distinguish between benign downscaling and malicious splicing."
                    ],
                    metadata={"spectral_oscillations": oscillations},
                )
            )

    metrics = {
        "anisotropy_ratio": round(anisotropy_ratio, 4),
        "low_frequency_ratio": round(low_power, 4),
        "mid_frequency_ratio": round(mid_power, 4),
        "high_frequency_ratio": round(high_power, 4),
        "has_grid_harmonics": has_grid_harmonics,
        "resampling_detected": resampling_detected,
    }

    return metrics, findings

