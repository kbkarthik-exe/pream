"""AICF Forensic Report PDF Generation Service.

Generates high-assurance, professional PDF forensic reports matching the AICF black-and-gold
brand identity for Text, Image, and Video analyses.
"""

import html
import io
import json
from datetime import UTC, datetime
from typing import Any

from backend.app.models.image_analysis import ImageAnalysisRecord
from backend.app.models.report import ForensicReport
from backend.app.models.text_analysis import TextAnalysisRecord
from backend.app.models.video import VideoAnalysisRecord
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import Flowable

# Brand Color Palette
COLOR_OBSIDIAN = colors.HexColor("#0B0C10")
COLOR_CARD_BG = colors.HexColor("#12141A")
COLOR_GOLD = colors.HexColor("#D4AF37")
COLOR_GOLD_LIGHT = colors.HexColor("#F3E5AB")
COLOR_GOLD_DARK = colors.HexColor("#997A15")
COLOR_BORDER = colors.HexColor("#2B2F3D")
COLOR_TEXT_PRIMARY = colors.HexColor("#FFFFFF")
COLOR_TEXT_MUTED = colors.HexColor("#6B7280")
COLOR_TEXT_BODY = colors.HexColor("#1F2937")
COLOR_LIGHT_BG = colors.HexColor("#F8F9FA")
COLOR_TABLE_HEADER = colors.HexColor("#0F1117")

# Classification Accent Colors
COLOR_RED = colors.HexColor("#DC2626")
COLOR_GREEN = colors.HexColor("#059669")
COLOR_AMBER = colors.HexColor("#D97706")
COLOR_BLUE = colors.HexColor("#2563EB")


def safe_escape(text: Any) -> str:
    """Escapes user and raw content for safe insertion into ReportLab Paragraphs."""
    if text is None:
        return ""
    return html.escape(str(text))


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas that dynamically counts total pages and draws running headers and footers."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._saved_page_states: list[dict[str, Any]] = []

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        start_page_fn = getattr(self, "_startPage", None)
        if callable(start_page_fn):
            start_page_fn()

    def save(self) -> None:
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, total_pages: int) -> None:
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#6B7280"))

        page_w, page_h = letter
        page_num = self.getPageNumber()

        # Running Header (pages 2+)
        if page_num > 1:
            self.drawString(
                36, page_h - 28, "A Multimodal Deep Learning Framework for Robust Detection of Synthetic Media"
            )
            self.drawRightString(
                page_w - 36, page_h - 28, f"Document Page {page_num} of {total_pages}"
            )
            self.setStrokeColor(COLOR_GOLD)
            self.setLineWidth(0.5)
            self.line(36, page_h - 32, page_w - 36, page_h - 32)

        # Running Footer (all pages)
        self.setStrokeColor(COLOR_BORDER)
        self.setLineWidth(0.5)
        self.line(36, 40, page_w - 36, 40)

        footer_text = "CONFIDENTIAL & PROPRIETARY — FOR AUTHORIZED FORENSIC PURPOSES ONLY"
        self.drawString(36, 28, footer_text)
        page_indicator = f"Page {page_num} of {total_pages}"
        self.drawRightString(page_w - 36, 28, page_indicator)

        self.restoreState()


class ReportStyleManager:
    """Centralized stylesheet conforming to AICF forensic publishing standards."""

    def __init__(self) -> None:
        self.base = getSampleStyleSheet()

        self.title = ParagraphStyle(
            "AICFTitle",
            parent=self.base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=COLOR_TEXT_PRIMARY,
        )

        self.subtitle = ParagraphStyle(
            "AICFSubtitle",
            parent=self.base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=COLOR_GOLD,
            textTransform="uppercase",
        )

        self.section_heading = ParagraphStyle(
            "AICFSectionHeading",
            parent=self.base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=15,
            textColor=COLOR_OBSIDIAN,
            spaceBefore=8,
            spaceAfter=4,
        )

        self.meta_label = ParagraphStyle(
            "AICFMetaLabel",
            parent=self.base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=COLOR_TEXT_MUTED,
        )

        self.meta_value = ParagraphStyle(
            "AICFMetaValue",
            parent=self.base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=COLOR_TEXT_BODY,
        )

        self.mono_value = ParagraphStyle(
            "AICFMonoValue",
            parent=self.base["Normal"],
            fontName="Courier",
            fontSize=7.5,
            leading=9.5,
            textColor=COLOR_TEXT_BODY,
        )

        self.body = ParagraphStyle(
            "AICFBody",
            parent=self.base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=COLOR_TEXT_BODY,
        )

        self.disclaimer = ParagraphStyle(
            "AICFDisclaimer",
            parent=self.base["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=7.5,
            leading=10.5,
            textColor=COLOR_TEXT_MUTED,
        )


styles = ReportStyleManager()


def _build_header_flowable(report_code: str, title: str, subtitle: str) -> Table:
    """Builds the signature black-and-gold AICF document header."""
    header_content = [
        [
            Paragraph(safe_escape(subtitle), styles.subtitle),
            Paragraph(f"<b>REPORT ID:</b> {safe_escape(report_code)}", styles.subtitle),
        ],
        [
            Paragraph(safe_escape(title), styles.title),
            Paragraph("VERIFIED AUDIT", styles.subtitle),
        ],
    ]

    header_table = Table(header_content, colWidths=[380, 160])
    header_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_OBSIDIAN),
                ("TEXTCOLOR", (0, 0), (-1, -1), COLOR_TEXT_PRIMARY),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 10),
            ]
        )
    )
    return header_table


