import hashlib
import logging
import time
from typing import Any

from backend.app.ml.base import BaseDetector
from backend.app.ml.text.ensemble import (
    ENSEMBLE_LIMITATIONS,
    TextEnsembleAggregator,
    check_system_resources,
)
from backend.app.ml.text.features import build_evidence_signals, extract_linguistic_features

logger = logging.getLogger("aicf.ml.text")

# Documented scientific limitations and epistemic boundaries (backward compatibility)
DEFAULT_TEXT_LIMITATIONS: list[str] = ENSEMBLE_LIMITATIONS


class RobertaTextDetector:
    """Primary neural text sequence classifier based on RoBERTa."""

    def __init__(
        self,
        model_name: str = "roberta-base-openai-detector",
        version: str = "1.0.0",
    ) -> None:
        self.model_name = model_name
        self.version = version
        self._tokenizer: Any = None
        self._model: Any = None
        self._is_loaded: bool = False
        self._load_error: str | None = None
        self._device: str = "cpu"

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @property
    def load_error(self) -> str | None:
        return self._load_error

    def load_model(self) -> bool:
        """Load pretrained tokenizer and model once into memory using low_cpu_mem_usage."""
        if self._is_loaded and self._model is not None:
            return True

        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(
                "Initializing primary text classification model '%s' on %s...",
                self.model_name,
                self._device,
            )

            t0 = time.time()
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name,
                low_cpu_mem_usage=True,
            )
            self._model.to(self._device)
            self._model.eval()

            self._is_loaded = True
            self._load_error = None
            logger.info(
                "Primary model '%s' successfully loaded in %.2fs on %s.",
                self.model_name,
                time.time() - t0,
                self._device,
            )
            return True
        except Exception as exc:
            self._is_loaded = False
            self._load_error = str(exc)
            logger.warning("Failed to load primary text detector model '%s': %s", self.model_name, exc)
            return False

    def infer(self, text: str) -> dict[str, Any]:
        """Execute inference forward pass on text string."""
        if not self._is_loaded or self._model is None or self._tokenizer is None:
            if not self.load_model():
                return {
                    "model_name": self.model_name,
                    "model_version": self.version,
                    "status": "UNAVAILABLE",
                    "status_detail": self._load_error or "Model weights unconfigured.",
                    "ai_probability": None,
                    "human_probability": None,
                    "confidence_score": None,
                    "latency_ms": 0.0,
                    "raw_output": None,
                }

        import torch

        t0 = time.time()
        try:
            encoded = self._tokenizer(
                text,
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

            latency = round((time.time() - t0) * 1000, 2)
            raw_logits = [round(float(l), 4) for l in logits.tolist()]
            raw_probs_list = [round(float(p), 4) for p in probs]
            tokens_evaluated = int(encoded["input_ids"].shape[-1]) if "input_ids" in encoded else len(text.split())

            return {
                "model_name": self.model_name,
                "model_version": self.version,
                "status": "READY",
                "status_detail": f"Inference completed in {latency}ms on {self._device}",
                "ai_probability": round(ai_prob, 4),
                "human_probability": round(human_prob, 4),
                "confidence_score": round(max(ai_prob, human_prob), 4),
                "latency_ms": latency,
                "raw_output": {
                    "logits": raw_logits,
                    "raw_probs": raw_probs_list,
                    "tokens_evaluated": tokens_evaluated,
                    "device": self._device,
                },
            }
        except Exception as exc:
            logger.error("RoBERTa inference failed: %s", exc, exc_info=True)
            return {
                "model_name": self.model_name,
                "model_version": self.version,
                "status": "ERROR",
                "status_detail": str(exc),
                "ai_probability": None,
                "human_probability": None,
                "confidence_score": None,
                "latency_ms": round((time.time() - t0) * 1000, 2),
                "raw_output": None,
            }


class DebertaTextDetector:
    """Secondary neural text detector based on DeBERTa-v3 architecture.

    Features strict resource pre-flight checks to prevent OS Error 1455 / memory starvation.
    Reports status honestly if weights are not downloaded or memory is constrained.
    """

    def __init__(
        self,
        model_name: str = "microsoft/deberta-v3-base",
        version: str = "1.0.0",
    ) -> None:
        self.model_name = model_name
        self.version = version
        self._tokenizer: Any = None
        self._model: Any = None
        self._is_loaded: bool = False
        self._load_error: str | None = None
        self._device: str = "cpu"

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @property
    def load_error(self) -> str | None:
        return self._load_error

    def load_model(self) -> bool:
        """Attempts to load DeBERTa-v3 model with pre-flight resource protection."""
        if self._is_loaded and self._model is not None:
            return True

        # Pre-flight check: Must have at least 1.0 GB free disk and 1.0 GB commit memory
        is_safe, metrics = check_system_resources(min_disk_free_gb=1.0, min_commit_avail_gb=1.0)
        if not is_safe:
            self._is_loaded = False
            self._load_error = (
                f"Resource constrained: {metrics['reason']} "
                f"(Disk: {metrics['disk_free_gb']}GB, Commit: {metrics['commit_avail_gb']}GB)"
            )
            logger.info("DeBERTa loading skipped due to resource constraints: %s", self._load_error)
            return False

        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info("Attempting to load secondary detector '%s' on %s...", self.model_name, self._device)

            t0 = time.time()
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name, local_files_only=True)
            self._model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name,
                local_files_only=True,
                low_cpu_mem_usage=True,
            )
            self._model.to(self._device)
            self._model.eval()

            self._is_loaded = True
            self._load_error = None
            logger.info(
                "Secondary model '%s' successfully loaded in %.2fs on %s.",
                self.model_name,
                time.time() - t0,
                self._device,
            )
            return True
        except Exception as exc:
            self._is_loaded = False
            # Distinguish missing local weights from other errors
            err_str = str(exc)
            if "offline mode" in err_str.lower() or "local_files_only" in err_str.lower() or "not find" in err_str.lower():
                self._load_error = (
                    f"Model weights for '{self.model_name}' are not cached on local filesystem. "
                    "In compliance with AICF rules, automatic heavy downloads are disabled without manual confirmation."
                )
            else:
                self._load_error = err_str

            logger.info("Secondary detector '%s' not active: %s", self.model_name, self._load_error)
            return False

    def infer(self, text: str) -> dict[str, Any]:
        """Execute inference forward pass on text string, or report availability status."""
        if not self._is_loaded or self._model is None or self._tokenizer is None:
            loaded = self.load_model()
            if not loaded:
                is_safe, metrics = check_system_resources(min_disk_free_gb=1.0, min_commit_avail_gb=1.0)
                status_name = "RESOURCE_CONSTRAINED" if not is_safe else "UNAVAILABLE"
                return {
                    "model_name": self.model_name,
                    "model_version": self.version,
                    "status": status_name,
                    "status_detail": self._load_error or "Model weights unavailable.",
                    "ai_probability": None,
                    "human_probability": None,
                    "confidence_score": None,
                    "latency_ms": 0.0,
                    "raw_output": None,
                }

        import torch

        t0 = time.time()
        try:
            encoded = self._tokenizer(
                text,
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

            latency = round((time.time() - t0) * 1000, 2)
            raw_logits = [round(float(l), 4) for l in logits.tolist()]
            raw_probs_list = [round(float(p), 4) for p in probs]
            tokens_evaluated = int(encoded["input_ids"].shape[-1]) if "input_ids" in encoded else len(text.split())

            return {
                "model_name": self.model_name,
                "model_version": self.version,
                "status": "READY",
                "status_detail": f"Inference completed in {latency}ms on {self._device}",
                "ai_probability": round(ai_prob, 4),
                "human_probability": round(human_prob, 4),
                "confidence_score": round(max(ai_prob, human_prob), 4),
                "latency_ms": latency,
                "raw_output": {
                    "logits": raw_logits,
                    "raw_probs": raw_probs_list,
                    "tokens_evaluated": tokens_evaluated,
                    "device": self._device,
                },
            }
        except Exception as exc:
            logger.error("DeBERTa inference failed: %s", exc, exc_info=True)
            return {
                "model_name": self.model_name,
                "model_version": self.version,
                "status": "ERROR",
                "status_detail": str(exc),
                "ai_probability": None,
                "human_probability": None,
                "confidence_score": None,
                "latency_ms": round((time.time() - t0) * 1000, 2),
                "raw_output": None,
            }


class TextForensicsDetector(BaseDetector):
    """Production-grade AI Text Forensics Multi-Detector & Ensemble Engine.

    Coordinates:
    - Primary RoBERTa sequence classifier (roberta-base-openai-detector)
    - Secondary DeBERTa-v3 sequence classifier (microsoft/deberta-v3-base)
    - Deterministic linguistic and information-theoretic profiler
    - Temperature-scaled covariance ensemble aggregator (T=1.25, rho=0.72)
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

        # Sub-detectors
        self.roberta = RobertaTextDetector(model_name=model_name, version=version)
        self.deberta = DebertaTextDetector(model_name="microsoft/deberta-v3-base", version="1.0.0")

        # Ensemble Aggregator
        self.ensemble_aggregator = TextEnsembleAggregator(
            temperature=1.25,
            covariance_rho=0.72,
            ai_threshold=ai_threshold,
            human_threshold=human_threshold,
            min_words_gate=40,
        )

        # Legacy compatibility properties
        self._tokenizer: Any = None
        self._model: Any = None
        self._is_loaded: bool = False
        self._load_error: str | None = None
        self._device: str = "cpu"

    @property
    def is_loaded(self) -> bool:
        return self.roberta.is_loaded or self._is_loaded

    @property
    def load_error(self) -> str | None:
        return self.roberta.load_error or self._load_error

    def load_model(self) -> bool:
        """Load primary detector model into memory."""
        success = self.roberta.load_model()
        self._is_loaded = success
        self._load_error = self.roberta.load_error
        self._tokenizer = self.roberta._tokenizer
        self._model = self.roberta._model
        self._device = self.roberta._device
        return success

    async def analyze(self, payload: Any) -> dict[str, Any]:
        """BaseDetector interface implementation."""
        if not isinstance(payload, str):
            raise TypeError("TextForensicsDetector requires string payload.")
        return self.analyze_text(payload)

    def analyze_text(self, text: str) -> dict[str, Any]:
        """Execute multi-detector forensic analysis with calibrated ensemble aggregation."""
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
                "detector_scores": {},
                "ensemble": None,
                "sentence_analysis": [],
                "paragraph_analysis": [],
                "punctuation_metrics": {},
                "sentence_length_distribution": {},
                "syntactic_repetition": {},
                "language_warning": None,
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
                "detector_scores": {},
                "ensemble": None,
                "sentence_analysis": features.get("sentence_details", []),
                "paragraph_analysis": features.get("paragraph_details", []),
                "punctuation_metrics": features.get("punctuation_metrics", {}),
                "sentence_length_distribution": features.get("sentence_length_distribution", {}),
                "syntactic_repetition": features.get("syntactic_repetition", {}),
                "language_warning": (
                    features.get("language_detection", {}).get("non_english_warning")
                    or features.get("language_detection", {}).get("warning")
                ),
            }

        # 3. Model Availability Check
        if not self._is_loaded:
            loaded = self.load_model()
            if not loaded or not self._is_loaded:
                elapsed_ms = round((time.time() - start_time) * 1000, 2)
                error_msg = self._load_error or self.roberta.load_error or "Model weights not downloaded or unconfigured."
                return {
                    "status": "BLOCKED",
                    "classification": "INCONCLUSIVE",
                    "confidence_score": None,
                    "ai_probability": None,
                    "human_probability": None,
                    "features": features,
                    "evidence": [],
                    "limitations": [
                        f"Primary model engine unconfigured or unavailable: {error_msg}",
                        "In compliance with AICF rules, simulated results are disabled.",
                    ] + DEFAULT_TEXT_LIMITATIONS,
                    "word_count": word_count,
                    "character_count": char_count,
                    "input_hash": input_hash,
                    "text_snippet": text_snippet,
                    "model_name": self.model_name,
                    "model_version": self.version,
                    "processing_time_ms": elapsed_ms,
                    "detector_scores": {},
                    "ensemble": None,
                    "sentence_analysis": features.get("sentence_details", []),
                    "paragraph_analysis": features.get("paragraph_details", []),
                    "punctuation_metrics": features.get("punctuation_metrics", {}),
                    "sentence_length_distribution": features.get("sentence_length_distribution", {}),
                    "syntactic_repetition": features.get("syntactic_repetition", {}),
                    "language_warning": (
                        features.get("language_detection", {}).get("non_english_warning")
                        or features.get("language_detection", {}).get("warning")
                    ),
                }

        # 4. Multi-Detector Execution
        detector_outputs: dict[str, dict[str, Any]] = {}

        # Detector 1: RoBERTa
        roberta_res = self.roberta.infer(clean_text)
        detector_outputs["roberta"] = roberta_res

        # Detector 2: DeBERTa
        deberta_res = self.deberta.infer(clean_text)
        detector_outputs["deberta"] = deberta_res

        # 5. Ensemble Aggregation and Calibration
        consensus = self.ensemble_aggregator.calibrate_and_aggregate(
            detector_results=detector_outputs,
            linguistic_features=features,
            word_count=word_count,
        )

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        # Merge traditional evidence signals with ensemble consensus evidence
        combined_evidence = consensus.get("evidence_signals", [])
        # If legacy build_evidence_signals is wanted, add base linguistic signals
        base_signals = build_evidence_signals(
            consensus.get("ai_probability"),
            consensus.get("human_probability"),
            features,
        )
        for sig in base_signals:
            if not any(e["signal"] == sig["signal"] for e in combined_evidence):
                combined_evidence.append(sig)

        sentence_analysis = features.get("sentence_details", [])
        paragraph_analysis = features.get("paragraph_details", [])
        punctuation_metrics = features.get("punctuation_metrics", {})
        sentence_length_distribution = features.get("sentence_length_distribution", {})
        syntactic_repetition = features.get("syntactic_repetition", {})
        language_warning = (
            features.get("language_detection", {}).get("non_english_warning")
            or features.get("language_detection", {}).get("warning")
        )

        ensemble_meta = {
            "ensemble_method": consensus.get("calibration_method", ""),
            "calibration_method": consensus.get("calibration_method", ""),
            "detectors": consensus.get("detector_scores", {}),
            "active_detector_count": consensus.get("active_detector_count", 1),
            "total_detector_count": consensus.get("total_detector_count", 3),
            "agreement_score": consensus.get("agreement_score"),
            "uncertainty_margin": (
                round(abs(consensus["ai_probability"] - 0.50), 4)
                if consensus.get("ai_probability") is not None
                else None
            ),
            "disagreement_analysis": consensus.get("disagreement_analysis"),
            "evidence_strength": consensus.get("evidence_strength"),
            "reasons_for_uncertainty": consensus.get("reasons_for_uncertainty", []),
            "sentence_analysis": sentence_analysis,
            "paragraph_analysis": paragraph_analysis,
            "punctuation_metrics": punctuation_metrics,
            "sentence_length_distribution": sentence_length_distribution,
            "syntactic_repetition": syntactic_repetition,
            "language_warning": language_warning,
        }

        return {
            "status": consensus["status"],
            "classification": consensus["classification"],
            "confidence_score": consensus["confidence_score"],
            "ai_probability": consensus.get("ai_probability"),
            "human_probability": consensus.get("human_probability"),
            "features": features,
            "evidence": combined_evidence,
            "limitations": consensus.get("limitations", DEFAULT_TEXT_LIMITATIONS),
            "word_count": word_count,
            "character_count": char_count,
            "input_hash": input_hash,
            "text_snippet": text_snippet,
            "model_name": "AICF-Multi-Detector-Ensemble",
            "model_version": self.version,
            "processing_time_ms": elapsed_ms,
            "detector_scores": consensus.get("detector_scores", {}),
            "ensemble": ensemble_meta,
            "sentence_analysis": sentence_analysis,
            "paragraph_analysis": paragraph_analysis,
            "punctuation_metrics": punctuation_metrics,
            "sentence_length_distribution": sentence_length_distribution,
            "syntactic_repetition": syntactic_repetition,
            "language_warning": language_warning,
        }


# Global singleton detector instance
text_detector = TextForensicsDetector()
