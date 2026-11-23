"""Image manipulation forensics: ELA, edge-mask damping, spatial noise residuals, and copy-move detection."""

from __future__ import annotations

import io
from typing import Any

import numpy as np
from PIL import Image

from .schemas import EvidenceFinding, Reliability, Severity


def analyze_manipulation(
    image: Image.Image,
    raw_bytes: bytes,
) -> tuple[dict[str, Any], list[EvidenceFinding], np.ndarray | None]:
    """Execute compression, spatial noise, and copy-move forgery analysis.

    Returns:
        tuple of (manipulation_metrics_dict, list_of_evidence_findings, anomaly_spatial_map)
    """
    findings: list[EvidenceFinding] = []

    # Ensure RGB
    if image.mode != "RGB":
        image = image.convert("RGB")

    width, height = image.size
    if width < 32 or height < 32:
        return {
            "status": "INSUFFICIENT_DIMENSIONS",
            "ela_block_variance": 0.0,
            "noise_variance_gradient": 0.0,
            "copy_move_detected": False,
        }, [
            EvidenceFinding(
                source="MANIPULATION_ANALYSIS",
                description="Image dimensions below minimum 32x32 threshold for manipulation analysis.",
                severity=Severity.INFORMATIONAL,
                reliability=Reliability.HEURISTIC,
                limitations=["Insufficient spatial extent to evaluate local manipulation seams."],
            )
        ], None

    img_arr = np.array(image, dtype=np.float32)

    # -------------------------------------------------------------------------
    # 1. Error Level Analysis (ELA) with Edge-Mask Damping
    # -------------------------------------------------------------------------
    ela_buf = io.BytesIO()
    image.save(ela_buf, format="JPEG", quality=95)
    ela_buf.seek(0)
    recompressed_img = Image.open(ela_buf)
    recomp_arr = np.array(recompressed_img, dtype=np.float32)

    # Compute channel-wise absolute error and max across RGB
    raw_ela_diff = np.abs(img_arr - recomp_arr)
    ela_diff = np.max(raw_ela_diff, axis=2)  # [H, W]

    # Compute high-frequency edge mask using simple finite-difference gradients
    gy, gx = np.gradient(np.mean(img_arr, axis=2))
    edge_magnitude = np.sqrt(gx**2 + gy**2)
    # Normalize edge magnitude to [0, 1]
    edge_norm = edge_magnitude / (np.max(edge_magnitude) + 1e-9)
    # Damping factor: damp ELA where natural sharp edges exist
    edge_damping = 1.0 / (1.0 + 3.0 * edge_norm)
    damped_ela = ela_diff * edge_damping

    # Compute block-level ELA variance across 16x16 macro-blocks
    block_size = 16
    grid_h = height // block_size
    grid_w = width // block_size

    block_variances: list[float] = []
    block_means: list[float] = []
    anomaly_map = np.zeros((height, width), dtype=np.float32)

    if grid_h > 1 and grid_w > 1:
        for r in range(grid_h):
            for c in range(grid_w):
                y1 = r * block_size
                y2 = (r + 1) * block_size
                x1 = c * block_size
                x2 = (c + 1) * block_size
                blk = damped_ela[y1:y2, x1:x2]
                blk_var = float(np.var(blk))
                blk_mean = float(np.mean(blk))
                block_variances.append(blk_var)
                block_means.append(blk_mean)
                anomaly_map[y1:y2, x1:x2] = blk_mean

    overall_ela_mean = float(np.mean(damped_ela))
    overall_ela_var = float(np.var(damped_ela))

    # Evaluate ELA Inconsistency: ratio of peak block mean to overall mean
    peak_ratio = 1.0
    if overall_ela_mean > 0.05 and block_means:
        peak_block_mean = float(np.max(block_means))
        peak_ratio = peak_block_mean / overall_ela_mean

    ela_inconsistency_detected = peak_ratio > 3.2 and overall_ela_var > 4.0

    if ela_inconsistency_detected:
        findings.append(
            EvidenceFinding(
                source="COMPRESSION_ELA",
                description=(
                    f"Localized compression error discontinuity detected (Peak block ratio: {peak_ratio:.2f}x). "
                    f"Indicates localized recompression or pasted graphic element."
                ),
                severity=Severity.MEDIUM,
                reliability=Reliability.HEURISTIC,
                limitations=[
                    "ELA alone does NOT prove manipulation. Legitimate natural edges, high-contrast text, "
                    "or non-uniform lighting can create localized ELA elevation despite edge damping.",
                    "Repeated multi-generation recompression can equalize ELA differences (false negatives)."
                ],
                metadata={"peak_block_ratio": round(peak_ratio, 2), "ela_variance": round(overall_ela_var, 3)},
            )
        )

    # -------------------------------------------------------------------------
    # 2. Spatial Noise Residual Analysis
    # -------------------------------------------------------------------------
    # 3x3 Laplacian kernel on luminance to isolate sensor noise
    gray = 0.2989 * img_arr[:, :, 0] + 0.5870 * img_arr[:, :, 1] + 0.1140 * img_arr[:, :, 2]
    # Simple discrete Laplacian convolution
    lap = np.zeros_like(gray)
    lap[1:-1, 1:-1] = (
        gray[:-2, 1:-1] + gray[2:, 1:-1] + gray[1:-1, :-2] + gray[1:-1, 2:] - 4.0 * gray[1:-1, 1:-1]
    )

    # Divide image into 4 quadrants to measure noise variance gradient
    mid_y, mid_x = height // 2, width // 2
    quad_q1 = lap[:mid_y, :mid_x]
    quad_q2 = lap[:mid_y, mid_x:]
    quad_q3 = lap[mid_y:, :mid_x]
    quad_q4 = lap[mid_y:, mid_x:]

    quad_vars = [
        float(np.var(quad_q1)),
        float(np.var(quad_q2)),
        float(np.var(quad_q3)),
        float(np.var(quad_q4)),
    ]

    min_q_var = min(quad_vars)
    max_q_var = max(quad_vars)
    noise_gradient_ratio = float(max_q_var / (min_q_var + 1e-4)) if min_q_var > 0 else 1.0

    # Evaluate boundary seam discontinuity between quadrants to distinguish optical bokeh from splicing
    seam_h = np.abs(gray[mid_y - 1, :] - gray[mid_y, :])
    seam_v = np.abs(gray[:, mid_x - 1] - gray[:, mid_x])
    mean_seam_step = float((np.mean(seam_h) + np.mean(seam_v)) / 2.0)
    is_sharp_composite_seam = mean_seam_step > 3.5

    noise_splicing_detected = (
        noise_gradient_ratio > 4.5
        and max_q_var > 15.0
        and (is_sharp_composite_seam or noise_gradient_ratio > 8.0)
    )

    if noise_splicing_detected:
        findings.append(
            EvidenceFinding(
                source="NOISE_RESIDUAL",
                description=(
                    f"Sharp inter-quadrant sensor noise variance discrepancy detected "
                    f"(Variance delta ratio: {noise_gradient_ratio:.2f}x, Seam discontinuity: {mean_seam_step:.2f}). "
                    f"Indicates possible compositing from cameras with different ISO/sensor profiles."
                ),
                severity=Severity.HIGH,
                reliability=Reliability.STATISTICAL_SUPPORTED,
                limitations=[
                    "Large flat regions (clear sky, studio backdrop) naturally exhibit lower noise variance "
                    "than detailed foreground textures without any tampering.",
                    "Local depth-of-field blur or bokeh can also induce severe noise variance gradients."
                ],
                metadata={"noise_gradient_ratio": round(noise_gradient_ratio, 2), "quadrant_variances": quad_vars, "seam_step": round(mean_seam_step, 2)},
            )
        )
    elif noise_gradient_ratio > 3.5 and not is_sharp_composite_seam:
        findings.append(
            EvidenceFinding(
                source="NOISE_RESIDUAL",
                description=(
                    f"Inter-quadrant noise variance gradient observed ({noise_gradient_ratio:.2f}x), "
                    f"but quadrant boundary transition is smooth ({mean_seam_step:.2f}), "
                    f"consistent with optical depth-of-field (bokeh) rather than a hard composite splice."
                ),
                severity=Severity.INFORMATIONAL,
                reliability=Reliability.HEURISTIC,
                limitations=["Natural optical depth-of-field naturally attenuates background sensor noise."],
                metadata={"noise_gradient_ratio": round(noise_gradient_ratio, 2), "seam_step": round(mean_seam_step, 2)},
            )
        )

    # -------------------------------------------------------------------------
    # 3. Copy-Move Forgery Detection (CMFD with Shift-Vector Clustering)
    # -------------------------------------------------------------------------
    copy_move_detected = False
    matching_pairs_count = 0
    max_shift_cluster = 0
    # Downsample if image is large for fast bounded execution
    sample_img = gray
    if width > 400 or height > 400:
        sample_img = gray[::2, ::2]

    sh, sw = sample_img.shape
    cm_blk_size = 8
    blocks_h = sh // cm_blk_size
    blocks_w = sw // cm_blk_size
    total_blocks = blocks_h * blocks_w

    cmfd_status = "COMPLETED"

    if blocks_h <= 3 or blocks_w <= 3:
        cmfd_status = "SKIPPED_INSUFFICIENT_DIMENSIONS"
        findings.append(
            EvidenceFinding(
                source="MANIPULATION_COPY_MOVE",
                description=(
                    f"Copy-Move Forgery Detection (CMFD) skipped: Subsampled image dimensions ({sw}x{sh}) "
                    f"yield insufficient block grid ({blocks_h}x{blocks_w} blocks). "
                    f"Cloned region analysis was NOT evaluated."
                ),
                severity=Severity.INFORMATIONAL,
                reliability=Reliability.HEURISTIC,
                limitations=[
                    "Skipped CMFD processing does NOT constitute evidence of no manipulation or authenticity.",
                    "CMFD requires at least 4x4 blocks to evaluate translation vectors.",
                ],
                metadata={
                    "cmfd_status": cmfd_status,
                    "blocks_h": blocks_h,
                    "blocks_w": blocks_w,
                    "total_blocks": total_blocks,
                },
            )
        )
    elif total_blocks >= 4000:
        cmfd_status = "SKIPPED_EXCESSIVE_BLOCKS"
        findings.append(
            EvidenceFinding(
                source="MANIPULATION_COPY_MOVE",
                description=(
                    f"Copy-Move Forgery Detection (CMFD) skipped: Image spatial grid ({blocks_h}x{blocks_w} = {total_blocks} blocks) "
                    f"exceeds the maximum real-time processing limit of 4,000 blocks. "
                    f"Cloned region analysis was NOT evaluated."
                ),
                severity=Severity.INFORMATIONAL,
                reliability=Reliability.HEURISTIC,
                limitations=[
                    "Skipped CMFD processing does NOT constitute evidence of no manipulation or authenticity.",
                    "Large images exceed the O(N log N) pairwise sorting and verification budget (capped at 4,000 blocks).",
                    "Block matching operates on axis-aligned raster blocks; non-robust to rotational transformations (>5 degrees) or significant scaling (>10%).",
                ],
                metadata={
                    "cmfd_status": cmfd_status,
                    "blocks_h": blocks_h,
                    "blocks_w": blocks_w,
                    "total_blocks": total_blocks,
                    "max_block_budget": 4000,
                    "rotation_invariant": False,
                },
            )
        )
    else:
        # Fast block profile extraction
        block_features = []
        block_positions = []
        for r in range(blocks_h):
            for c in range(blocks_w):
                by1 = r * cm_blk_size
                by2 = (r + 1) * cm_blk_size
                bx1 = c * cm_blk_size
                bx2 = (c + 1) * cm_blk_size
                b = sample_img[by1:by2, bx1:bx2]
                b_mean = float(np.mean(b))
                b_std = float(np.std(b))
                # Only analyze textured blocks (skip flat/near-flat backgrounds)
                if b_std > 8.0:
                    block_features.append((b_mean, b_std))
                    block_positions.append((r, c))

        n_blks = len(block_features)
        if n_blks > 10:
            # Lexicographical sort CMFD with translation shift-vector clustering
            features_arr = np.array(block_features, dtype=np.float32)
            positions_arr = np.array(block_positions, dtype=np.int32)
            sort_idx = np.lexsort((features_arr[:, 1], features_arr[:, 0]))
            sorted_feats = features_arr[sort_idx]
            sorted_pos = positions_arr[sort_idx]

            window = 15
            shift_histogram: dict[tuple[int, int], int] = {}
            matching_pairs: list[tuple[tuple[int, int], tuple[int, int], tuple[int, int]]] = []

            for i in range(n_blks):
                m1, s1 = sorted_feats[i]
                r1, c1 = sorted_pos[i]
                for w in range(1, min(window, n_blks - i)):
                    j = i + w
                    m2, s2 = sorted_feats[j]
                    if abs(m1 - m2) > 0.40:
                        break  # sorted on mean, difference will only increase
                    if abs(s1 - s2) < 0.40:
                        r2, c2 = sorted_pos[j]
                        dr = int(r1 - r2)
                        dc = int(c1 - c2)
                        spatial_dist = np.sqrt(dr ** 2 + dc ** 2)
                        if spatial_dist >= 3.0:
                            # Verify pixel-level similarity (Mean Absolute Error) between candidate blocks
                            # Cloned patches have near-identical pixels (MAE ~0), whereas natural textures differ
                            b1_pix = sample_img[r1 * cm_blk_size : (r1 + 1) * cm_blk_size, c1 * cm_blk_size : (c1 + 1) * cm_blk_size]
                            b2_pix = sample_img[r2 * cm_blk_size : (r2 + 1) * cm_blk_size, c2 * cm_blk_size : (c2 + 1) * cm_blk_size]
                            if float(np.mean(np.abs(b1_pix.astype(np.float32) - b2_pix.astype(np.float32)))) < 3.0:
                                matching_pairs_count += 1
                                # Normalize shift vector so dr > 0 or (dr == 0 and dc >= 0)
                                shift_vec = (dr, dc) if dr > 0 or (dr == 0 and dc >= 0) else (-dr, -dc)
                                shift_histogram[shift_vec] = shift_histogram.get(shift_vec, 0) + 1
                                matching_pairs.append(((int(r1), int(c1)), (int(r2), int(c2)), shift_vec))

            # Spatial contiguous component check on dominant shift vector
            has_contiguous_cloned_patch = False
            if shift_histogram:
                dominant_shift, max_shift_cluster = max(shift_histogram.items(), key=lambda x: x[1])
                if max_shift_cluster >= 3:
                    cluster_positions = [
                        p1 for (p1, p2, svec) in matching_pairs if svec == dominant_shift
                    ]
                    neighbor_links = 0
                    for k1 in range(len(cluster_positions)):
                        r_a, c_a = cluster_positions[k1]
                        for k2 in range(k1 + 1, len(cluster_positions)):
                            r_b, c_b = cluster_positions[k2]
                            if abs(r_a - r_b) <= 2 and abs(c_a - c_b) <= 2:
                                neighbor_links += 1
                    if neighbor_links >= 2:
                        has_contiguous_cloned_patch = True

            copy_move_detected = has_contiguous_cloned_patch and max_shift_cluster >= 3

        # Only declare copy-move if a contiguous cloned patch is identified
        if copy_move_detected:
            findings.append(
                EvidenceFinding(
                    source="MANIPULATION_COPY_MOVE",
                    description=(
                        f"Repeated identical texture blocks sharing consistent translation offset detected "
                        f"({matching_pairs_count} pairs, primary shift cluster: {max_shift_cluster} blocks). "
                        f"Indicates cloning or copy-move forgery."
                    ),
                    severity=Severity.HIGH,
                    reliability=Reliability.HEURISTIC,
                    limitations=[
                        "Block matching is strictly axis-aligned and sensitive to rotational transformations (>5 degrees) and scaling (>10%).",
                        "Natural highly repetitive patterns with regular spatial grid spacing can still create shift clusters.",
                    ],
                    metadata={
                        "matching_pairs_count": matching_pairs_count,
                        "max_shift_cluster": max_shift_cluster,
                        "cmfd_status": cmfd_status,
                        "rotation_invariant": False,
                    },
                )
            )

    metrics = {
        "overall_ela_mean": round(overall_ela_mean, 3),
        "overall_ela_variance": round(overall_ela_var, 3),
        "ela_peak_ratio": round(peak_ratio, 2),
        "ela_inconsistency_detected": ela_inconsistency_detected,
        "noise_gradient_ratio": round(noise_gradient_ratio, 2),
        "noise_splicing_detected": noise_splicing_detected,
        "copy_move_detected": copy_move_detected,
        "copy_move_matches": matching_pairs_count,
        "cmfd_status": cmfd_status,
        "cmfd_total_blocks": total_blocks,
        "cmfd_max_block_budget": 4000,
        "cmfd_rotation_invariant": False,
    }

    return metrics, findings, anomaly_map