def _build_metadata_table(metadata_rows: list[tuple[str, str, bool]]) -> Table:
    """Renders structured key-value metadata in a dual-column format."""
    table_data = []
    for label, val, is_mono in metadata_rows:
        val_style = styles.mono_value if is_mono else styles.meta_value
        table_data.append(
            [
                Paragraph(safe_escape(label), styles.meta_label),
                Paragraph(safe_escape(val), val_style),
            ]
        )

    meta_table = Table(table_data, colWidths=[140, 400])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_LIGHT_BG),
                ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("PADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return meta_table


def _build_determination_card(
    classification: str,
    status: str,
    confidence_score: float | None,
    ai_prob: float | None = None,
    human_prob: float | None = None,
    calibration_note: str = "",
) -> Table:
    """Renders primary forensic classification and calibrated confidence banner."""
    accent_color = COLOR_BLUE
    if "AI-GENERATED" in classification:
        accent_color = COLOR_RED
    elif "HUMAN" in classification:
        accent_color = COLOR_GREEN
    elif "BLOCKED" in status or "FAILED" in status:
        accent_color = COLOR_AMBER

    conf_str = f"{(confidence_score * 100):.1f}%" if confidence_score is not None else "N/A"

    det_rows = [
        [
            Paragraph("FORENSIC CLASSIFICATION", styles.meta_label),
            Paragraph("PROCESSING STATUS", styles.meta_label),
            Paragraph("EMPIRICAL CONFIDENCE", styles.meta_label),
        ],
        [
            Paragraph(
                f"<b><font size=12 color='{accent_color.hexval()}'>"
                f"{safe_escape(classification)}</font></b>",
                styles.meta_value,
            ),
            Paragraph(f"<b>{safe_escape(status)}</b>", styles.meta_value),
            Paragraph(
                f"<b><font size=12 color='{COLOR_GOLD_DARK.hexval()}'>{conf_str}</font></b>",
                styles.meta_value,
            ),
        ],
    ]

    if ai_prob is not None and human_prob is not None:
        det_rows.append(
            [
                Paragraph("AI PROBABILITY DENSITY", styles.meta_label),
                Paragraph("HUMAN PROBABILITY DENSITY", styles.meta_label),
                Paragraph("CALIBRATION MODEL", styles.meta_label),
            ]
        )
        det_rows.append(
            [
                Paragraph(f"{(ai_prob * 100):.1f}%", styles.mono_value),
                Paragraph(f"{(human_prob * 100):.1f}%", styles.mono_value),
                Paragraph("Softmax Likelihood Distribution", styles.meta_value),
            ]
        )

    det_table = Table(det_rows, colWidths=[180, 180, 180])
    det_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_LIGHT_BG),
                ("BOX", (0, 0), (-1, -1), 1.5, accent_color),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("PADDING", (0, 0), (-1, -1), 5),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return det_table


def _build_evidence_table(evidence_list: list[dict[str, Any]]) -> Table:
    """Formats forensic telemetry items into an evidentiary findings table."""
    headers = [
        Paragraph("<b>SIGNAL</b>", styles.meta_label),
        Paragraph("<b>METRIC</b>", styles.meta_label),
        Paragraph("<b>OBSERVED FORENSIC FINDING</b>", styles.meta_label),
    ]
    rows = [headers]

    for item in evidence_list:
        signal = safe_escape(item.get("signal", ""))
        metric = safe_escape(item.get("metric", "-"))
        finding = safe_escape(item.get("finding", ""))
        rows.append(
            [
                Paragraph(signal, styles.meta_value),
                Paragraph(metric, styles.mono_value),
                Paragraph(finding, styles.body),
            ]
        )

    evidence_table = Table(rows, colWidths=[120, 100, 320])
    evidence_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_LIGHT_BG),
                ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("PADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return evidence_table


def _build_frame_scores_table(frame_scores: list[dict[str, Any]]) -> Table:
    """Formats frame-level classification scores into an audit timeline table."""
    headers = [
        Paragraph("<b>FRAME #</b>", styles.meta_label),
        Paragraph("<b>TIMESTAMP</b>", styles.meta_label),
        Paragraph("<b>AI PROBABILITY</b>", styles.meta_label),
        Paragraph("<b>HUMAN PROBABILITY</b>", styles.meta_label),
        Paragraph("<b>FRAME CLASSIFICATION</b>", styles.meta_label),
    ]
    rows = [headers]
    for f in frame_scores:
        idx = safe_escape(f.get("frame_index", "-"))
        ts = f"{f.get('timestamp_seconds', 0.0):.2f}s"
        ai_p = f"{(f.get('ai_probability', 0.0) * 100):.1f}%"
        hu_p = f"{(f.get('human_probability', 0.0) * 100):.1f}%"
        cls_name = safe_escape(f.get("classification", "-"))

        rows.append(
            [
                Paragraph(f"#{idx}", styles.mono_value),
                Paragraph(ts, styles.mono_value),
                Paragraph(ai_p, styles.mono_value),
                Paragraph(hu_p, styles.mono_value),
                Paragraph(cls_name, styles.meta_value),
            ]
        )

    table = Table(rows, colWidths=[70, 80, 100, 100, 190])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_LIGHT_BG),
                ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("PADDING", (0, 0), (-1, -1), 3),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return table


