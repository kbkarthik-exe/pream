"""Independent, evidence-based image generator attribution engine for AICF.

Evaluates provenance, container metadata, software tags, and canonical heuristic
signatures across separate evidence tiers without replacing or modifying existing
synthetic-image classification backbones.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from PIL import ExifTags, Image


class GeneratorOutcome(str, Enum):
    """Supported generator attribution outcomes."""

    MIDJOURNEY = "MIDJOURNEY"
    STABLE_DIFFUSION = "STABLE_DIFFUSION"
    DALLE = "DALLE"
    FLUX = "FLUX"
    ADOBE_FIREFLY = "ADOBE_FIREFLY"
    OTHER_KNOWN_GENERATOR = "OTHER_KNOWN_GENERATOR"
    UNKNOWN = "UNKNOWN"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class EvidenceTier(str, Enum):
    """Hierarchy of evidence used to establish generator attribution."""

    DIRECT_PROVENANCE = "DIRECT_PROVENANCE"
    METADATA_CLUES = "METADATA_CLUES"
    STATISTICAL_MODEL = "STATISTICAL_MODEL"
    HEURISTIC_INDICATORS = "HEURISTIC_INDICATORS"
    NONE = "NONE"


# Regex patterns for known generative tools in metadata
GENERATOR_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    GeneratorOutcome.MIDJOURNEY.value: [
        re.compile(r"\bmidjourney\b", re.IGNORECASE),
        re.compile(r"--v\s+[1-6](\.\d)?\b", re.IGNORECASE),
        re.compile(r"--ar\s+\d+:\d+\b", re.IGNORECASE),
        re.compile(r"--stylize\s+\d+\b", re.IGNORECASE),
        re.compile(r"--chaos\s+\d+\b", re.IGNORECASE),
    ],
    GeneratorOutcome.STABLE_DIFFUSION.value: [
        re.compile(r"\bstable\s*diffusion\b", re.IGNORECASE),
        re.compile(r"\bcomfyui\b", re.IGNORECASE),
        re.compile(r"\bautomatic1111\b", re.IGNORECASE),
        re.compile(r"\bwebui\b", re.IGNORECASE),
        re.compile(r"\bsteps:\s*\d+", re.IGNORECASE),
        re.compile(r"\bsampler:\s*[\w+]+", re.IGNORECASE),
        re.compile(r"\bcfg\s*scale:\s*[\d.]+", re.IGNORECASE),
        re.compile(r"\bnegative\s*prompt:", re.IGNORECASE),
        re.compile(r"\bmodel\s*hash:\s*[a-f0-9]+", re.IGNORECASE),
    ],
    GeneratorOutcome.DALLE.value: [
        re.compile(r"\bdall[- ·]?e\b", re.IGNORECASE),
        re.compile(r"\bopenai\b", re.IGNORECASE),
    ],
    GeneratorOutcome.FLUX.value: [
        re.compile(r"\bflux(\.1)?(-schnell|-dev|-pro)?\b", re.IGNORECASE),
        re.compile(r"\bblack[- ]forest[- ]labs\b", re.IGNORECASE),
        re.compile(r"\bbfl\b", re.IGNORECASE),
    ],
    GeneratorOutcome.ADOBE_FIREFLY.value: [
        re.compile(r"\badobe\s*firefly\b", re.IGNORECASE),
        re.compile(r"\bfirefly\b", re.IGNORECASE),
        re.compile(r"\badobe\s*photoshop\s*ai\b", re.IGNORECASE),
    ],
    GeneratorOutcome.OTHER_KNOWN_GENERATOR.value: [
        re.compile(r"\bnovelai\b", re.IGNORECASE),
        re.compile(r"\bleonardo(\.ai)?\b", re.IGNORECASE),
        re.compile(r"\bideogram\b", re.IGNORECASE),
        re.compile(r"\bcraiyon\b", re.IGNORECASE),
        re.compile(r"\bbing\s*image\s*creator\b", re.IGNORECASE),
    ],
}

# C2PA byte signatures in raw file containers
C2PA_BYTE_MARKERS = [b"c2pa", b"jumb", b"urn:c2pa:", b"C2PA"]
C2PA_SIGNATURE_MARKERS = [b"c2pa.signature", b"c2as", b"c2pa.claim"]

# Canonical latent resolution pairs for known generators
CANONICAL_RESOLUTIONS: dict[str, set[tuple[int, int]]] = {
    GeneratorOutcome.STABLE_DIFFUSION.value: {
        (512, 512), (768, 768), (512, 768), (768, 512),
        (1024, 1024), (1152, 896), (896, 1152), (1216, 832), (832, 1216),
        (1344, 768), (768, 1344), (1536, 640), (640, 1536),
    },
    GeneratorOutcome.DALLE.value: {
        (1024, 1024), (1024, 1792), (1792, 1024),
    },
    GeneratorOutcome.MIDJOURNEY.value: {
        (1024, 1024), (2048, 2048),
    },
}


@dataclass
class GeneratorAttributionResult:
    """Structured, typed result of the generator attribution analysis."""

    primary_generator: str
    confidence: float
    evidence_tier: str
    provenance_findings: dict[str, Any] = field(default_factory=dict)
    metadata_findings: dict[str, Any] = field(default_factory=dict)
    statistical_findings: dict[str, Any] = field(default_factory=dict)
    heuristic_findings: dict[str, Any] = field(default_factory=dict)
    conflicting_evidence: bool = False
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize result to a standard Python dictionary."""
        return asdict(self)


