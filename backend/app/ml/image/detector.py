"""Production-grade AI Image Forensics Detector implementing BaseDetector.

Combines genuine deep representation classification (Swin Transformer fine-tuned
for AI-generated vs. authentic image discrimination) with deterministic 2D Fourier
frequency domain analysis, Laplacian noise residuals, and provenance telemetry.
"""

import hashlib
import io
import logging
import time
from typing import Any

from backend.app.ml.base import BaseDetector
from backend.app.ml.image.features import (
    build_image_evidence,
    compute_frequency_domain_features,
    compute_noise_residual_variance,
    extract_metadata_and_provenance,
)
from PIL import Image

logger = logging.getLogger("aicf.ml.image")

DEFAULT_IMAGE_LIMITATIONS: list[str] = [
    (
        "Probabilistic Assessment: Detector outputs are statistical feature estimates and do not "
        "constitute definitive or legal proof of artificial generation."
    ),
    (
        "Resolution & Re-compression Sensitivity: Aggressive JPEG re-compression, downscaling, "
        "or social media transcoding degrades high-frequency pixel artifacts and model confidence."
    ),
    (
        "Domain Shift & Novel Generators: Generative architectures (newer diffusion, "
        "flow-matching, or fine-tunes) outside training distribution may yield lower certainty."
    ),
    (
        "Hybrid & Inpainted Content: Real photographs containing localized generative inpainting "
        "or retouching generate conflicting signals that can produce inconclusive scores."
    ),
    (
        "Provenance Boundaries: The absence of camera EXIF or C2PA credentials is ubiquitous "
        "across the web and does not constitute evidence of artificial generation."
    ),
]


