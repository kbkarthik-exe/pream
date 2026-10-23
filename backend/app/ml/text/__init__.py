"""Modular Text Forensics Engine."""

from backend.app.ml.text.detector import (
    DEFAULT_TEXT_LIMITATIONS,
    TextForensicsDetector,
    text_detector,
)
from backend.app.ml.text.features import (
    build_evidence_signals,
    extract_linguistic_features,
)

__all__ = [
    "TextForensicsDetector",
    "text_detector",
    "DEFAULT_TEXT_LIMITATIONS",
    "extract_linguistic_features",
    "build_evidence_signals",
]