def attribute_generator(
    image: Image.Image | None,
    raw_bytes: bytes,
    fft_metrics: dict[str, Any] | None = None,
) -> GeneratorAttributionResult:
    """Analyze image provenance and metadata to attribute the likely generator.

    Maintains strict separation between direct provenance, metadata clues,
    statistical predictions, and heuristic indicators. Never establishes
    attribution based solely on heuristic indicators.

    Args:
        image: Pillow Image instance (optional if raw_bytes provided).
        raw_bytes: Raw bytes of the image file.
        fft_metrics: Optional spectral metrics dictionary.

    Returns:
        GeneratorAttributionResult containing structured findings across all tiers.
    """
    limitations: list[str] = [
        "Metadata can be stripped, forged, or altered during social media recompression.",
        "Heuristic resolution indicators cannot independently establish generator identity.",
        "Absence of C2PA credentials does NOT imply human or authentic camera origin.",
    ]

    # Validate image input
    if not raw_bytes or len(raw_bytes) == 0:
        return GeneratorAttributionResult(
            primary_generator=GeneratorOutcome.INSUFFICIENT_EVIDENCE.value,
            confidence=0.0,
            evidence_tier=EvidenceTier.NONE.value,
            limitations=limitations + ["Input image bytes are empty or corrupted."],
        )

    # Resolve PIL Image if not provided or handle corrupted stream
    if image is None:
        try:
            import io
            image = Image.open(io.BytesIO(raw_bytes))
        except Exception:
            return GeneratorAttributionResult(
                primary_generator=GeneratorOutcome.INSUFFICIENT_EVIDENCE.value,
                confidence=0.0,
                evidence_tier=EvidenceTier.NONE.value,
                limitations=limitations + ["Unable to parse valid image raster from bytes."],
            )

    try:
        width, height = image.size
        _img_format = (image.format or "UNKNOWN").upper()
    except Exception:
        return GeneratorAttributionResult(
            primary_generator=GeneratorOutcome.INSUFFICIENT_EVIDENCE.value,
            confidence=0.0,
            evidence_tier=EvidenceTier.NONE.value,
            limitations=limitations + ["Image header parsing failed."],
        )

    # Resolution gate
    if width < 32 or height < 32:
        return GeneratorAttributionResult(
            primary_generator=GeneratorOutcome.INSUFFICIENT_EVIDENCE.value,
            confidence=0.0,
            evidence_tier=EvidenceTier.NONE.value,
            heuristic_findings={"width": width, "height": height, "status": "BELOW_MINIMUM_GATE"},
            limitations=limitations + ["Resolution below minimum forensic threshold (32x32)."],
        )

    # -------------------------------------------------------------------------
    # Tier A: Direct Provenance Evidence (C2PA / JUMBF / CAI)
    # -------------------------------------------------------------------------
    provenance_findings = _extract_direct_provenance(raw_bytes)

    # -------------------------------------------------------------------------
    # Tier B: Metadata-based Clues (EXIF, PNG text chunks)
    # -------------------------------------------------------------------------
    metadata_findings = _extract_metadata_clues(image)

    # -------------------------------------------------------------------------
    # Tier C: Statistical Evidence (Neural / Classifier Predictions)
    # -------------------------------------------------------------------------
    # Per architectural requirement: do not invent predictions.
    # Leave unavailable when no verified generator-specific statistical model exists.
    statistical_findings = {
        "status": "UNAVAILABLE",
        "model_id": None,
        "prediction": None,
        "note": "No generator-specific statistical classifier currently registered; category inactive.",
    }

    # -------------------------------------------------------------------------
    # Tier D: Heuristic Indicators (Dimensions, Aspect Ratio, Fourier)
    # -------------------------------------------------------------------------
    heuristic_findings = _extract_heuristic_indicators(width, height, fft_metrics)

    # -------------------------------------------------------------------------
    # Attribution Decision Synthesis
    # -------------------------------------------------------------------------
    c2pa_generator = provenance_findings.get("attributed_generator")
    c2pa_verified = provenance_findings.get("has_cryptographic_signature", False)

    metadata_matches = metadata_findings.get("detected_generators", [])
    has_conflicting_metadata = len(metadata_matches) > 1

    # Check for misleading metadata (camera hardware combined with AI prompt)
    has_camera_hardware = metadata_findings.get("has_camera_hardware", False)
    has_ai_metadata = bool(metadata_matches)
    if has_camera_hardware and has_ai_metadata:
        limitations.append(
            "Potentially misleading metadata detected: Camera hardware tags coexist with AI generation markers."
        )

    # Case 1: Conflicting metadata from multiple generators
    if has_conflicting_metadata:
        return GeneratorAttributionResult(
            primary_generator=GeneratorOutcome.UNKNOWN.value,
            confidence=0.0,
            evidence_tier=EvidenceTier.METADATA_CLUES.value,
            provenance_findings=provenance_findings,
            metadata_findings=metadata_findings,
            statistical_findings=statistical_findings,
            heuristic_findings=heuristic_findings,
            conflicting_evidence=True,
            limitations=limitations + [
                f"Conflicting generator markers identified in metadata: {metadata_matches}."
            ],
        )

    # Case 2: Direct Provenance (C2PA) with verified generator assertion
    if c2pa_generator:
        # C2PA provides highest confidence tier
        conf = 0.85 if c2pa_verified else 0.70
        return GeneratorAttributionResult(
            primary_generator=c2pa_generator,
            confidence=conf,
            evidence_tier=EvidenceTier.DIRECT_PROVENANCE.value,
            provenance_findings=provenance_findings,
            metadata_findings=metadata_findings,
            statistical_findings=statistical_findings,
            heuristic_findings=heuristic_findings,
            conflicting_evidence=False,
            limitations=limitations,
        )

    # Case 3: Metadata-based Clues (Single generator match with strong markers)
    if len(metadata_matches) == 1:
        matched_gen = metadata_matches[0]
        # Metadata is client-controlled; provisional confidence capped at 0.75
        return GeneratorAttributionResult(
            primary_generator=matched_gen,
            confidence=0.75,
            evidence_tier=EvidenceTier.METADATA_CLUES.value,
            provenance_findings=provenance_findings,
            metadata_findings=metadata_findings,
            statistical_findings=statistical_findings,
            heuristic_findings=heuristic_findings,
            conflicting_evidence=False,
            limitations=limitations + ["Metadata markers detected, but metadata is forgeable."],
        )

    # Case 4: Heuristics only (Dimensions / Aspect ratio / Fourier)
    # CRITICAL RULE: Heuristics must NEVER independently establish generator identity.
    matched_heuristics = heuristic_findings.get("candidate_generators", [])
    if matched_heuristics:
        return GeneratorAttributionResult(
            primary_generator=GeneratorOutcome.UNKNOWN.value,
            confidence=0.0,
            evidence_tier=EvidenceTier.HEURISTIC_INDICATORS.value,
            provenance_findings=provenance_findings,
            metadata_findings=metadata_findings,
            statistical_findings=statistical_findings,
            heuristic_findings=heuristic_findings,
            conflicting_evidence=False,
            limitations=limitations + [
                f"Image matches canonical geometry of {matched_heuristics}, "
                f"but heuristic indicators cannot independently prove generator identity."
            ],
        )

    # Case 5: No evidence found across any tier
    return GeneratorAttributionResult(
        primary_generator=GeneratorOutcome.UNKNOWN.value,
        confidence=0.0,
        evidence_tier=EvidenceTier.NONE.value,
        provenance_findings=provenance_findings,
        metadata_findings=metadata_findings,
        statistical_findings=statistical_findings,
        heuristic_findings=heuristic_findings,
        conflicting_evidence=False,
        limitations=limitations + ["No provenance, metadata, or heuristic indicators detected."],
    )


