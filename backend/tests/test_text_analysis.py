import pytest
from backend.app.core.config import settings
from backend.app.ml.text import extract_linguistic_features, text_detector
from httpx import AsyncClient


async def create_authenticated_analyst(client: AsyncClient, suffix: str = "1") -> dict[str, str]:
    """Helper to register and authenticate an analyst session."""
    payload = {
        "email": f"analyst_{suffix}@aicf.internal",
        "username": f"analyst_{suffix}",
        "password": "SecurePassword123!",
        "full_name": f"Analyst {suffix}",
    }
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201
    return {
        settings.COOKIE_NAME: resp.cookies[settings.COOKIE_NAME],
    }


# 1. Authentication Requirements
@pytest.mark.asyncio
async def test_text_analysis_unauthenticated(client: AsyncClient):
    """Unauthenticated requests must be rejected with 401 Unauthorized."""
    response = await client.post(
        "/api/v1/text/analyze",
        json={"text": "This is a legitimate test text sample."},
    )
    assert response.status_code == 401
    assert "Authentication required" in response.json()["detail"]


# 2. Empty Text Validation
@pytest.mark.asyncio
async def test_text_analysis_empty_text(client: AsyncClient):
    """Empty or whitespace-only text must return HTTP 422 Unprocessable Entity."""
    cookies = await create_authenticated_analyst(client, "empty")
    client.cookies = cookies

    response = await client.post(
        "/api/v1/text/analyze",
        json={"text": "    "},
    )
    assert response.status_code == 422


