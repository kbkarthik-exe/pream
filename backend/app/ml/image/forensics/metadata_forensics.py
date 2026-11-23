"""Metadata forensics: EXIF, PNG chunks, software identification, and inconsistency analysis."""

from __future__ import annotations

import re
from typing import Any

from PIL import ExifTags, Image

from .schemas import EvidenceFinding, Reliability, Severity

# Known image manipulation & editing software signatures
EDITING_SOFTWARE_PATTERNS = [
    (re.compile(r"adobe\s*photoshop", re.IGNORECASE), "Adobe Photoshop"),
    (re.compile(r"adobe\s*lightroom", re.IGNORECASE), "Adobe Lightroom"),
    (re.compile(r"\bgimp\b", re.IGNORECASE), "GIMP"),
    (re.compile(r"affinity\s*photo", re.IGNORECASE), "Affinity Photo"),
    (re.compile(r"paint\.net", re.IGNORECASE), "Paint.NET"),
    (re.compile(r"canva", re.IGNORECASE), "Canva"),
    (re.compile(r"snapseed", re.IGNORECASE), "Snapseed"),
    (re.compile(r"vsco", re.IGNORECASE), "VSCO"),
]

# Generative AI software markers in metadata
GENERATIVE_SOFTWARE_PATTERNS = [
    (re.compile(r"midjourney", re.IGNORECASE), "Midjourney"),
    (re.compile(r"stable\s*diffusion", re.IGNORECASE), "Stable Diffusion"),
    (re.compile(r"comfyui", re.IGNORECASE), "ComfyUI"),
    (re.compile(r"automatic1111", re.IGNORECASE), "Automatic1111 WebUI"),
    (re.compile(r"dall[- ·]?e", re.IGNORECASE), "DALL-E"),
    (re.compile(r"flux(\.1)?", re.IGNORECASE), "FLUX.1"),
    (re.compile(r"adobe\s*firefly", re.IGNORECASE), "Adobe Firefly"),
    (re.compile(r"steps:\s*\d+", re.IGNORECASE), "Stable Diffusion"),
    (re.compile(r"sampler:\s*[\w+]+", re.IGNORECASE), "Stable Diffusion"),
]


