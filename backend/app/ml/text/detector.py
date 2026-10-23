import hashlib
import logging
import time
from typing import Any

from backend.app.ml.base import BaseDetector
from backend.app.ml.text.features import build_evidence_signals, extract_linguistic_features

logger = logging.getLogger("aicf.ml.text")

# Documented scientific limitations and epistemic boundaries
DEFAULT_TEXT_LIMITATIONS: list[str] = [
    (
        "Probabilistic Assessment: Detector outputs are statistical estimations and do not "
        "constitute legal or definitive proof of authorship."
    ),
    (
        "False Positive Vulnerability: Highly structured academic prose, formal technical "
        "documentation, or non-native English writing may be incorrectly flagged."
    ),
    (
        "Evasion via Paraphrasing: AI-generated text that has been manually edited, paraphrased, "
        "or passed through translation round-trips can evade detection."
    ),
    (
        "Short Sample Sensitivity: Samples with fewer than 50 words lack sufficient token volume "
        "for stable distribution analysis and default to inconclusive boundaries."
    ),
    (
        "Hybrid Authorship: Co-authored content (human drafting with LLM polishing) generates "
        "overlapping linguistic signals that resist binary classification."
    ),
]


class TextForensicsDetector(BaseDetector):
    """Production-grade AI Text Forensics Detector.

    Uses a genuine pretrained sequence classification transformer (RoBERTa fine-tuned for
    AI-generated vs. human text classification) combined with deterministic linguistic
    telemetry (burstiness, lexical diversity, repeated n-grams, and entropy).
    """

    def __init__(
        self,
        model_name: str = "roberta-base-openai-detector",
        version: str = "1.0.0",
        ai_threshold: float = 0.70,
        human_threshold: float = 0.30,
        min_words: int = 15,
        min_chars: int = 50,
    ) -> None:
        super().__init__(name=model_name, media_type="text", version=version)
        self.model_name = model_name
        self.ai_threshold = ai_threshold
        self.human_threshold = human_threshold
        self.min_words = min_words
        self.min_chars = min_chars

        self._tokenizer: Any = None
        self._model: Any = None
        self._is_loaded: bool = False
        self._load_error: str | None = None
        self._device: str = "cpu"

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    def load_model(self) -> bool:
        """Load pretrained tokenizer and model once into memory on CPU."""
        if self._is_loaded and self._model is not None:
            return True

        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(
                "Initializing text classification model '%s' on %s...",
                self.model_name,
                self._device,
            )

            t0 = time.time()
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self._model.to(self._device)
            self._model.eval()

            self._is_loaded = True
            self._load_error = None
            logger.info(
                "Model '%s' successfully loaded in %.2fs on %s.",
                self.model_name,
                time.time() - t0,
                self._device,
            )
            return True
        except Exception as exc:
            self._is_loaded = False
            self._load_error = str(exc)
            logger.warning("Failed to load text detector model '%s': %s", self.model_name, exc)
            return False

    async def analyze(self, payload: Any) -> dict[str, Any]:
        """BaseDetector interface implementation."""
        if not isinstance(payload, str):
            raise TypeError("TextForensicsDetector requires string payload.")
        return self.analyze_text(payload)

    def analyze_text(self, text: str) -> dict[str, Any]:
        """Execute forensic analysis with real model inference and explainable features."""
        start_time = time.time()

        clean_text = text.strip() if text else ""
        char_count = len(clean_text)
        words = clean_text.split()
        word_count = len(words)

        # Input SHA-256 hash for privacy-safe audit trail
        input_hash = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()
        text_snippet = (clean_text[:120] + "...") if len(clean_text) > 120 else clean_text

        # 1. Validation: Empty input check
        if not clean_text or word_count == 0:
            return {
                "status": "FAILED",
                "error": "Text payload is empty. Please provide text for forensic analysis.",
                "classification": "INCONCLUSIVE",
                "confidence_score": 0.0,
                "ai_probability": 0.0,
                "human_probability": 0.0,
                "evidence": [],
                "limitations": DEFAULT_TEXT_LIMITATIONS,
                "word_count": 0,
                "character_count": 0,
                "input_hash": input_hash,
                "text_snippet": "",
                "model_name": self.model_name,
                "model_version": self.version,
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        # Extract deterministic linguistic metrics
        features = extract_linguistic_features(clean_text)

        # 2. Validation: Input too short for reliable statistical evaluation
        if word_count < self.min_words or char_count < self.min_chars:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            short_caveat = (
                f"Sample volume is insufficient ({word_count} words / {char_count} chars). "
                f"Statistical language detection requires a minimum of {self.min_words} words "
                f"(recommended: 50+ words) to avoid false-positive classifications."
            )
            return {
                "status": "INCONCLUSIVE",
                "classification": "INCONCLUSIVE",
                "confidence_score": 0.50,
                "ai_probability": 0.50,
                "human_probability": 0.50,
                "features": features,
                "evidence": [
                    {
                        "signal": "Input Length Gate",
                        "metric": f"{word_count} words / {char_count} chars",
                        "finding": short_caveat,
                    }
                ],
                "limitations": [short_caveat] + DEFAULT_TEXT_LIMITATIONS,
                "word_count": word_count,
                "character_count": char_count,
                "input_hash": input_hash,
                "text_snippet": text_snippet,
                "model_name": self.model_name,
                "model_version": self.version,
                "processing_time_ms": elapsed_ms,
            }

        # 3. Model Availability Check
        if not self._is_loaded or self._model is None or self._tokenizer is None:
            # Attempt on-demand load
            loaded = self.load_model()
            if not loaded or self._model is None or self._tokenizer is None:
                elapsed_ms = round((time.time() - start_time) * 1000, 2)
                error_msg = self._load_error or "Model weights not downloaded or unconfigured."
                return {
                    "status": "BLOCKED",
                    "classification": "INCONCLUSIVE",
                    "confidence_score": None,
                    "ai_probability": None,
                    "human_probability": None,
                    "features": features,
                    "evidence": [],
                    "limitations": [
                        f"Model engine unconfigured or unavailable: {error_msg}",
                        "In compliance with AICF rules, simulated results are disabled.",
                    ] + DEFAULT_TEXT_LIMITATIONS,
                    "word_count": word_count,
                    "character_count": char_count,
                    "input_hash": input_hash,
                    "text_snippet": text_snippet,
                    "model_name": self.model_name,
                    "model_version": self.version,
                    "processing_time_ms": elapsed_ms,
                }

        # 4. Genuine Model Inference
        import torch

        try:
            encoded = self._tokenizer(
                clean_text,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            )
            encoded = {k: v.to(self._device) for k, v in encoded.items()}

            with torch.inference_mode():
                outputs = self._model(**encoded)
                logits = outputs.logits.squeeze(0)
                probs = torch.softmax(logits, dim=-1).tolist()

            id2label = getattr(self._model.config, "id2label", {0: "Fake", 1: "Real"})
            first_label = str(id2label.get(0, "Fake")).lower()

            if "real" in first_label or "human" in first_label:
                human_prob = float(probs[0])
                ai_prob = float(probs[1]) if len(probs) > 1 else float(1.0 - probs[0])
            else:
                ai_prob = float(probs[0])
                human_prob = float(probs[1]) if len(probs) > 1 else float(1.0 - probs[0])

            # Apply uncertainty boundaries & calibrated classification thresholds
            if ai_prob >= self.ai_threshold:
                classification = "LIKELY AI-GENERATED"
                confidence_score = round(ai_prob, 4)
            elif ai_prob <= self.human_threshold:
                classification = "LIKELY HUMAN"
                confidence_score = round(human_prob, 4)
            else:
                classification = "INCONCLUSIVE"
                confidence_score = round(max(ai_prob, human_prob), 4)

            # Enforce INCONCLUSIVE for short samples under 40 words
            if word_count < 40 and classification != "INCONCLUSIVE":
                classification = "INCONCLUSIVE"

            evidence = build_evidence_signals(ai_prob, human_prob, features)
            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            return {
                "status": "SUCCESS",
                "classification": classification,
                "confidence_score": confidence_score,
                "ai_probability": round(ai_prob, 4),
                "human_probability": round(human_prob, 4),
                "features": features,
                "evidence": evidence,
                "limitations": DEFAULT_TEXT_LIMITATIONS,
                "word_count": word_count,
                "character_count": char_count,
                "input_hash": input_hash,
                "text_snippet": text_snippet,
                "model_name": self.model_name,
                "model_version": self.version,
                "processing_time_ms": elapsed_ms,
            }

        except Exception as exc:
            logger.error("Inference execution failed: %s", exc, exc_info=True)
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            return {
                "status": "FAILED",
                "error": "An internal inference error occurred while processing the text.",
                "classification": "INCONCLUSIVE",
                "confidence_score": None,
                "ai_probability": None,
                "human_probability": None,
                "features": features,
                "evidence": [],
                "limitations": DEFAULT_TEXT_LIMITATIONS,
                "word_count": word_count,
                "character_count": char_count,
                "input_hash": input_hash,
                "text_snippet": text_snippet,
                "model_name": self.model_name,
                "model_version": self.version,
                "processing_time_ms": elapsed_ms,
            }


# Global singleton detector instance
text_detector = TextForensicsDetector()