def _extract_direct_provenance(raw_bytes: bytes) -> dict[str, Any]:
    """Scan container bytes for C2PA / JUMBF manifests and assertions."""
    has_c2pa = False
    has_sig = False
    attributed_gen: str | None = None

    # Check for C2PA markers
    for marker in C2PA_BYTE_MARKERS:
        if marker in raw_bytes[:15000] or marker in raw_bytes[-15000:]:
            has_c2pa = True
            break

    if has_c2pa:
        # Check for digital signature markers
        for sig_marker in C2PA_SIGNATURE_MARKERS:
            if sig_marker in raw_bytes[:20000] or sig_marker in raw_bytes[-20000:]:
                has_sig = True
                break

        # Check for specific generator assertions in manifest payload
        lower_sample = raw_bytes[:30000].lower() + raw_bytes[-30000:].lower()
        if b"adobe:firefly" in lower_sample or b"firefly" in lower_sample:
            attributed_gen = GeneratorOutcome.ADOBE_FIREFLY.value
        elif b"dall-e" in lower_sample or b"openai" in lower_sample:
            attributed_gen = GeneratorOutcome.DALLE.value

    return {
        "has_c2pa_manifest": has_c2pa,
        "has_cryptographic_signature": has_sig,
        "signature_verification_status": (
            "PRESENT_CRYPTOGRAPHIC_SIGNATURE" if has_sig else
            ("UNVERIFIED_MANIFEST_ONLY" if has_c2pa else "NO_MANIFEST_PRESENT")
        ),
        "attributed_generator": attributed_gen,
        "provenance_note": (
            "Direct provenance manifest detected." if has_c2pa else
            "No C2PA provenance manifest present. Note: Absence does NOT imply human origin."
        ),
    }


