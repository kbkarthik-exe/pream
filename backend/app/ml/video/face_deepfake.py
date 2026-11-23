"""Dedicated Facial Deepfake Detection Model and Pipeline for Video Forensics.

Provides:
1. MesoNet-4 (Meso4) PyTorch architecture specialized for intermediate spatial frequency
   facial boundary and warping artifacts (Dari et al., WIFS 2018).
2. Strict offline loading rules: reports UNAVAILABLE when model weights are not found,
   never silently downloads large models, and never fabricates predictions.
3. Facial boundary seam blending telemetry integration.
4. Timestamp-based facial manipulation evidence tracking.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from backend.app.ml.video.face_detector import DetectedFace, face_detector
from PIL import Image

TORCH_AVAILABLE = True

logger = logging.getLogger("aicf.ml.video.face_deepfake")


class Meso4(nn.Module):
    """MesoNet-4 architecture for facial deepfake detection (Dari et al., WIFS 2018).

    Compact convolutional network targeting mesoscopic facial frequency artifacts.
    Parameters: ~27,977 (< 150 KB weights; < 2 MB memory footprint).
    """

    def __init__(self, num_classes: int = 2) -> None:
        super().__init__()
        self.conv1 = nn.Conv2d(3, 8, 3, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(8)
        self.relu = nn.ReLU(inplace=True)
        self.pool1 = nn.MaxPool2d(2, 2)

        self.conv2 = nn.Conv2d(8, 8, 5, padding=2, bias=False)
        self.bn2 = nn.BatchNorm2d(8)
        self.pool2 = nn.MaxPool2d(2, 2)

        self.conv3 = nn.Conv2d(8, 16, 5, padding=2, bias=False)
        self.bn3 = nn.BatchNorm2d(16)
        self.pool3 = nn.MaxPool2d(2, 2)

        self.conv4 = nn.Conv2d(16, 16, 5, padding=2, bias=False)
        self.bn4 = nn.BatchNorm2d(16)
        self.pool4 = nn.MaxPool2d(4, 4)

        self.dropout = nn.Dropout(0.5)
        # Input 256x256 -> pool1(128) -> pool2(64) -> pool3(32) -> pool4(8)
        self.fc1 = nn.Linear(16 * 8 * 8, 16)
        self.leaky_relu = nn.LeakyReLU(0.1)
        self.fc2 = nn.Linear(16, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.pool1(self.relu(self.bn1(self.conv1(x))))
        x = self.pool2(self.relu(self.bn2(self.conv2(x))))
        x = self.pool3(self.relu(self.bn3(self.conv3(x))))
        x = self.pool4(self.relu(self.bn4(self.conv4(x))))
        x = x.view(x.size(0), -1)
        x = self.dropout(x)
        x = self.leaky_relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x


@dataclass
class FacialFrameRecord:
    """Timestamp-based forensic record for faces detected in a single sampled frame."""

    frame_index: int
    timestamp_seconds: float
    face_count: int
    face_detected: bool
    primary_bbox: tuple[int, int, int, int] | None
    face_manipulation_score: float | None  # Neural manipulation probability if model ready
    boundary_seam_delta: float | None  # Boundary seam gradient disparity
    is_low_res: bool
    verdict: str  # LIKELY_MANIPULATED | LIKELY_REAL | INCONCLUSIVE | NO_FACE


@dataclass
class FacialDeepfakeTelemetry:
    """Aggregated facial deepfake analysis outcome across all video frames."""

    model_name: str
    model_version: str
    model_license: str
    availability: str  # "READY" | "UNAVAILABLE" | "NO_FACES_DETECTED"
    total_faces_analyzed: int
    frames_with_faces: int
    total_frames_sampled: int
    mean_facial_manipulation_score: float | None
    max_facial_manipulation_score: float | None
    mean_boundary_seam_delta: float
    max_boundary_seam_delta: float
    peak_manipulation_timestamp: float | None
    low_resolution_frames_count: int
    timeline: list[FacialFrameRecord]
    suspicious_temporal_segments: list[dict[str, Any]]
    error_message: str | None = None


class FacialDeepfakeDetector:
    """Dedicated facial deepfake detector implementing MesoNet-4 architecture and boundary seam forensics."""

    DEFAULT_WEIGHTS_PATH = (
        Path(__file__).parent.parent.parent.parent / "models" / "mesonet4_ffpp.pt"
    )

    def __init__(
        self,
        name: str = "MesoNet-4 Facial Forensics Head",
        version: str = "1.0.0",
        license_type: str = "MIT / Research (Dari et al., WIFS 2018)",
        weights_path: str | Path | None = None,
    ) -> None:
        self.name = name
        self.version = version
        self.license_type = license_type
        self.weights_path = Path(weights_path) if weights_path else self.DEFAULT_WEIGHTS_PATH

        self._model: Meso4 | None = None
        self._is_loaded: bool = False
        self._load_error: str | None = None

        # Attempt to load weights if locally available
        self.load_model()

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @property
    def status(self) -> str:
        return "READY" if self._is_loaded else "UNAVAILABLE"

    def load_model(self, custom_weights_path: str | Path | None = None) -> bool:
        """Loads MesoNet-4 model weights strictly from local disk.

        Never downloads from external network silently.
        """
        if not TORCH_AVAILABLE:
            self._is_loaded = False
            self._load_error = "PyTorch is not installed in the environment."
            logger.info("Facial deepfake model status: UNAVAILABLE (%s)", self._load_error)
            return False

        target_path = Path(custom_weights_path) if custom_weights_path else self.weights_path

        if not target_path.exists():
            self._is_loaded = False
            self._load_error = (
                f"Local facial deepfake model weights not found at '{target_path}'. "
                "Operating in heuristic facial boundary seam analysis mode."
            )
            logger.info("Facial deepfake model status: UNAVAILABLE (%s)", self._load_error)
            return False

        try:
            model = Meso4(num_classes=2)
            state_dict = torch.load(str(target_path), map_location="cpu")
            model.load_state_dict(state_dict)
            model.eval()
            self._model = model
            self._is_loaded = True
            self._load_error = None
            logger.info("MesoNet-4 facial deepfake model loaded successfully from %s", target_path)
            return True
        except Exception as exc:
            self._is_loaded = False
            self._load_error = f"Failed to load MesoNet-4 weights: {exc}"
            logger.warning("MesoNet-4 loading failure: %s", exc)
            return False

    def classify_face_chip(self, chip: Image.Image) -> float | None:
        """Runs MesoNet-4 forward pass on a normalized 256x256 facial chip.

        Returns:
            float | None: Probability of manipulation in [0.0, 1.0], or None if model unavailable.
        """
        if not self._is_loaded or self._model is None:
            return None

        try:
            # Standard MesoNet normalization: rescale RGB to [0, 1]
            chip_rgb = chip.convert("RGB").resize((256, 256), resample=Image.Resampling.BICUBIC)
            arr = np.array(chip_rgb, dtype=np.float32) / 255.0
            # [H, W, C] -> [1, C, H, W]
            tensor = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0)

            with torch.no_grad():
                logits = self._model(tensor)
                probs = torch.softmax(logits, dim=1).squeeze(0)
                # Index 1 = Fake / Manipulated
                fake_prob = float(probs[1].item())
                return round(fake_prob, 4)
        except Exception as exc:
            logger.error("Error during facial inference: %s", exc)
            return None

    def analyze_sampled_frames(
        self,
        sampled_frames: list[Any],  # list of SampledFrame from frames.py
    ) -> FacialDeepfakeTelemetry:
        """Executes full face detection, alignment, inference, and boundary telemetry across sampled frames."""
        timeline: list[FacialFrameRecord] = []
        all_face_scores: list[float] = []
        all_seam_deltas: list[float] = []

        total_faces_analyzed = 0
        frames_with_faces = 0
        low_res_frames_count = 0

        for f in sampled_frames:
            # 1. Detect faces in frame
            faces: list[DetectedFace] = face_detector.detect_faces(f.image_rgb)
            face_count = len(faces)

            if face_count == 0:
                timeline.append(
                    FacialFrameRecord(
                        frame_index=f.frame_index,
                        timestamp_seconds=round(f.timestamp_seconds, 3),
                        face_count=0,
                        face_detected=False,
                        primary_bbox=None,
                        face_manipulation_score=None,
                        boundary_seam_delta=None,
                        is_low_res=False,
                        verdict="NO_FACE",
                    )
                )
                continue

            frames_with_faces += 1
            total_faces_analyzed += face_count

            # Primary face is largest detected bounding box
            primary_face = faces[0]
            if primary_face.is_low_res:
                low_res_frames_count += 1

            seam_delta = primary_face.boundary_seam_delta
            all_seam_deltas.append(seam_delta)

            # 2. Run dedicated facial neural classifier if loaded
            face_prob = self.classify_face_chip(primary_face.face_chip)
            if face_prob is not None:
                all_face_scores.append(face_prob)
                if face_prob >= 0.70 or (face_prob >= 0.55 and seam_delta >= 0.35):
                    verdict = "LIKELY_MANIPULATED"
                elif face_prob <= 0.30 and seam_delta < 0.20:
                    verdict = "LIKELY_REAL"
                else:
                    verdict = "INCONCLUSIVE"
            else:
                # Heuristic boundary seam determination when model is unavailable
                if seam_delta >= 0.45:
                    verdict = "LIKELY_MANIPULATED"
                elif seam_delta <= 0.15:
                    verdict = "LIKELY_REAL"
                else:
                    verdict = "INCONCLUSIVE"

            timeline.append(
                FacialFrameRecord(
                    frame_index=f.frame_index,
                    timestamp_seconds=round(f.timestamp_seconds, 3),
                    face_count=face_count,
                    face_detected=True,
                    primary_bbox=primary_face.bbox,
                    face_manipulation_score=face_prob,
                    boundary_seam_delta=seam_delta,
                    is_low_res=primary_face.is_low_res,
                    verdict=verdict,
                )
            )

        # 3. Statistical summary
        mean_face_score = (
            round(float(np.mean(all_face_scores)), 4) if all_face_scores else None
        )
        max_face_score = (
            round(float(np.max(all_face_scores)), 4) if all_face_scores else None
        )
        mean_seam = round(float(np.mean(all_seam_deltas)), 4) if all_seam_deltas else 0.0
        max_seam = round(float(np.max(all_seam_deltas)), 4) if all_seam_deltas else 0.0

        # Peak timestamp
        peak_timestamp: float | None = None
        if all_face_scores:
            # Timestamp where neural face score is highest
            scored_records = [r for r in timeline if r.face_manipulation_score is not None]
            if scored_records:
                peak_rec = max(scored_records, key=lambda r: r.face_manipulation_score or 0.0)
                peak_timestamp = peak_rec.timestamp_seconds
        elif all_seam_deltas:
            # Timestamp where seam disparity is highest
            seam_records = [r for r in timeline if r.boundary_seam_delta is not None]
            if seam_records:
                peak_rec = max(seam_records, key=lambda r: r.boundary_seam_delta or 0.0)
                peak_timestamp = peak_rec.timestamp_seconds

        # 4. Temporal manipulation segments (cluster consecutive timestamps)
        suspicious_segments = self._extract_suspicious_segments(timeline)

        availability = (
            "NO_FACES_DETECTED"
            if frames_with_faces == 0
            else ("READY" if self._is_loaded else "UNAVAILABLE")
        )

        return FacialDeepfakeTelemetry(
            model_name=self.name,
            model_version=self.version,
            model_license=self.license_type,
            availability=availability,
            total_faces_analyzed=total_faces_analyzed,
            frames_with_faces=frames_with_faces,
            total_frames_sampled=len(sampled_frames),
            mean_facial_manipulation_score=mean_face_score,
            max_facial_manipulation_score=max_face_score,
            mean_boundary_seam_delta=mean_seam,
            max_boundary_seam_delta=max_seam,
            peak_manipulation_timestamp=peak_timestamp,
            low_resolution_frames_count=low_res_frames_count,
            timeline=timeline,
            suspicious_temporal_segments=suspicious_segments,
            error_message=self._load_error if not self._is_loaded else None,
        )

    def _extract_suspicious_segments(
        self, timeline: list[FacialFrameRecord]
    ) -> list[dict[str, Any]]:
        """Identifies timestamp intervals where facial manipulation or boundary seam disparity clusters."""
        suspicious_records = [
            r
            for r in timeline
            if r.verdict == "LIKELY_MANIPULATED"
            or (r.face_manipulation_score and r.face_manipulation_score >= 0.65)
            or (r.boundary_seam_delta and r.boundary_seam_delta >= 0.40)
        ]

        if not suspicious_records:
            return []

        segments: list[dict[str, Any]] = []
        current_cluster: list[FacialFrameRecord] = [suspicious_records[0]]

        for r in suspicious_records[1:]:
            # Group timestamps within 2.5 seconds of each other
            if r.timestamp_seconds - current_cluster[-1].timestamp_seconds <= 2.5:
                current_cluster.append(r)
            else:
                segments.append(self._format_cluster(current_cluster))
                current_cluster = [r]

        if current_cluster:
            segments.append(self._format_cluster(current_cluster))

        return segments

    def _format_cluster(self, cluster: list[FacialFrameRecord]) -> dict[str, Any]:
        start_t = cluster[0].timestamp_seconds
        end_t = cluster[-1].timestamp_seconds
        scores = [r.face_manipulation_score for r in cluster if r.face_manipulation_score is not None]
        seams = [r.boundary_seam_delta for r in cluster if r.boundary_seam_delta is not None]

        max_s = round(float(np.max(scores)), 4) if scores else None
        max_seam = round(float(np.max(seams)), 4) if seams else 0.0

        return {
            "start_timestamp_seconds": start_t,
            "end_timestamp_seconds": end_t,
            "frame_count": len(cluster),
            "peak_manipulation_score": max_s,
            "peak_boundary_seam_delta": max_seam,
            "description": (
                f"Suspicious facial segment between t={start_t:.1f}s and t={end_t:.1f}s "
                f"({len(cluster)} frames). Peak seam disparity: {max_seam:.3f}."
            ),
        }


facial_deepfake_detector = FacialDeepfakeDetector()
