"""Modular AI/ML Forensics Architecture.

This module encapsulates all forensic detection algorithms, pipelines,
feature extractors, and model runtimes isolated from the API and DB layers.
"""

from backend.app.ml.base import BaseDetector

__all__ = ["BaseDetector"]