def analyze_metadata(image: Image.Image) -> tuple[dict[str, Any], list[EvidenceFinding]]:
    """Inspect EXIF, PNG chunks, and detect metadata inconsistencies.

    Returns:
        tuple of (metadata_summary_dict, list_of_evidence_findings)
    """
    findings: list[EvidenceFinding] = []
    exif_tags: dict[str, Any] = {}
    png_chunks: dict[str, str] = {}
    camera_make: str | None = None
    camera_model: str | None = None
    software: str | None = None
    date_original: str | None = None
    date_modify: str | None = None

    # 1. Parse EXIF
    try:
        raw_exif = image.getexif()
        if raw_exif:
            for tag_id, value in raw_exif.items():
                tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                if isinstance(value, bytes):
                    try:
                        exif_tags[tag_name] = value.decode("utf-8", errors="ignore").strip("\x00")
                    except Exception:
                        exif_tags[tag_name] = f"<{len(value)} bytes binary>"
                elif isinstance(value, (int, float, str, bool)):
                    exif_tags[tag_name] = value
                else:
                    exif_tags[tag_name] = str(value)

            camera_make = exif_tags.get("Make")
            camera_model = exif_tags.get("Model")
            software = exif_tags.get("Software") or exif_tags.get("ProcessingSoftware")
            date_original = exif_tags.get("DateTimeOriginal")
            date_modify = exif_tags.get("DateTime")
    except Exception as e:
        findings.append(
            EvidenceFinding(
                source="METADATA_EXIF",
                description=f"EXIF header parsing failed: {e}",
                severity=Severity.LOW,
                reliability=Reliability.HEURISTIC,
                limitations=["Malformed EXIF can occur naturally or through deliberate byte tampering."],
            )
        )

    # 2. Parse PNG info chunks
    if hasattr(image, "info") and isinstance(image.info, dict):
        for k, v in image.info.items():
            if isinstance(v, (str, bytes)):
                v_str = v.decode("utf-8", errors="ignore") if isinstance(v, bytes) else str(v)
                png_chunks[str(k)] = v_str[:1000]

    # 3. Detect Editing Software
    editing_tools_found: list[str] = []
    for pat, tool_name in EDITING_SOFTWARE_PATTERNS:
        if software and pat.search(str(software)):
            editing_tools_found.append(tool_name)
        for chunk_val in png_chunks.values():
            if pat.search(chunk_val) and tool_name not in editing_tools_found:
                editing_tools_found.append(tool_name)

    if editing_tools_found:
        findings.append(
            EvidenceFinding(
                source="METADATA_SOFTWARE",
                description=f"Image editing/processing software headers detected: {editing_tools_found}.",
                severity=Severity.MEDIUM,
                reliability=Reliability.HEURISTIC,
                limitations=[
                    "Presence of editing software indicates post-processing, but does not prove malicious tampering.",
                    "Metadata software headers can be preserved, stripped, or falsified.",
                ],
                metadata={"editing_software": editing_tools_found},
            )
        )

    # 4. Detect Generative AI Metadata Markers
    generative_tools_found: list[str] = []
    text_corpus = " ".join([str(software or "")] + list(png_chunks.values()) + [str(exif_tags.get("UserComment", ""))])
    for pat, gen_name in GENERATIVE_SOFTWARE_PATTERNS:
        if pat.search(text_corpus) and gen_name not in generative_tools_found:
            generative_tools_found.append(gen_name)

    if generative_tools_found:
        findings.append(
            EvidenceFinding(
                source="METADATA_GENERATIVE",
                description=f"Generative AI metadata headers or prompt parameters detected: {generative_tools_found}.",
                severity=Severity.HIGH,
                reliability=Reliability.HEURISTIC,
                limitations=[
                    "Metadata parameters are easily stripped during social media upload.",
                    "Metadata can be injected into authentic images to create false positives.",
                ],
                metadata={"generative_tools": generative_tools_found},
            )
        )

    # 5. Inconsistency Analysis
    # Case A: Camera Hardware tags present alongside Generative AI markers
    if (camera_make or camera_model) and generative_tools_found:
        findings.append(
            EvidenceFinding(
                source="METADATA_INCONSISTENCY",
                description=(
                    f"Conflicting metadata detected: Optical camera hardware tags ({camera_make} {camera_model}) "
                    f"coexist with generative AI parameters ({generative_tools_found})."
                ),
                severity=Severity.HIGH,
                reliability=Reliability.HEURISTIC,
                limitations=[
                    "May represent an authentic photograph modified via generative inpainting, or synthesized media with forged EXIF."
                ],
                metadata={"camera_make": camera_make, "generative_tools": generative_tools_found},
            )
        )

    # Case B: Date Discrepancies
    if date_original and date_modify and date_original != date_modify:
        findings.append(
            EvidenceFinding(
                source="METADATA_INCONSISTENCY",
                description=f"Creation date ({date_original}) differs from modification date ({date_modify}).",
                severity=Severity.LOW,
                reliability=Reliability.HEURISTIC,
                limitations=["Standard post-processing, exporting, or format conversion updates modification timestamps."],
                metadata={"date_original": date_original, "date_modify": date_modify},
            )
        )

    # Case C: Missing Metadata Baseline
    has_any_metadata = bool(exif_tags or png_chunks)
    if not has_any_metadata:
        findings.append(
            EvidenceFinding(
                source="METADATA_ABSENT",
                description="Container contains zero EXIF tags or PNG textual chunks.",
                severity=Severity.INFORMATIONAL,
                reliability=Reliability.HEURISTIC,
                limitations=[
                    "Social media platforms, messaging applications, and web optimizers routinely strip all container metadata.",
                    "Absence of metadata provides no evidentiary value regarding image authenticity."
                ],
            )
        )

    summary = {
        "has_exif": bool(exif_tags),
        "has_png_chunks": bool(png_chunks),
        "camera_make": camera_make,
        "camera_model": camera_model,
        "software": software,
        "editing_software_detected": editing_tools_found,
        "generative_software_detected": generative_tools_found,
        "exif_tag_count": len(exif_tags),
        "png_chunk_keys": list(png_chunks.keys()),
    }

    return summary, findings
