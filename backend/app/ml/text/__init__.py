"""Modular Text Forensics Engine."""

from backend.app.ml.text.detector import (
    DEFAULT_TEXT_LIMITATIONS,
    DebertaTextDetector,
    RobertaTextDetector,
    TextForensicsDetector,
    text_detector,
)
from backend.app.ml.text.ensemble import (
    ENSEMBLE_LIMITATIONS,
    TextEnsembleAggregator,
    check_system_resources,
)
from backend.app.ml.text.features import (
    build_evidence_signals,
    extract_linguistic_features,
)

__all__ = [
    "TextForensicsDetector",
    "text_detector",
    "RobertaTextDetector",
    "DebertaTextDetector",
    "TextEnsembleAggregator",
    "check_system_resources",
    "DEFAULT_TEXT_LIMITATIONS",
    "ENSEMBLE_LIMITATIONS",
    "extract_linguistic_features",
    "build_evidence_signals",
]
