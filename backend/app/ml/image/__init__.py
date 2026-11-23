"""Modular Image Forensics package."""

from backend.app.ml.image.detector import (
    ImageForensicsDetector,
    SwinImageDetector,
    VitImageDetector,
    image_detector,
)
from backend.app.ml.image.ensemble import (
    IMAGE_ENSEMBLE_LIMITATIONS,
    ImageEnsembleAggregator,
    check_system_resources,
)
from backend.app.ml.image.heatmap import (
    compute_error_level_analysis,
    compute_noise_residual_heatmap,
    generate_image_forensic_heatmap,
)
from backend.app.ml.image.hive_adapter import HiveImageAdapter, HiveImageDetectionResult

__all__ = [
    "ImageForensicsDetector",
    "SwinImageDetector",
    "VitImageDetector",
    "image_detector",
    "ImageEnsembleAggregator",
    "check_system_resources",
    "IMAGE_ENSEMBLE_LIMITATIONS",
    "compute_error_level_analysis",
    "compute_noise_residual_heatmap",
    "generate_image_forensic_heatmap",
    "HiveImageAdapter",
    "HiveImageDetectionResult",
]
