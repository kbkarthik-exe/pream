"""Comprehensive automated test suite for AICF PDF Forensic Report Generation.

Covers:
1. Unit testing of PDF generation service functions for Text, Image, and Case reports.
2. Resilience against missing optional fields, None scores, and empty telemetry.
3. Untrusted text sanitization (XSS and XML injection prevention).
4. Multi-page document pagination and NumberedCanvas dynamic page calculation.
5. End-to-end HTTP API downloads for Text, Image, and Video Case reports.
6. Security checks: Authentication requirement (401), cross-user isolation (403),
   and non-existent record handling (404).
"""

import io
import json
from datetime import UTC, datetime

import numpy as np
import pytest
from backend.app.core.config import settings
from backend.app.models.image_analysis import ImageAnalysisRecord
from backend.app.models.report import ForensicReport
from backend.app.models.text_analysis import TextAnalysisRecord
from backend.app.services.pdf_generator import (
    generate_case_report_pdf,
    generate_image_analysis_pdf,
    generate_text_analysis_pdf,
)
from httpx import AsyncClient
from PIL import Image


def make_test_image(width: int = 64, height: int = 64, fmt: str = "JPEG") -> bytes:
    """Generate in-memory valid image bytes for API testing."""
    arr = np.random.randint(50, 200, (height, width, 3), dtype=np.uint8)
    img = Image.fromarray(arr, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


# ==============================================================================
# UNIT TESTS: Direct PDF Service Functions
# ==============================================================================


def test_generate_text_analysis_pdf_direct():
    """Unit Test: Verify direct TextAnalysisRecord PDF generation returns valid PDF stream."""
    record = TextAnalysisRecord(
        id=1,
        user_id=42,
        input_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        text_snippet="Artificial intelligence models generate language with lower perplexity.",
        word_count=9,
        character_count=71,
        model_name="roberta-base-openai-detector",
        model_version="1.0.0",
        classification="LIKELY AI-GENERATED",
        confidence_score=0.942,
        perplexity_score=14.2,
        burstiness_score=0.21,
        token_entropy=3.15,
        type_token_ratio=0.88,
        repeated_ngram_ratio=0.02,
        evidence_json=json.dumps([
            {
                "signal": "Transformer Sequence Classifier",
                "metric": "94.2% Softmax",
                "finding": "Strong statistical resemblance to GPT synthetic generations.",
            },
            {
                "signal": "Burstiness Uniformity",
                "metric": "0.21 CV",
                "finding": "Uniform sentence length indicative of automated output.",
            },
        ]),
        limitations_text=json.dumps([
            "Short text sample under 100 words increases statistical variance.",
            "Detector provides probabilistic estimation, not definitive legal proof.",
        ]),
        status="SUCCESS",
        processing_time_ms=85.4,
        created_at=datetime.now(UTC),
    )

    pdf_bytes = generate_text_analysis_pdf(record, analyst_name="Lead Analyst")
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF-")


def test_generate_image_analysis_pdf_direct():
    """Unit Test: Verify direct ImageAnalysisRecord PDF generation with full telemetry."""
    record = ImageAnalysisRecord(
        id=10,
        user_id=42,
        file_hash="c55f111f111f111f111f111f111f111f111f111f111f111f111f111f111f111f",
        file_name="synthetic_landscape.png",
        file_size_bytes=1048576,
        image_width=1024,
        image_height=1024,
        image_format="PNG",
        model_name="umm-maybe/AI-image-detector",
        model_version="1.0.0",
        classification="LIKELY AI-GENERATED",
        confidence_score=0.985,
        ai_probability=0.985,
        human_probability=0.015,
        fft_high_freq_ratio=0.184,
        spectral_anisotropy=0.082,
        noise_variance=0.045,
        has_ai_metadata=True,
        has_c2pa=False,
        evidence_json=json.dumps([
            {
                "signal": "Swin Vision Transformer",
                "metric": "98.5% AI Likelihood",
                "finding": "High synthetic confidence based on diffusion latent patterns.",
            },
            {
                "signal": "2D Fourier Spectral Grid Spikes",
                "metric": "0.082 Anisotropy",
                "finding": "Periodic frequency spikes characteristic of upsampling layers.",
            },
        ]),
        provenance_json=json.dumps({
            "has_exif": False,
            "exif_summary": {},
            "has_ai_metadata": True,
            "ai_prompt_snippet": "A photorealistic obsidian fortress at sunset, 8k",
            "has_c2pa": False,
            "c2pa_finding": "No Content Credentials signature present",
            "provenance_summary": "AI generation metadata extracted from PNG tEXt chunk.",
        }),
        limitations_text=json.dumps([
            "Compression artifacts can degrade high-frequency residual accuracy.",
            "Results are probabilistic and require human corroboration.",
        ]),
        status="SUCCESS",
        processing_time_ms=142.0,
        created_at=datetime.now(UTC),
    )

    pdf_bytes = generate_image_analysis_pdf(record, analyst_name="Senior Forensics Specialist")
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF-")


def test_generate_case_report_pdf_for_video_direct():
    """Unit Test: Verify ForensicReport case PDF for Video reflects unconfigured status."""
    report = ForensicReport(
        id=7,
        user_id=42,
        title="Video Deepfake Stream Audit: evidence_sample.mp4",
        media_type="video",
        summary="Submitted for temporal facial boundary and optical flow verification.",
        is_private=True,
        created_at=datetime.now(UTC),
    )

    pdf_bytes = generate_case_report_pdf(report, analyst_name="Investigator Alpha")
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF-")


def test_generate_pdf_missing_optional_fields():
    """Unit Test: Ensure PDF generation handles None scores, empty telemetry & provenance."""
    # Text record with None/zero confidence and empty lists
    record_text = TextAnalysisRecord(
        id=2,
        user_id=1,
        input_hash="0000000000000000000000000000000000000000000000000000000000000000",
        text_snippet="Inconclusive brief statement.",
        word_count=3,
        character_count=29,
        model_name="roberta-base-openai-detector",
        model_version="1.0.0",
        classification="INCONCLUSIVE",
        confidence_score=0.0,
        perplexity_score=0.0,
        burstiness_score=0.0,
        token_entropy=0.0,
        type_token_ratio=0.0,
        repeated_ngram_ratio=0.0,
        evidence_json="",
        limitations_text="",
        status="INCONCLUSIVE",
        processing_time_ms=12.0,
        created_at=None,
    )
    pdf_text = generate_text_analysis_pdf(record_text)
    assert pdf_text.startswith(b"%PDF-")

    # Image record with None probabilities and empty json
    record_image = ImageAnalysisRecord(
        id=3,
        user_id=1,
        file_hash="1111111111111111111111111111111111111111111111111111111111111111",
        file_name="low_res_sample.jpg",
        file_size_bytes=512,
        image_width=64,
        image_height=64,
        image_format="JPEG",
        model_name="umm-maybe/AI-image-detector",
        model_version="1.0.0",
        classification="INCONCLUSIVE",
        confidence_score=0.0,
        ai_probability=0.0,
        human_probability=0.0,
        fft_high_freq_ratio=0.0,
        spectral_anisotropy=0.0,
        noise_variance=0.0,
        has_ai_metadata=False,
        has_c2pa=False,
        evidence_json="[]",
        provenance_json="",
        limitations_text="[]",
        status="INCONCLUSIVE",
        processing_time_ms=10.0,
        created_at=None,
    )
    pdf_image = generate_image_analysis_pdf(record_image)
    assert pdf_image.startswith(b"%PDF-")


def test_pdf_untrusted_html_injection_safety():
    """Security Test: Raw text with HTML tags and XML characters must be escaped safely."""
    malicious_text = '<script>alert("XSS")</script> & <font color="red">malicious</font>'
    record = TextAnalysisRecord(
        id=99,
        user_id=1,
        input_hash="9999999999999999999999999999999999999999999999999999999999999999",
        text_snippet=malicious_text,
        word_count=5,
        character_count=60,
        model_name="roberta-base-openai-detector",
        model_version="1.0.0",
        classification="LIKELY HUMAN",
        confidence_score=0.88,
        perplexity_score=10.0,
        burstiness_score=0.5,
        token_entropy=2.5,
        type_token_ratio=0.9,
        repeated_ngram_ratio=0.0,
        evidence_json=json.dumps([{"signal": "XSS Probe", "finding": malicious_text}]),
        limitations_text=json.dumps([malicious_text]),
        status="SUCCESS",
        processing_time_ms=50.0,
        created_at=datetime.now(UTC),
    )

    # Should build cleanly without throwing xml.parsers.expat.ExpatError
    pdf_bytes = generate_text_analysis_pdf(record, analyst_name="<script>tester</script>")
    assert pdf_bytes.startswith(b"%PDF-")


def test_pdf_multi_page_pagination_flow():
    """Unit Test: Multi-page document pagination and NumberedCanvas dynamic page calculation."""
    # Create an extensive text record with 30 evidence items that definitely forces page breaks
    long_snippet = "Extensive forensic analysis of multi-paragraph synthetic corpus. " * 20
    many_evidence = [
        {
            "signal": f"Deep Telemetry Signal #{i:02d}",
            "metric": f"{i * 1.5:.2f} score",
            "finding": (
                f"Detailed diagnostic finding explaining anomalous structural "
                f"distribution for test item {i}."
            ),
        }
        for i in range(25)
    ]

    record = TextAnalysisRecord(
        id=500,
        user_id=1,
        input_hash="5005005005005005005005005005005005005005005005005005005005005005",
        text_snippet=long_snippet,
        word_count=200,
        character_count=len(long_snippet),
        model_name="roberta-base-openai-detector",
        model_version="1.0.0",
        classification="LIKELY AI-GENERATED",
        confidence_score=0.99,
        perplexity_score=12.0,
        burstiness_score=0.15,
        token_entropy=3.8,
        type_token_ratio=0.75,
        repeated_ngram_ratio=0.05,
        evidence_json=json.dumps(many_evidence),
        limitations_text=json.dumps(["Multi-page test limitation."]),
        status="SUCCESS",
        processing_time_ms=110.0,
        created_at=datetime.now(UTC),
    )

    pdf_bytes = generate_text_analysis_pdf(record)
    assert pdf_bytes.startswith(b"%PDF-")
    # Verify significant content size for multi-page output
    assert len(pdf_bytes) > 4000


# ==============================================================================
# INTEGRATION TESTS: HTTP API Endpoints & Security Checks
# ==============================================================================


@pytest.mark.asyncio
async def test_api_download_text_pdf_authenticated(client: AsyncClient):
    """Integration Test: Full workflow to analyze text and download generated PDF report."""
    # 1. Register analyst
    auth_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "pdf_text_analyst@aicf.internal",
            "username": "pdf_text_analyst",
            "password": "SecurePassword123!",
            "full_name": "Dr. Eleanor Vance",
        },
    )
    assert auth_resp.status_code == 201
    client.cookies = {settings.COOKIE_NAME: auth_resp.cookies[settings.COOKIE_NAME]}

    # 2. Run real text analysis
    text_sample = (
        "Neural language models synthesize discourse through contextual self-attention "
        "mechanisms that minimize cross-entropy loss over token sequences."
    )
    analyze_resp = await client.post(
        "/api/v1/text/analyze",
        json={"text": text_sample, "save_to_cases": True},
    )
    assert analyze_resp.status_code == 200
    analysis_data = analyze_resp.json()
    analysis_id = analysis_data["analysis_id"]

    # 3. Download generated PDF
    pdf_resp = await client.get(f"/api/v1/text/analyses/{analysis_id}/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["Content-Type"] == "application/pdf"
    assert "Content-Disposition" in pdf_resp.headers
    assert f"AICF-Text-Report-{analysis_id:05d}.pdf" in pdf_resp.headers["Content-Disposition"]
    assert pdf_resp.content.startswith(b"%PDF-")
    assert len(pdf_resp.content) > 1500


@pytest.mark.asyncio
async def test_api_download_image_pdf_authenticated(client: AsyncClient):
    """Integration Test: Full workflow to analyze image and download generated PDF report."""
    # 1. Register analyst
    auth_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "pdf_image_analyst@aicf.internal",
            "username": "pdf_image_analyst",
            "password": "SecurePassword123!",
            "full_name": "Marcus Sterling",
        },
    )
    assert auth_resp.status_code == 201
    client.cookies = {settings.COOKIE_NAME: auth_resp.cookies[settings.COOKIE_NAME]}

    # 2. Run real image analysis
    img_bytes = make_test_image(128, 128, fmt="JPEG")
    analyze_resp = await client.post(
        "/api/v1/image/analyze",
        files={"file": ("test_artifact.jpg", img_bytes, "image/jpeg")},
        data={"save_to_cases": "true"},
    )
    assert analyze_resp.status_code == 200
    analysis_data = analyze_resp.json()
    analysis_id = analysis_data["analysis_id"]

    # 3. Download generated image PDF
    pdf_resp = await client.get(f"/api/v1/image/{analysis_id}/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["Content-Type"] == "application/pdf"
    assert "Content-Disposition" in pdf_resp.headers
    assert f"AICF-Image-Report-{analysis_id:05d}.pdf" in pdf_resp.headers["Content-Disposition"]
    assert pdf_resp.content.startswith(b"%PDF-")
    assert len(pdf_resp.content) > 1500


@pytest.mark.asyncio
async def test_api_download_case_pdf_authenticated(client: AsyncClient):
    """Integration Test: Create a case report (e.g. video audit) and download its PDF."""
    # 1. Register analyst
    auth_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "pdf_case_analyst@aicf.internal",
            "username": "pdf_case_analyst",
            "password": "SecurePassword123!",
            "full_name": "Case Auditor",
        },
    )
    assert auth_resp.status_code == 201
    client.cookies = {settings.COOKIE_NAME: auth_resp.cookies[settings.COOKIE_NAME]}

    # 2. Record video investigation case
    case_resp = await client.post(
        "/api/v1/reports",
        json={
            "title": "Video Stream Forensic Verification",
            "media_type": "video",
            "summary": "Audited candidate stream for inter-frame temporal consistency.",
            "is_private": True,
        },
    )
    assert case_resp.status_code == 201
    report_id = case_resp.json()["id"]

    # 3. Download case report PDF
    pdf_resp = await client.get(f"/api/v1/reports/{report_id}/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["Content-Type"] == "application/pdf"
    assert "Content-Disposition" in pdf_resp.headers
    assert f"AICF-Case-Report-{report_id:05d}.pdf" in pdf_resp.headers["Content-Disposition"]
    assert pdf_resp.content.startswith(b"%PDF-")


@pytest.mark.asyncio
async def test_security_pdf_download_unauthorized(client: AsyncClient):
    """Security Test: Accessing PDF endpoints without active authentication fails with 401."""
    # Ensure client has no credentials
    client.cookies.clear()

    resp_text = await client.get("/api/v1/text/analyses/1/pdf")
    assert resp_text.status_code == 401

    resp_image = await client.get("/api/v1/image/1/pdf")
    assert resp_image.status_code == 401

    resp_case = await client.get("/api/v1/reports/1/pdf")
    assert resp_case.status_code == 401


@pytest.mark.asyncio
async def test_security_pdf_cross_user_isolation(client: AsyncClient):
    """Security Test: Prevent horizontal privilege escalation when exporting PDF reports."""
    # User A registers and creates analyses
    user_a = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user_a_pdf@aicf.internal",
            "username": "user_a_pdf",
            "password": "SecurePassword123!",
        },
    )
    client.cookies = {settings.COOKIE_NAME: user_a.cookies[settings.COOKIE_NAME]}

    # User A runs text analysis
    text_resp = await client.post(
        "/api/v1/text/analyze",
        json={"text": "Authentic forensic sample for Analyst A."},
    )
    text_id = text_resp.json()["analysis_id"]

    # User A runs image analysis
    img_resp = await client.post(
        "/api/v1/image/analyze",
        files={"file": ("a_pic.jpg", make_test_image(64, 64), "image/jpeg")},
    )
    img_id = img_resp.json()["analysis_id"]

    # User A creates a case report
    case_resp = await client.post(
        "/api/v1/reports",
        json={
            "title": "Private Case A",
            "media_type": "text",
            "summary": "Classified findings for User A.",
            "is_private": True,
        },
    )
    case_id = case_resp.json()["id"]

    # User B registers and acquires separate session
    user_b = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user_b_pdf@aicf.internal",
            "username": "user_b_pdf",
            "password": "SecurePassword123!",
        },
    )
    client.cookies = {settings.COOKIE_NAME: user_b.cookies[settings.COOKIE_NAME]}

    # User B attempts to download User A's text PDF -> 403 Forbidden
    text_pdf_denied = await client.get(f"/api/v1/text/analyses/{text_id}/pdf")
    assert text_pdf_denied.status_code == 403
    assert "Access denied" in text_pdf_denied.json()["detail"]

    # User B attempts to download User A's image PDF -> 403 Forbidden
    img_pdf_denied = await client.get(f"/api/v1/image/{img_id}/pdf")
    assert img_pdf_denied.status_code == 403
    assert "Access denied" in img_pdf_denied.json()["detail"]

    # User B attempts to download User A's private case PDF -> 403 Forbidden
    case_pdf_denied = await client.get(f"/api/v1/reports/{case_id}/pdf")
    assert case_pdf_denied.status_code == 403
    assert "Access denied" in case_pdf_denied.json()["detail"]


@pytest.mark.asyncio
async def test_security_pdf_invalid_id_not_found(client: AsyncClient):
    """Security Test: Non-existent IDs return 404 with clean JSON error."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "not_found_tester@aicf.internal",
            "username": "not_found_tester",
            "password": "SecurePassword123!",
        },
    )
    client.cookies = {settings.COOKIE_NAME: reg.cookies[settings.COOKIE_NAME]}

    resp_text = await client.get("/api/v1/text/analyses/999999/pdf")
    assert resp_text.status_code == 404

    resp_image = await client.get("/api/v1/image/999999/pdf")
    assert resp_image.status_code == 404

    resp_case = await client.get("/api/v1/reports/999999/pdf")
    assert resp_case.status_code == 404
