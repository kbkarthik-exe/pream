from abc import ABC, abstractmethod
from typing import Any


class BaseDetector(ABC):
    """Abstract base class for all forensic media detection pipelines.

    Guarantees architectural separation between AI models and API routes.
    """

    def __init__(self, name: str, media_type: str, version: str = "0.1.0") -> None:
        self.name = name
        self.media_type = media_type
        self.version = version

    @abstractmethod
    async def analyze(self, payload: Any) -> dict[str, Any]:
        """Execute forensic analysis on raw payload.

        Must be implemented by concrete media detectors in future steps.
        """
        raise NotImplementedError("Detection pipelines must be implemented in concrete modules.")

    def get_metadata(self) -> dict[str, Any]:
        """Return detector metadata and mandatory scientific disclaimers."""
        return {
            "name": self.name,
            "media_type": self.media_type,
            "version": self.version,
            "accuracy_disclaimer": (
                "Forensic detectors produce probabilistic estimations and confidence intervals. "
                "No detector provides 100% certainty of human or AI authorship."
            ),
        }
