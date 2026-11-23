"""Spatial localization of anomalous regions, bounding box extraction, and quadrant assignment."""

from __future__ import annotations

import numpy as np

from .schemas import SuspiciousRegion


def localize_suspicious_regions(
    anomaly_map: np.ndarray | None,
    width: int,
    height: int,
) -> list[SuspiciousRegion]:
    """Segment spatial anomaly heatmap into discrete suspicious regions with bounding boxes.

    Args:
        anomaly_map: 2D numpy array [height, width] of anomaly intensity values.
        width: Image width in pixels.
        height: Image height in pixels.

    Returns:
        List of SuspiciousRegion objects.
    """
    if anomaly_map is None or height < 32 or width < 32:
        return []

    # Calculate global mean and standard deviation of anomaly map
    mean_val = float(np.mean(anomaly_map))
    std_val = float(np.std(anomaly_map))

    if std_val < 0.5:
        # Uniform anomaly map, no localized clusters
        return []

    threshold = mean_val + 2.2 * std_val
    binary_mask = anomaly_map > threshold

    if not np.any(binary_mask):
        return []

    regions: list[SuspiciousRegion] = []
    mid_y, mid_x = height // 2, width // 2

    # Quadrant partition definitions: (name, y_slice, x_slice, y_offset, x_offset)
    quads = [
        ("Q1_TOP_LEFT", slice(0, mid_y), slice(0, mid_x), 0, 0),
        ("Q2_TOP_RIGHT", slice(0, mid_y), slice(mid_x, width), 0, mid_x),
        ("Q3_BOTTOM_LEFT", slice(mid_y, height), slice(0, mid_x), mid_y, 0),
        ("Q4_BOTTOM_RIGHT", slice(mid_y, height), slice(mid_x, width), mid_y, mid_x),
    ]

    for q_name, y_sl, x_sl, y_off, x_off in quads:
        quad_mask = binary_mask[y_sl, x_sl]
        anomalous_pixel_count = int(np.sum(quad_mask))

        # Require a minimum cluster size (e.g. at least 64 anomalous pixels or 1/1000th of quadrant)
        min_cluster = max(48, int((mid_y * mid_x) * 0.005))
        if anomalous_pixel_count >= min_cluster:
            # Find bounding box within this quadrant
            y_indices, x_indices = np.where(quad_mask)
            ymin = int(np.min(y_indices) + y_off)
            ymax = int(np.max(y_indices) + y_off)
            xmin = int(np.min(x_indices) + x_off)
            xmax = int(np.max(x_indices) + x_off)

            norm_ymin = round(float(ymin / height), 4)
            norm_xmin = round(float(xmin / width), 4)
            norm_ymax = round(float(ymax / height), 4)
            norm_xmax = round(float(xmax / width), 4)

            # Heuristic confidence based on cluster density and peak intensity
            quad_vals = anomaly_map[y_sl, x_sl][quad_mask]
            peak_val = float(np.max(quad_vals)) if len(quad_vals) > 0 else 0.0
            conf = min(0.85, 0.40 + (peak_val / (mean_val + std_val + 1e-4)) * 0.1)

            regions.append(
                SuspiciousRegion(
                    region_id=f"REG_{q_name}",
                    quadrant=q_name,
                    bounding_box=(ymin, xmin, ymax, xmax),
                    normalized_box=(norm_ymin, norm_xmin, norm_ymax, norm_xmax),
                    anomalous_block_count=int(anomalous_pixel_count // 16),
                    primary_indicator="LOCALIZED_COMPRESSION_NOISE_DISCONTINUITY",
                    confidence=round(conf, 3),
                )
            )

    return regions