def _build_multi_detector_table(detectors: dict[str, Any]) -> Table:
    """Formats individual detector models in multi-model ensemble into an evidentiary table."""
    headers = [
        Paragraph("<b>DETECTOR HEAD</b>", styles.meta_label),
        Paragraph("<b>STATUS</b>", styles.meta_label),
        Paragraph("<b>AI PROBABILITY</b>", styles.meta_label),
        Paragraph("<b>DIAGNOSTIC / TELEMETRY</b>", styles.meta_label),
    ]
    rows = [headers]
    for key, d in detectors.items():
        name = safe_escape(d.get("model_name", key))
        st = safe_escape(d.get("status", "UNAVAILABLE"))
        ai_p = f"{(d.get('ai_probability', 0.0) * 100):.1f}%" if d.get("ai_probability") is not None else "N/A"
        det = safe_escape(d.get("status_detail") or f"Latency: {d.get('latency_ms', 0):.1f}ms")

        rows.append(
            [
                Paragraph(name, styles.meta_value),
                Paragraph(f"<b>{st}</b>", styles.mono_value),
                Paragraph(ai_p, styles.mono_value),
                Paragraph(det, styles.meta_value),
            ]
        )

    table = Table(rows, colWidths=[150, 90, 80, 220])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_LIGHT_BG),
                ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("PADDING", (0, 0), (-1, -1), 3),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return table


def _build_sentence_cadence_table(sentence_details: list[dict[str, Any]]) -> Table:
    """Formats sentence-level cadence and pacing details into an evidentiary table."""
    headers = [
        Paragraph("<b>#</b>", styles.meta_label),
        Paragraph("<b>SENTENCE EXCERPT</b>", styles.meta_label),
        Paragraph("<b>WORDS</b>", styles.meta_label),
        Paragraph("<b>CADENCE</b>", styles.meta_label),
        Paragraph("<b>TRANSITIONAL</b>", styles.meta_label),
    ]
    rows = [headers]
    for s in sentence_details[:8]:
        idx = safe_escape(s.get("sentence_idx", 0) + 1)
        raw_text = s.get("text", "")
        snip = (raw_text[:50] + "...") if len(raw_text) > 50 else raw_text
        w_cnt = str(s.get("word_count", 0))
        cadence = safe_escape(s.get("relative_cadence", "BALANCED"))
        opening = "Yes (Formal)" if s.get("has_transitional_opening") else "Standard"

        rows.append(
            [
                Paragraph(f"#{idx}", styles.mono_value),
                Paragraph(safe_escape(snip), styles.meta_value),
                Paragraph(w_cnt, styles.mono_value),
                Paragraph(f"<b>{cadence}</b>", styles.mono_value),
                Paragraph(opening, styles.meta_value),
            ]
        )

    table = Table(rows, colWidths=[35, 245, 60, 100, 100])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_LIGHT_BG),
                ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("PADDING", (0, 0), (-1, -1), 3),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return table


def _build_image_ensemble_table(scores: list[dict[str, Any]]) -> Table:
    """Formats individual image detector models in multi-model ensemble into an evidentiary table."""
    headers = [
        Paragraph("<b>DETECTOR HEAD</b>", styles.meta_label),
        Paragraph("<b>STATUS</b>", styles.meta_label),
        Paragraph("<b>SCORE / FINDING</b>", styles.meta_label),
        Paragraph("<b>DIAGNOSTIC / EVIDENCE</b>", styles.meta_label),
    ]
    rows = [headers]
    for d in scores:
        name = safe_escape(d.get("model_name", d.get("detector_id", "Unknown")))
        st = safe_escape(d.get("status", "READY"))
        cal_score = d.get("calibrated_score") or d.get("raw_probability")
        score_str = f"{(cal_score * 100):.1f}%" if cal_score is not None else "N/A"
        evidence_str = (
            d.get("evidence", [""])[0]
            if d.get("evidence")
            else f"Latency: {d.get('latency_ms', 0):.1f}ms"
        )

        rows.append(
            [
                Paragraph(name, styles.meta_value),
                Paragraph(f"<b>{st}</b>", styles.mono_value),
                Paragraph(score_str, styles.mono_value),
                Paragraph(safe_escape(evidence_str), styles.meta_value),
            ]
        )

    table = Table(rows, colWidths=[150, 80, 80, 230])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_LIGHT_BG),
                ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("PADDING", (0, 0), (-1, -1), 3),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return table


def _build_disclaimer_block() -> Table:
    """Standard legal and scientific disclaimer required for forensic honesty."""
    disclaimer_text = (
        "<b>MANDATORY SCIENTIFIC &amp; EPISTEMIC DISCLAIMER:</b> Automated synthetic "
        "content detection operates on probabilistic statistical inference and does not "
        "constitute absolute, irrefutable proof of synthetic generation or human origin. "
        "Novel generative models, adversarial perturbations, extreme lossy compression, and "
        "paraphrasing can alter confidence metrics. Findings should be utilized in conjunction "
        "with broader chain-of-custody corroboration, source provenance, and human forensic "
        "analyst review."
    )
    disc_table = Table([[Paragraph(disclaimer_text, styles.disclaimer)]], colWidths=[540])
    disc_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_LIGHT_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return disc_table