# 3. Text Too Short
@pytest.mark.asyncio
async def test_text_analysis_too_short(client: AsyncClient):
    """Text under minimum word/character bounds returns INCONCLUSIVE status."""
    cookies = await create_authenticated_analyst(client, "short")
    client.cookies = cookies

    response = await client.post(
        "/api/v1/text/analyze",
        json={"text": "Short snippet."},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "INCONCLUSIVE"
    assert data["classification"] == "INCONCLUSIVE"
    assert "insufficient" in data["evidence"][0]["finding"].lower()


# 4. Maximum Input Length Exceeded
@pytest.mark.asyncio
async def test_text_analysis_max_length_exceeded(client: AsyncClient):
    """Inputs exceeding configured maximum characters must return HTTP 422."""
    cookies = await create_authenticated_analyst(client, "toolong")
    client.cookies = cookies

    oversized_text = "word " * 4000  # > 15,000 chars
    response = await client.post(
        "/api/v1/text/analyze",
        json={"text": oversized_text},
    )
    assert response.status_code == 422


# 5. Malformed Requests
@pytest.mark.asyncio
async def test_text_analysis_malformed_request(client: AsyncClient):
    """Malformed request payload missing required fields must return HTTP 422."""
    cookies = await create_authenticated_analyst(client, "malformed")
    client.cookies = cookies

    response = await client.post(
        "/api/v1/text/analyze",
        json={"invalid_field": 123},
    )
    assert response.status_code == 422


# 6. Model Unavailable / Loading Failure Handling
@pytest.mark.asyncio
async def test_text_analysis_model_unavailable(client: AsyncClient, monkeypatch):
    """When the model engine is unavailable or unconfigured, it must return BLOCKED status."""
    cookies = await create_authenticated_analyst(client, "unavail")
    client.cookies = cookies

    # Mock unconfigured model state
    monkeypatch.setattr(text_detector, "_is_loaded", False)
    monkeypatch.setattr(text_detector, "load_model", lambda: False)
    monkeypatch.setattr(text_detector, "_load_error", "Model weights file missing.")

    sample = (
        "The advancement of neural network architectures has profoundly impacted digital "
        "forensics. Language models generate syntactic structures with varying perplexity. "
        "This long sample contains sufficient tokens for empirical statistical verification."
    )
    response = await client.post(
        "/api/v1/text/analyze",
        json={"text": sample},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "BLOCKED"
    assert data["confidence_score"] is None
    assert any("unconfigured" in lim.lower() for lim in data["limitations"])


# 7. Uncertain Model Output
@pytest.mark.asyncio
async def test_text_analysis_uncertain_output(client: AsyncClient, monkeypatch):
    """When probabilities fall in the uncertainty boundary, return INCONCLUSIVE."""
    cookies = await create_authenticated_analyst(client, "uncertain")
    client.cookies = cookies

    # Unit-test mock: Model returning ambiguous logits (50% AI / 50% Human)
    def mock_analyze(text: str):
        feats = extract_linguistic_features(text)
        return {
            "status": "SUCCESS",
            "classification": "INCONCLUSIVE",
            "confidence_score": 0.51,
            "ai_probability": 0.51,
            "human_probability": 0.49,
            "features": feats,
            "evidence": [
                {
                    "signal": "Transformer Softmax Distribution",
                    "metric": "AI: 51% | Human: 49%",
                    "finding": "Indeterminate probability in uncertainty interval.",
                }
            ],
            "limitations": ["Model output is in the uncertainty interval."],
            "word_count": feats["word_count"],
            "character_count": feats["char_count"],
            "input_hash": "mockhash123",
            "text_snippet": text[:50],
            "model_name": "test-mock-detector",
            "model_version": "1.0.0",
            "processing_time_ms": 12.5,
        }

    monkeypatch.setattr(text_detector, "analyze_text", mock_analyze)

    sample = (
        "This is an ambiguous text sample with enough words to pass the initial length gate. "
        "It features multiple sentences designed to evaluate how the uncertainty interval "
        "handles indeterminate probabilities without jumping to binary false certainty."
    )
    response = await client.post(
        "/api/v1/text/analyze",
        json={"text": sample},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["classification"] == "INCONCLUSIVE"
    assert data["confidence_score"] == 0.51


# 8. Valid Inference with Configured Engine
@pytest.mark.asyncio
async def test_text_analysis_valid_inference(client: AsyncClient):
    """Real or unit-tested inference must compute deterministic linguistic features."""
    cookies = await create_authenticated_analyst(client, "valid")
    client.cookies = cookies

    sample = (
        "Artificial intelligence and natural language processing systems continue to "
        "evolve rapidly. Computational researchers examine burstiness, vocabulary diversity, "
        "and syntactic patterns to distinguish machine output from human prose. "
        "In digital forensics, transparency and calibrated uncertainty are paramount "
        "to maintaining evidentiary integrity."
    )
    response = await client.post(
        "/api/v1/text/analyze",
        json={"text": sample, "save_to_cases": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["SUCCESS", "INCONCLUSIVE"]
    assert data["classification"] in ["LIKELY AI-GENERATED", "LIKELY HUMAN", "INCONCLUSIVE"]
    assert data["word_count"] > 30
    assert data["burstiness_score"] >= 0.0
    assert data["type_token_ratio"] > 0.0
    assert len(data["evidence"]) >= 3
    assert len(data["limitations"]) > 0
    assert data["processing_time_ms"] > 0
    assert data["case_report_id"] is not None


# 9. Database Persistence and History
@pytest.mark.asyncio
async def test_text_analysis_history(client: AsyncClient):
    """Analyzed records must persist in the database and be retrievable via history endpoint."""
    cookies = await create_authenticated_analyst(client, "history")
    client.cookies = cookies

    sample = (
        "Forensic telemetry records provide audit trails for investigator verification. "
        "Each analysis computes deterministic language statistics and model softmax outputs "
        "to ensure reproducible authenticity findings."
    )
    post_res = await client.post(
        "/api/v1/text/analyze",
        json={"text": sample},
    )
    assert post_res.status_code == 200
    analysis_id = post_res.json()["analysis_id"]

    # Retrieve history list
    list_res = await client.get("/api/v1/text/analyses")
    assert list_res.status_code == 200
    history = list_res.json()
    assert len(history) >= 1
    assert any(h["id"] == analysis_id for h in history)

    # Retrieve specific item
    get_res = await client.get(f"/api/v1/text/analyses/{analysis_id}")
    assert get_res.status_code == 200
    item = get_res.json()
    assert item["analysis_id"] == analysis_id
    assert item["word_count"] > 20


# 10. Cross-User Data Isolation
@pytest.mark.asyncio
async def test_text_analysis_user_isolation(client: AsyncClient):
    """Analyst B must not be permitted to view Analyst A's private text analysis."""
    # Analyst A creates an analysis
    cookies_a = await create_authenticated_analyst(client, "user_a")
    client.cookies = cookies_a

    sample = (
        "Confidential forensic case notes regarding synthetic content investigation. "
        "This data must remain strictly isolated to the originating investigator account."
    )
    res_a = await client.post("/api/v1/text/analyze", json={"text": sample})
    assert res_a.status_code == 200
    analysis_id = res_a.json()["analysis_id"]

    # Analyst B attempts to access Analyst A's analysis
    cookies_b = await create_authenticated_analyst(client, "user_b")
    client.cookies = cookies_b

    res_b = await client.get(f"/api/v1/text/analyses/{analysis_id}")
    assert res_b.status_code == 403
    assert "Access denied" in res_b.json()["detail"]


# 11. Deterministic Linguistic Features Unit Test
def test_linguistic_features_deterministic():
    """Linguistic features must be strictly deterministic across repeated evaluations."""
    text = (
        "Short sentence one. This is a significantly longer second sentence crafted "
        "to induce measurable variation in sentence length and burstiness. Third."
    )
    f1 = extract_linguistic_features(text)
    f2 = extract_linguistic_features(text)

    assert f1 == f2
    assert f1["word_count"] == 21
    assert f1["sentence_count"] == 3
    assert f1["burstiness_score"] > 0.0
    assert 0.0 < f1["type_token_ratio"] <= 1.0
    assert f1["token_entropy"] > 0.0