class ImageForensicsDetector(BaseDetector):
    """Production AI Image Forensics Detector.

    Integrates Swin Transformer image classifier with deterministic frequency
    and provenance telemetry. Strictly adheres to AICF scientific honesty rules.
    """

    def __init__(
        self,
        model_name: str = "umm-maybe/AI-image-detector",
        version: str = "1.0.0",
        ai_threshold: float = 0.70,
        human_threshold: float = 0.30,
        min_dimension: int = 32,
    ) -> None:
        super().__init__(name=model_name, media_type="image", version=version)
        self.model_name = model_name
        self.ai_threshold = ai_threshold
        self.human_threshold = human_threshold
        self.min_dimension = min_dimension

        self._processor: Any = None
        self._model: Any = None
        self._is_loaded: bool = False
        self._load_error: str | None = None
        self._device: str = "cpu"

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    def load_model(self) -> bool:
        """Load pretrained vision transformer and image processor into memory."""
        if self._is_loaded and self._model is not None and self._processor is not None:
            return True

        try:
            import torch
            from transformers import AutoImageProcessor, AutoModelForImageClassification

            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(
                "Initializing image classification model '%s' on %s...",
                self.model_name,
                self._device,
            )

            t0 = time.time()
            self._processor = AutoImageProcessor.from_pretrained(self.model_name)
            self._model = AutoModelForImageClassification.from_pretrained(self.model_name)
            self._model.to(self._device)
            self._model.eval()

            self._is_loaded = True
            self._load_error = None
            logger.info(
                "Image model '%s' successfully loaded in %.2fs on %s.",
                self.model_name,
                time.time() - t0,
                self._device,
            )
            return True

        except Exception as exc:
            self._is_loaded = False
            self._load_error = str(exc)
            logger.warning("Failed to load image detector model '%s': %s", self.model_name, exc)
            return False

    async def analyze(self, payload: Any) -> dict[str, Any]:
        """BaseDetector interface implementation."""
        if isinstance(payload, bytes):
            return self.analyze_image_bytes(payload)
        elif isinstance(payload, Image.Image):
            buf = io.BytesIO()
            payload.save(buf, format="PNG")
            return self.analyze_image_bytes(buf.getvalue(), file_name="image.png")
        else:
            raise TypeError("ImageForensicsDetector requires raw image bytes or PIL.Image.")

    def analyze_image_bytes(
        self,
        image_bytes: bytes,
        file_name: str = "uploaded_image",
    ) -> dict[str, Any]:
        """Execute forensic analysis on raw image bytes."""
        start_time = time.time()
        file_size = len(image_bytes)

        # 1. Calculate SHA-256 hash for forensic chain-of-custody
        file_hash = hashlib.sha256(image_bytes).hexdigest()

        # 2. Check for empty payload
        if not image_bytes or file_size == 0:
            return {
                "status": "FAILED",
                "error": "Image payload is empty (0 bytes received).",
                "classification": "INCONCLUSIVE",
                "confidence_score": 0.0,
                "ai_probability": 0.0,
                "human_probability": 0.0,
                "evidence": [],
                "limitations": DEFAULT_IMAGE_LIMITATIONS,
                "file_hash": file_hash,
                "file_name": file_name,
                "file_size_bytes": 0,
                "image_width": 0,
                "image_height": 0,
                "image_format": "UNKNOWN",
                "model_name": self.model_name,
                "model_version": self.version,
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        # 3. Decode and validate raster image safely with Pillow
        try:
            pil_img = Image.open(io.BytesIO(image_bytes))
            pil_img.load()  # Force raster decoding into memory
            img_format = (pil_img.format or "UNKNOWN").upper()
            width, height = pil_img.size
        except Exception as decode_err:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            logger.warning("Image decoding failed for %s: %s", file_name, decode_err)
            return {
                "status": "FAILED",
                "error": (
                    f"Failed to decode image bytes. Corrupted or unsupported format: {decode_err}"
                ),
                "classification": "INCONCLUSIVE",
                "confidence_score": 0.0,
                "ai_probability": 0.0,
                "human_probability": 0.0,
                "evidence": [],
                "limitations": DEFAULT_IMAGE_LIMITATIONS,
                "file_hash": file_hash,
                "file_name": file_name,
                "file_size_bytes": file_size,
                "image_width": 0,
                "image_height": 0,
                "image_format": "CORRUPTED",
                "model_name": self.model_name,
                "model_version": self.version,
                "processing_time_ms": elapsed_ms,
            }

        # 4. Extract deterministic spatial, frequency, and provenance features
        provenance = extract_metadata_and_provenance(pil_img, image_bytes)
        fft_features = compute_frequency_domain_features(pil_img)
        noise_features = compute_noise_residual_variance(pil_img)

        # 5. Check dimension gates
        if width < self.min_dimension or height < self.min_dimension:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            res_caveat = (
                f"Image dimensions ({width}x{height}) fall below minimum forensic threshold "
                f"({self.min_dimension}x{self.min_dimension}). Insufficient pixel patches for "
                f"vision transformer receptive field."
            )
            return {
                "status": "INCONCLUSIVE",
                "classification": "INCONCLUSIVE",
                "confidence_score": 0.50,
                "ai_probability": 0.50,
                "human_probability": 0.50,
                "fft_features": fft_features,
                "noise_features": noise_features,
                "provenance": provenance,
                "evidence": [
                    {
                        "signal": "Spatial Resolution Gate",
                        "metric": f"{width}x{height} pixels",
                        "finding": res_caveat,
                    }
                ],
                "limitations": [res_caveat] + DEFAULT_IMAGE_LIMITATIONS,
                "file_hash": file_hash,
                "file_name": file_name,
                "file_size_bytes": file_size,
                "image_width": width,
                "image_height": height,
                "image_format": img_format,
                "model_name": self.model_name,
                "model_version": self.version,
                "processing_time_ms": elapsed_ms,
            }

        # 6. Ensure model is loaded
        if not self._is_loaded or self._model is None or self._processor is None:
            loaded = self.load_model()
            if not loaded or self._model is None or self._processor is None:
                elapsed_ms = round((time.time() - start_time) * 1000, 2)
                error_msg = self._load_error or "Model weights not downloaded or unconfigured."
                return {
                    "status": "BLOCKED",
                    "classification": "INCONCLUSIVE",
                    "confidence_score": None,
                    "ai_probability": None,
                    "human_probability": None,
                    "fft_features": fft_features,
                    "noise_features": noise_features,
                    "provenance": provenance,
                    "evidence": [],
                    "limitations": [
                        f"Image detection model unavailable: {error_msg}",
                        "In compliance with AICF rules, simulated results are disabled.",
                    ] + DEFAULT_IMAGE_LIMITATIONS,
                    "file_hash": file_hash,
                    "file_name": file_name,
                    "file_size_bytes": file_size,
                    "image_width": width,
                    "image_height": height,
                    "image_format": img_format,
                    "model_name": self.model_name,
                    "model_version": self.version,
                    "processing_time_ms": elapsed_ms,
                }

        # 7. Execute genuine model inference
        import torch

        try:
            # Ensure RGB mode for standard vision transformer input
            rgb_img = pil_img.convert("RGB")
            inputs = self._processor(images=rgb_img, return_tensors="pt")
            inputs = {k: v.to(self._device) for k, v in inputs.items()}

            with torch.inference_mode():
                outputs = self._model(**inputs)
                logits = outputs.logits.squeeze(0)
                probs = torch.softmax(logits, dim=-1).tolist()

            # umm-maybe/AI-image-detector id2label: {0: 'artificial', 1: 'human'}
            id2label = getattr(self._model.config, "id2label", {0: "artificial", 1: "human"})
            label_0 = str(id2label.get(0, "artificial")).lower()

            if "artif" in label_0 or "fake" in label_0 or "ai" in label_0:
                ai_prob = float(probs[0])
                human_prob = float(probs[1]) if len(probs) > 1 else float(1.0 - probs[0])
            else:
                human_prob = float(probs[0])
                ai_prob = float(probs[1]) if len(probs) > 1 else float(1.0 - probs[0])

            # Apply calibrated classification boundaries
            if ai_prob >= self.ai_threshold:
                classification = "LIKELY AI-GENERATED"
                confidence_score = round(ai_prob, 4)
            elif ai_prob <= self.human_threshold:
                classification = "LIKELY HUMAN"
                confidence_score = round(human_prob, 4)
            else:
                classification = "INCONCLUSIVE"
                confidence_score = round(max(ai_prob, human_prob), 4)

            # Enforce INCONCLUSIVE for low-res images under 64x64
            if (width < 64 or height < 64) and classification != "INCONCLUSIVE":
                classification = "INCONCLUSIVE"

            evidence = build_image_evidence(
                ai_prob=ai_prob,
                human_prob=human_prob,
                fft_features=fft_features,
                noise_features=noise_features,
                provenance=provenance,
            )

            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            return {
                "status": "SUCCESS",
                "classification": classification,
                "confidence_score": confidence_score,
                "ai_probability": round(ai_prob, 4),
                "human_probability": round(human_prob, 4),
                "raw_score": round(ai_prob, 4),
                "fft_features": fft_features,
                "noise_features": noise_features,
                "provenance": provenance,
                "evidence": evidence,
                "limitations": DEFAULT_IMAGE_LIMITATIONS,
                "file_hash": file_hash,
                "file_name": file_name,
                "file_size_bytes": file_size,
                "image_width": width,
                "image_height": height,
                "image_format": img_format,
                "model_name": self.model_name,
                "model_version": self.version,
                "processing_time_ms": elapsed_ms,
            }

        except Exception as exc:
            logger.error("Image inference execution failed: %s", exc, exc_info=True)
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            return {
                "status": "FAILED",
                "error": "An internal inference error occurred while analyzing the image.",
                "classification": "INCONCLUSIVE",
                "confidence_score": None,
                "ai_probability": None,
                "human_probability": None,
                "fft_features": fft_features,
                "noise_features": noise_features,
                "provenance": provenance,
                "evidence": [],
                "limitations": DEFAULT_IMAGE_LIMITATIONS,
                "file_hash": file_hash,
                "file_name": file_name,
                "file_size_bytes": file_size,
                "image_width": width,
                "image_height": height,
                "image_format": img_format,
                "model_name": self.model_name,
                "model_version": self.version,
                "processing_time_ms": elapsed_ms,
            }


# Global singleton detector instance
image_detector = ImageForensicsDetector()