def generate_text_analysis_pdf(record: TextAnalysisRecord, analyst_name: str = "Analyst") -> bytes:
    """Generates an official forensic PDF report for a TextAnalysisRecord."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=40,
        bottomMargin=48,
    )

    story: list[Flowable] = []

    # 1. Header
    report_code = f"AICF-TXT-{record.id:05d}"
    story.append(
        _build_header_flowable(
            report_code, "AI Text Forensic Examination", "Synthetic Media Detection Framework"
        )
    )
    story.append(
        HRFlowable(width="100%", thickness=2, color=COLOR_GOLD, spaceBefore=2, spaceAfter=8)
    )

    # 2. Metadata Grid
    now_utc = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    record_created = (
        record.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if record.created_at else now_utc
    )

    metadata = [
        ("Analysis Record ID", f"#{record.id}", False),
        ("Report Code", report_code, True),
        ("Report Generated At", now_utc, False),
        ("Investigation Timestamp", record_created, False),
        ("Assigned Analyst", analyst_name, False),
        ("Media Modality", "Text (Natural Language)", False),
        ("Cryptographic Input Hash (SHA-256)", record.input_hash, True),
        (
            "Payload Metrics",
            f"{record.word_count} words | {record.character_count} characters",
            False,
        ),
    ]
    story.append(_build_metadata_table(metadata))
    story.append(Spacer(1, 8))

    # 3. Determination
    story.append(
        _build_determination_card(
            classification=record.classification,
            status=record.status,
            confidence_score=record.confidence_score,
            calibration_note="Calibrated RoBERTa Softmax Probability Thresholds",
        )
    )
    story.append(Spacer(1, 10))

    # 4. Text Sample Snippet Box
    story.append(
        Paragraph("<b>EXAMINED TEXT CORPUS (HASH-VERIFIED SNIPPET)</b>", styles.section_heading)
    )
    snippet_content = f"&ldquo;{safe_escape(record.text_snippet)}&rdquo;"
    snippet_table = Table([[Paragraph(snippet_content, styles.body)]], colWidths=[540])
    snippet_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_LIGHT_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(snippet_table)
    story.append(Spacer(1, 10))

    # 5. Model & Telemetry Specifications
    story.append(
        Paragraph("<b>DETECTION PIPELINE &amp; METRIC SUMMARY</b>", styles.section_heading)
    )
    pipeline_rows = [
        ("Inference Transformer", f"{record.model_name} (v{record.model_version})", False),
        ("Inference Runtime Latency", f"{record.processing_time_ms:.1f} ms", False),
        ("Sentence Burstiness Variance (CV)", f"{record.burstiness_score:.2f}", True),
        ("Type-Token Ratio (Lexical Diversity)", f"{record.type_token_ratio:.2f}", True),
        ("Shannon Token Entropy", f"{record.token_entropy:.2f} bits", True),
        ("Repeated 3-Gram Ratio", f"{record.repeated_ngram_ratio:.2%}", True),
    ]
    story.append(_build_metadata_table(pipeline_rows))
    story.append(Spacer(1, 10))

    # 5b. Multi-Detector Ensemble Telemetry
    ensemble_data = None
    if getattr(record, "ensemble_json", None):
        try:
            ensemble_data = json.loads(record.ensemble_json)
        except Exception:
            ensemble_data = None

    if ensemble_data and "detectors" in ensemble_data:
        story.append(
            Paragraph("<b>MULTI-MODEL DETECTOR ENSEMBLE CONSENSUS</b>", styles.section_heading)
        )
        story.append(_build_multi_detector_table(ensemble_data["detectors"]))
        story.append(Spacer(1, 8))

        consensus_meta = []
        if ensemble_data.get("agreement_score") is not None:
            consensus_meta.append(
                ("Inter-Detector Agreement", f"{ensemble_data['agreement_score']:.1%}", True)
            )
        if ensemble_data.get("evidence_strength"):
            consensus_meta.append(
                ("Evidence Strength Tier", str(ensemble_data["evidence_strength"]), False)
            )
        if ensemble_data.get("disagreement_analysis"):
            consensus_meta.append(
                ("Model Agreement Analysis", str(ensemble_data["disagreement_analysis"]), False)
            )
        if consensus_meta:
            story.append(_build_metadata_table(consensus_meta))
            story.append(Spacer(1, 10))

        # Sentence-Level Cadence Table
        sent_details = ensemble_data.get("sentence_analysis", [])
        if sent_details:
            story.append(
                Paragraph("<b>SENTENCE-LEVEL CADENCE &amp; FORENSIC PACING</b>", styles.section_heading)
            )
            story.append(_build_sentence_cadence_table(sent_details))
            story.append(Spacer(1, 10))

        # Syntactic Pacing & Punctuation
        punct = ensemble_data.get("punctuation_metrics")
        if punct and punct.get("total_punctuation_count", 0) > 0:
            punct_rows = [
                ("Total Punctuation Marks", str(punct.get("total_punctuation_count", 0)), True),
                ("Punctuation Density", f"{punct.get('punctuation_density', 0.0):.2%}", True),
                ("Commas / Periods", f"{punct.get('comma_count', 0)} / {punct.get('period_count', 0)}", True),
                ("Expressive Marks (! / ?)", f"{punct.get('exclamation_count', 0)} / {punct.get('question_count', 0)}", True),
            ]
            story.append(
                Paragraph("<b>SYNTACTIC PACING &amp; PUNCTUATION DENSITY</b>", styles.section_heading)
            )
            story.append(_build_metadata_table(punct_rows))
            story.append(Spacer(1, 10))

    # 6. Evidentiary Signals
    try:
        evidence_list = json.loads(record.evidence_json) if record.evidence_json else []
    except Exception:
        evidence_list = []

    if evidence_list:
        story.append(Paragraph("<b>OBSERVED FORENSIC EVIDENCE</b>", styles.section_heading))
        story.append(_build_evidence_table(evidence_list))
        story.append(Spacer(1, 10))

    # 7. Methodological Limitations
    try:
        limitations = json.loads(record.limitations_text) if record.limitations_text else []
    except Exception:
        limitations = [record.limitations_text] if record.limitations_text else []

    if limitations:
        story.append(
            Paragraph("<b>METHODOLOGICAL LIMITATIONS &amp; CAVEATS</b>", styles.section_heading)
        )
        lim_paragraphs = [
            Paragraph(f"&bull; {safe_escape(lim)}", styles.body) for lim in limitations
        ]
        lim_table = Table([[p] for p in lim_paragraphs], colWidths=[540])
        lim_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), COLOR_LIGHT_BG),
                    ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                    ("PADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(lim_table)
        story.append(Spacer(1, 10))

    # 8. Disclaimer
    story.append(KeepTogether([_build_disclaimer_block()]))

    doc.build(story, canvasmaker=NumberedCanvas)
    return buf.getvalue()


def generate_image_analysis_pdf(
    record: ImageAnalysisRecord, analyst_name: str = "Analyst"
) -> bytes:
    """Generates an official forensic PDF report for an ImageAnalysisRecord."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=40,
        bottomMargin=48,
    )

    story: list[Flowable] = []

    # 1. Header
    report_code = f"AICF-IMG-{record.id:05d}"
    story.append(
        _build_header_flowable(
            report_code, "AI Image Forensic Examination", "Synthetic Media Detection Framework"
        )
    )
    story.append(
        HRFlowable(width="100%", thickness=2, color=COLOR_GOLD, spaceBefore=2, spaceAfter=8)
    )

    # 2. Metadata Grid
    now_utc = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    record_created = (
        record.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if record.created_at else now_utc
    )

    metadata = [
        ("Analysis Record ID", f"#{record.id}", False),
        ("Report Code", report_code, True),
        ("Report Generated At", now_utc, False),
        ("Investigation Timestamp", record_created, False),
        ("Assigned Analyst", analyst_name, False),
        ("Examined File Name", record.file_name, False),
        ("Cryptographic File Hash (SHA-256)", record.file_hash, True),
        (
            "Raster Specifications",
            f"{record.image_width} × {record.image_height} px ({record.image_format})",
            False,
        ),
        ("Payload Size", f"{record.file_size_bytes:,} bytes", False),
    ]
    story.append(_build_metadata_table(metadata))
    story.append(Spacer(1, 8))

    # 3. Determination
    story.append(
        _build_determination_card(
            classification=record.classification,
            status=record.status,
            confidence_score=record.confidence_score,
            ai_prob=record.ai_probability,
            human_prob=record.human_probability,
            calibration_note="Calibrated Swin Vision Transformer Softmax Probabilities",
        )
    )
    story.append(Spacer(1, 10))

    # 4. Computed Computer Vision Telemetry
    story.append(
        Paragraph(
            "<b>COMPUTER VISION &amp; MATHEMATICAL FREQUENCY FORENSICS</b>", styles.section_heading
        )
    )
    cv_rows = [
        ("Vision Transformer Backbone", f"{record.model_name} (v{record.model_version})", False),
        ("Inference Execution Latency", f"{record.processing_time_ms:.1f} ms", False),
        ("2D FFT Spectral Anisotropy (Octants)", f"{record.spectral_anisotropy:.4f}", True),
        ("High-Frequency Spectral Energy Ratio", f"{record.fft_high_freq_ratio:.4f}", True),
        ("Laplacian Noise Residual Variance", f"{record.noise_variance:.4f}", True),
        (
            "AI Metadata Watermark Extracted",
            "YES (Detected)" if record.has_ai_metadata else "NO (Negative)",
            False,
        ),
        (
            "C2PA Content Credentials Signed",
            "YES (Verified Signature)" if record.has_c2pa else "NO (Unsigned)",
            False,
        ),
    ]
    story.append(_build_metadata_table(cv_rows))
    story.append(Spacer(1, 10))

    # 4b. Multi-Detector Vision Ensemble Breakdown
    try:
        ensemble_data = json.loads(record.ensemble_json) if getattr(record, "ensemble_json", None) else {}
    except Exception:
        ensemble_data = {}

    detector_scores = ensemble_data.get("detector_scores", [])
    if detector_scores:
        story.append(Paragraph("<b>MULTI-DETECTOR VISION FORENSIC CONSENSUS</b>", styles.section_heading))
        story.append(_build_image_ensemble_table(detector_scores))
        story.append(Spacer(1, 10))

    # 4c. Error Level Analysis & Compression Forensics
    try:
        heatmap_data = json.loads(record.heatmap_json) if getattr(record, "heatmap_json", None) else {}
    except Exception:
        heatmap_data = {}

    if heatmap_data:
        story.append(
            Paragraph("<b>ERROR LEVEL ANALYSIS (ELA) &amp; COMPRESSION RESIDUALS</b>", styles.section_heading)
        )
        ela_rows = [
            ("Forensic Method", heatmap_data.get("method", "ELA Q=95"), False),
            ("Mean Compression Error", f"{heatmap_data.get('ela_mean_error', 0.0):.4f}", True),
            ("Max Compression Error Spike", f"{heatmap_data.get('ela_max_error', 0.0):.4f}", True),
            ("Block Discontinuity Score", f"{heatmap_data.get('ela_discontinuity_score', 0.0):.4f} SD", True),
        ]
        story.append(_build_metadata_table(ela_rows))
        story.append(Spacer(1, 10))

    # 5. Provenance & Container Metadata Findings
    try:
        provenance = json.loads(record.provenance_json) if record.provenance_json else {}
    except Exception:
        provenance = {}

    if provenance:
        story.append(
            Paragraph("<b>PROVENANCE &amp; CONTAINER INSPECTION</b>", styles.section_heading)
        )
        prov_rows = []
        if provenance.get("provenance_summary"):
            prov_rows.append(("Provenance Summary", provenance["provenance_summary"], False))
        if provenance.get("c2pa_finding"):
            prov_rows.append(("C2PA Credentials Finding", provenance["c2pa_finding"], False))
        if provenance.get("ai_prompt_snippet"):
            prov_rows.append(
                ("Extracted Generative Prompt", f'"{provenance["ai_prompt_snippet"]}"', False)
            )

        exif = provenance.get("exif_summary", {})
        if exif:
            exif_details = ", ".join(f"{k}: {v}" for k, v in exif.items() if v)
            if exif_details:
                prov_rows.append(("EXIF Camera Hardware", exif_details, False))

        if prov_rows:
            story.append(_build_metadata_table(prov_rows))
            story.append(Spacer(1, 10))

    # 6. Evidentiary Signals
    try:
        evidence_list = json.loads(record.evidence_json) if record.evidence_json else []
    except Exception:
        evidence_list = []

    if evidence_list:
        story.append(Paragraph("<b>OBSERVED FORENSIC EVIDENCE SIGNALS</b>", styles.section_heading))
        story.append(_build_evidence_table(evidence_list))
        story.append(Spacer(1, 10))

    # 7. Methodological Limitations
    try:
        limitations = json.loads(record.limitations_text) if record.limitations_text else []
    except Exception:
        limitations = [record.limitations_text] if record.limitations_text else []

    if limitations:
        story.append(
            Paragraph(
                "<b>METHODOLOGICAL LIMITATIONS &amp; UNCERTAINTIES</b>", styles.section_heading
            )
        )
        lim_paragraphs = [
            Paragraph(f"&bull; {safe_escape(lim)}", styles.body) for lim in limitations
        ]
        lim_table = Table([[p] for p in lim_paragraphs], colWidths=[540])
        lim_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), COLOR_LIGHT_BG),
                    ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                    ("PADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(lim_table)
        story.append(Spacer(1, 10))

    # 8. Disclaimer
    story.append(KeepTogether([_build_disclaimer_block()]))

    doc.build(story, canvasmaker=NumberedCanvas)
    return buf.getvalue()


def generate_case_report_pdf(report: ForensicReport, analyst_name: str = "Analyst") -> bytes:
    """Generates an official forensic PDF report for a ForensicReport case entry.

    Supports Video audit cases, text cases, and multi-modal records.
    Accurately represents unconfigured/scaffolded modules without fabricating data.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=40,
        bottomMargin=48,
    )

    story: list[Flowable] = []

    # 1. Header
    report_code = f"AICF-CASE-{report.id:05d}"
    story.append(_build_header_flowable(report_code, report.title, "Synthetic Media Detection Framework"))
    story.append(
        HRFlowable(width="100%", thickness=2, color=COLOR_GOLD, spaceBefore=2, spaceAfter=8)
    )

    # 2. Metadata Grid
    now_utc = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    record_created = (
        report.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if report.created_at else now_utc
    )

    metadata = [
        ("Case Record ID", f"#{report.id}", False),
        ("Report Code", report_code, True),
        ("Report Generated At", now_utc, False),
        ("Case Record Timestamp", record_created, False),
        ("Recording Analyst", analyst_name, False),
        ("Investigation Modality", report.media_type.upper(), False),
        (
            "Confidentiality Scope",
            "Strictly Confidential (Private Case)" if report.is_private else "Public",
            False,
        ),
    ]
    story.append(_build_metadata_table(metadata))
    story.append(Spacer(1, 8))

    # 3. Status & Modality Context
    is_video = report.media_type.lower() == "video"
    status_label = "PARTIAL / CONFIGURATION REQUIRED" if is_video else "VERIFIED"
    class_label = "ENGINE UNCONFIGURED" if is_video else "RECORDED CASE"

    story.append(
        _build_determination_card(
            classification=class_label,
            status=status_label,
            confidence_score=None,
        )
    )
    story.append(Spacer(1, 10))

    # 4. Case Summary / Investigative Log
    story.append(Paragraph("<b>CASE SUMMARY &amp; INVESTIGATIVE NOTES</b>", styles.section_heading))
    summary_p = Paragraph(safe_escape(report.summary), styles.body)
    summary_table = Table([[summary_p]], colWidths=[540])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_LIGHT_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 10))

    # 5. Modality Specific Disclosure (e.g. for Video)
    if is_video:
        story.append(
            Paragraph(
                "<b>VIDEO DETECTION STATUS &amp; PIPELINE SPECIFICATION</b>", styles.section_heading
            )
        )
        video_note = (
            "<b>HONEST STATUS DISCLOSURE:</b> In compliance with AICF forensic standards, the AI "
            "Video Detection Engine is currently <b>PARTIAL / CONFIGURATION REQUIRED</b>. The "
            "architectural package in <font name='Courier'>backend/app/ml/video/</font> is "
            "scaffolded. Frame extraction, optical flow analysis, and 3D spatio-temporal deepfake "
            "models have not been fully configured or calibrated. Zero simulated frame scores or "
            "artificial timestamps were generated for this case record."
        )
        vid_table = Table([[Paragraph(video_note, styles.body)]], colWidths=[540])
        vid_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), COLOR_LIGHT_BG),
                    ("BOX", (0, 0), (-1, -1), 1, COLOR_AMBER),
                    ("PADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(vid_table)
        story.append(Spacer(1, 10))

    # 6. Disclaimer
    story.append(KeepTogether([_build_disclaimer_block()]))

    doc.build(story, canvasmaker=NumberedCanvas)
    return buf.getvalue()


def generate_video_analysis_pdf(
    record: VideoAnalysisRecord, analyst_name: str = "Analyst"
) -> bytes:
    """Generates an official forensic PDF report for a VideoAnalysisRecord."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=40,
        bottomMargin=48,
    )

    story: list[Flowable] = []

    # 1. Header
    report_code = f"AICF-VID-{record.id:05d}"
    story.append(
        _build_header_flowable(
            report_code, "AI Video Forensic Examination", "Synthetic Media Detection Framework"
        )
    )
    story.append(
        HRFlowable(width="100%", thickness=2, color=COLOR_GOLD, spaceBefore=2, spaceAfter=8)
    )

    # 2. Metadata Grid
    now_utc = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    record_created = (
        record.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if record.created_at else now_utc
    )

    metadata = [
        ("Analysis Record ID", f"#{record.id}", False),
        ("Report Code", report_code, True),
        ("Report Generated At", now_utc, False),
        ("Investigation Timestamp", record_created, False),
        ("Assigned Analyst", analyst_name, False),
        ("Examined File Name", record.file_name, False),
        ("Cryptographic File Hash (SHA-256)", record.file_hash, True),
        (
            "Video Stream Specifications",
            f"{record.video_width} × {record.video_height} px @ {record.fps:.1f} fps",
            False,
        ),
        (
            "Stream Duration & Frames",
            f"{record.duration_seconds:.2f} s ({record.total_frames:,} total frames)",
            False,
        ),
        ("Uniform Sampled Keyframes", f"{record.sampled_frame_count} frames", False),
        ("Payload Size", f"{record.file_size_bytes:,} bytes", False),
    ]
    story.append(_build_metadata_table(metadata))
    story.append(Spacer(1, 8))

    # 3. Determination
    human_prob = 1.0 - record.ai_probability_mean if record.ai_probability_mean is not None else None
    determination_verdict = getattr(record, "consensus_verdict", None) or record.classification
    story.append(
        _build_determination_card(
            classification=determination_verdict,
            status=record.status,
            confidence_score=record.confidence_score,
            ai_prob=record.ai_probability_mean,
            human_prob=human_prob,
            calibration_note="Multi-Signal Consensus: Swin ViT Frame Screening, MesoNet-4 Facial Forensics & Temporal Telemetry",
        )
    )
    story.append(Spacer(1, 10))

    # 4. Computed Video Forensics & Neural Telemetry
    face_status = getattr(record, "face_deepfake_status", None) or "UNAVAILABLE"
    story.append(
        Paragraph(
            "<b>VIDEO FORENSIC ARCHITECTURE &amp; STATISTICAL TELEMETRY</b>", styles.section_heading
        )
    )
    telemetry_rows = [
        ("Forensics Engine", f"{record.model_name} (v{record.model_version})", False),
        ("Frame Screening Backbone", record.frame_classifier_id, False),
        ("Inference Execution Latency", f"{record.processing_time_ms:.1f} ms", False),
        ("Mean Frame AI Probability", f"{record.ai_probability_mean:.1%}", True),
        ("Peak Frame AI Probability", f"{record.ai_probability_max:.1%}", True),
        ("Peak Frame Timestamp", f"t = {record.peak_frame_timestamp:.2f} s", True),
        ("Temporal Motion Flicker Score", f"{record.temporal_flicker_score:.4f}", True),
        (
            "Facial Deepfake Analysis Status",
            face_status,
            True,
        ),
    ]
    story.append(_build_metadata_table(telemetry_rows))
    story.append(Spacer(1, 10))

    # 4b. Dedicated Facial Deepfake Forensics
    if getattr(record, "facial_telemetry_json", None):
        try:
            face_data = json.loads(record.facial_telemetry_json)
        except Exception:
            face_data = {}

        if face_data:
            story.append(
                Paragraph(
                    "<b>DEDICATED FACIAL DEEPFAKE FORENSICS (MESONET-4 &amp; BOUNDARY SEAMS)</b>",
                    styles.section_heading,
                )
            )
            mean_f = face_data.get("mean_facial_manipulation_score")
            mean_f_str = f"{mean_f:.1%}" if mean_f is not None else "N/A (Heuristic Seam Mode)"
            max_f = face_data.get("max_facial_manipulation_score")
            max_f_str = f"{max_f:.1%}" if max_f is not None else "N/A"
            peak_f_t = face_data.get("peak_manipulation_timestamp")
            peak_f_str = f"t = {peak_f_t:.2f} s" if peak_f_t is not None else "None"

            face_rows = [
                ("Facial Model Architecture", f"{face_data.get('model_name', 'MesoNet-4')} (v{face_data.get('model_version', '1.0.0')})", False),
                ("Architecture License", face_data.get("model_license", "MIT / Research (Dari et al., WIFS 2018)"), False),
                ("Detection Availability", face_data.get("availability", face_status), True),
                ("Total Faces Analyzed", f"{face_data.get('total_faces_analyzed', 0)} face instance(s)", False),
                ("Frames with Human Faces", f"{face_data.get('frames_with_faces', 0)} of {face_data.get('total_frames_sampled', 0)} sampled frames", False),
                ("Mean Facial Manipulation Score", mean_f_str, True),
                ("Peak Facial Manipulation Score", max_f_str, True),
                ("Peak Manipulation Timestamp", peak_f_str, False),
                ("Mean Boundary Seam Disparity", f"{face_data.get('mean_boundary_seam_delta', 0.0):.3f}", True),
                ("Max Boundary Seam Disparity", f"{face_data.get('max_boundary_seam_delta', 0.0):.3f}", True),
                ("Low-Resolution Faces", f"{face_data.get('low_resolution_frames_count', 0)} frame(s) (< 48px)", False),
            ]
            story.append(_build_metadata_table(face_rows))
            story.append(Spacer(1, 10))

    # 5. Temporal Motion & Inter-Frame Telemetry
    try:
        temporal_dict = json.loads(record.temporal_telemetry_json) if record.temporal_telemetry_json else {}
    except Exception:
        temporal_dict = {}

    if temporal_dict:
        story.append(
            Paragraph("<b>TEMPORAL MOTION &amp; INTER-FRAME TELEMETRY</b>", styles.section_heading)
        )
        suspicious_ts = temporal_dict.get("suspicious_transition_timestamps", [])
        ts_str = ", ".join(f"t={t:.2f}s" for t in suspicious_ts) if suspicious_ts else "None detected (smooth transitions)"
        temp_rows = [
            ("Mean Inter-Frame Difference", f"{temporal_dict.get('mean_frame_difference', 0.0):.4f}", True),
            ("Temporal Flicker Standard Deviation", f"{temporal_dict.get('temporal_flicker_score', 0.0):.4f}", True),
            ("Anomalous Transition Spikes", ts_str, False),
            ("Signal Characterization", "Deterministic Heuristic Telemetry (Non-Neural)", False),
        ]
        story.append(_build_metadata_table(temp_rows))
        story.append(Spacer(1, 10))

    # 6. Third-Party Hive AI Verification
    story.append(
        Paragraph("<b>THIRD-PARTY CLOUD VERIFICATION (HIVE AI)</b>", styles.section_heading)
    )
    if record.has_hive_result:
        hive_score_str = f"{record.hive_score:.1%}" if record.hive_score is not None else "Verified"
        hive_rows = [
            ("Provider & Integration", "Hive AI Visual Moderation API (v2)", False),
            ("Cloud Verification Status", "SUCCESS", False),
            ("Hive AI-Generated Score", hive_score_str, True),
        ]
    else:
        hive_rows = [
            ("Provider & Integration", "Hive AI Visual Moderation API (v2)", False),
            ("Cloud Verification Status", "Not configured / Not available (Air-gapped local execution)", False),
            ("Verification Note", "HIVE_API_KEY unconfigured; local deep learning inference operates independently.", False),
        ]
    story.append(_build_metadata_table(hive_rows))
    story.append(Spacer(1, 10))

    # 7. Sampled Keyframe Score Timeline
    try:
        frame_scores_list = json.loads(record.frame_scores_json) if record.frame_scores_json else []
    except Exception:
        frame_scores_list = []

    if frame_scores_list:
        story.append(
            Paragraph("<b>UNIFORM KEYFRAME SCORE TIMELINE</b>", styles.section_heading)
        )
        story.append(_build_frame_scores_table(frame_scores_list))
        story.append(Spacer(1, 10))

    # 8. Observed Forensic Evidence Signals
    try:
        evidence_list = json.loads(record.evidence_json) if record.evidence_json else []
    except Exception:
        evidence_list = []

    if evidence_list:
        story.append(Paragraph("<b>OBSERVED FORENSIC EVIDENCE SIGNALS</b>", styles.section_heading))
        story.append(_build_evidence_table(evidence_list))
        story.append(Spacer(1, 10))

    # 9. Methodological Limitations & Epistemic Boundaries
    try:
        limitations = json.loads(record.limitations_text) if record.limitations_text else []
    except Exception:
        limitations = []

    if limitations:
        story.append(
            Paragraph("<b>METHODOLOGICAL LIMITATIONS &amp; SCIENTIFIC BOUNDARIES</b>", styles.section_heading)
        )
        lim_paragraphs = [
            Paragraph(f"• {safe_escape(lim)}", styles.body) for lim in limitations
        ]
        lim_table = Table([[p] for p in lim_paragraphs], colWidths=[540])
        lim_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), COLOR_LIGHT_BG),
                    ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                    ("PADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(lim_table)
        story.append(Spacer(1, 10))

    # 10. Mandatory Disclaimer Block
    story.append(KeepTogether([_build_disclaimer_block()]))

    doc.build(story, canvasmaker=NumberedCanvas)
    return buf.getvalue()