def _extract_metadata_clues(image: Image.Image) -> dict[str, Any]:
    """Safely extract metadata from EXIF and PNG text chunks."""
    matched_generators: list[str] = []
    text_corpus: list[str] = []
    inspected_keys: list[str] = []
    has_camera_hardware = False
    camera_info: dict[str, str | None] = {}
    software_tag: str | None = None

    # 1. Inspect EXIF
    try:
        exif = image.getexif()
        if exif:
            for tag_id, value in exif.items():
                tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                inspected_keys.append(str(tag_name))
                str_val = ""
                if isinstance(value, bytes):
                    str_val = value.decode("utf-8", errors="ignore").strip("\x00")
                elif isinstance(value, (int, float, str)):
                    str_val = str(value)

                if tag_name in ("Make", "Model", "LensModel") and str_val:
                    has_camera_hardware = True
                    camera_info[tag_name] = str_val[:50]
                elif tag_name in ("Software", "ProcessingSoftware") and str_val:
                    software_tag = str_val[:80]
                    text_corpus.append(str_val)
                elif tag_name in ("UserComment", "ImageDescription") and str_val:
                    text_corpus.append(str_val[:500])
    except Exception:
        pass

    # 2. Inspect PNG info chunks
    if hasattr(image, "info") and isinstance(image.info, dict):
        for k, v in image.info.items():
            inspected_keys.append(str(k))
            k_str = str(k).lower()
            v_str = ""
            if isinstance(v, bytes):
                v_str = v.decode("utf-8", errors="ignore")
            elif isinstance(v, str):
                v_str = v

            if k_str in ("parameters", "prompt", "workflow", "comment", "description", "software"):
                if v_str:
                    text_corpus.append(v_str[:1000])

    # Search corpus against generator patterns
    full_text = " ".join(text_corpus)
    if full_text:
        for gen_name, patterns in GENERATOR_PATTERNS.items():
            for pat in patterns:
                if pat.search(full_text):
                    if gen_name not in matched_generators:
                        matched_generators.append(gen_name)
                    break

    return {
        "detected_generators": matched_generators,
        "has_camera_hardware": has_camera_hardware,
        "camera_info": camera_info,
        "software_tag": software_tag,
        "metadata_inspected": bool(text_corpus),
        "inspected_keys": inspected_keys,
    }


def _extract_heuristic_indicators(
    width: int,
    height: int,
    fft_metrics: dict[str, Any] | None,
) -> dict[str, Any]:
    """Evaluate dimensions, aspect ratios, and spectral metrics."""
    candidates: list[str] = []
    dim_pair = (width, height)
    inverted_pair = (height, width)

    for gen_name, res_set in CANONICAL_RESOLUTIONS.items():
        if dim_pair in res_set or inverted_pair in res_set:
            if gen_name not in candidates:
                candidates.append(gen_name)

    # Compute aspect ratio string
    import math
    gcd = math.gcd(width, height)
    ar_str = f"{width // gcd}:{height // gcd}" if gcd > 0 else f"{width}:{height}"

    has_fft_harmonics = False
    if fft_metrics and isinstance(fft_metrics, dict):
        # High anisotropy (>0.75) is common in periodic synthetic grids
        anisotropy = fft_metrics.get("anisotropy_ratio", 0.0)
        if isinstance(anisotropy, (int, float)) and anisotropy > 0.75:
            has_fft_harmonics = True

    return {
        "width": width,
        "height": height,
        "aspect_ratio": ar_str,
        "is_canonical_resolution": bool(candidates),
        "candidate_generators": candidates,
        "fourier_harmonic_spike_detected": has_fft_harmonics,
        "heuristic_note": (
            f"Resolution {width}x{height} matches canonical buckets for {candidates}."
            if candidates else "Non-canonical resolution."
        ),
    }
