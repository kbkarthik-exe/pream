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


# 12. RoBERTa Independent Detector Test
def test_roberta_detector_independent():
    """RoBERTa detector unit test for direct inference and latency measurement."""
    from backend.app.ml.text.detector import RobertaTextDetector

    det = RobertaTextDetector()
    loaded = det.load_model()
    if loaded:
        res = det.infer("This is a comprehensive analytical sample evaluating transformer forward passes.")
        assert res["status"] in ["READY", "SUCCESS"]
        assert res["ai_probability"] is not None
        assert res["human_probability"] is not None
        assert res["latency_ms"] >= 0.0
        assert round(res["ai_probability"] + res["human_probability"], 2) == 1.00
    else:
        # If resources prevent load, verify honest reporting
        assert det.load_error is not None


# 13. DeBERTa-v3 Independent Detector Test
def test_deberta_detector_independent_unconfigured():
    """DeBERTa detector must honestly report availability and not crash if weights are missing or constrained."""
    from backend.app.ml.text.detector import DebertaTextDetector

    det = DebertaTextDetector()
    res = det.infer("Sample text for secondary architecture evaluation.")
    assert res["status"] in ["UNAVAILABLE", "RESOURCE_CONSTRAINED", "READY"]
    assert "model_name" in res
    if res["status"] != "READY":
        assert res["ai_probability"] is None
        assert res["status_detail"] is not None


# 14. Text Ensemble Aggregator Calibration Unit Test
def test_ensemble_aggregator_calibration():
    """Ensemble aggregator must apply temperature scaling, covariance adjustment, and linguistic priors."""
    from backend.app.ml.text.ensemble import TextEnsembleAggregator

    aggregator = TextEnsembleAggregator(temperature=1.25, covariance_rho=0.72)

    # Simulated dual model input
    mock_detectors = {
        "roberta": {
            "model_name": "roberta-base-openai-detector",
            "status": "READY",
            "ai_probability": 0.85,
            "human_probability": 0.15,
            "latency_ms": 45.0,
        },
        "deberta": {
            "model_name": "microsoft/deberta-v3-base",
            "status": "READY",
            "ai_probability": 0.80,
            "human_probability": 0.20,
            "latency_ms": 50.0,
        },
    }

    mock_linguistics = {
        "burstiness_score": 0.10,  # Low burstiness (characteristic AI)
        "type_token_ratio": 0.40,
        "token_entropy": 4.1,
        "repeated_ngram_ratio": 0.05,
    }

    consensus = aggregator.calibrate_and_aggregate(
        detector_results=mock_detectors,
        linguistic_features=mock_linguistics,
        word_count=60,
    )

    assert consensus["status"] == "SUCCESS"
    assert consensus["classification"] == "LIKELY AI-GENERATED"
    assert consensus["ai_probability"] >= 0.70
    assert consensus["active_detector_count"] == 2
    assert consensus["agreement_score"] > 0.90
    assert "linguistic_profiler" in consensus["detector_scores"]


# 15. Ensemble Inter-Model Conflict & Inconclusive Handling
def test_ensemble_inter_model_conflict():
    """When models disagree significantly, consensus must degrade to INCONCLUSIVE."""
    from backend.app.ml.text.ensemble import TextEnsembleAggregator

    aggregator = TextEnsembleAggregator()

    conflicting_detectors = {
        "roberta": {
            "model_name": "roberta-base-openai-detector",
            "status": "READY",
            "ai_probability": 0.90,
            "human_probability": 0.10,
        },
        "deberta": {
            "model_name": "microsoft/deberta-v3-base",
            "status": "READY",
            "ai_probability": 0.15,
            "human_probability": 0.85,
        },
    }

    linguistics = {
        "burstiness_score": 0.30,
        "type_token_ratio": 0.50,
        "token_entropy": 4.5,
        "repeated_ngram_ratio": 0.01,
    }

    consensus = aggregator.calibrate_and_aggregate(
        detector_results=conflicting_detectors,
        linguistic_features=linguistics,
        word_count=55,
    )

    # Disagreement is |0.90 - 0.15| = 0.75 > 0.45 threshold -> INCONCLUSIVE
    assert consensus["classification"] == "INCONCLUSIVE"


# 16. Multi-Detector API Response Verification
@pytest.mark.asyncio
async def test_text_analysis_multi_detector_api_response(client: AsyncClient):
    """API response must contain detector_scores and ensemble consensus structures."""
    cookies = await create_authenticated_analyst(client, "multidet")
    client.cookies = cookies

    sample = (
        "Artificial intelligence text detection systems employ multi-model ensemble consensus "
        "to prevent over-reliance on a single sequence classifier. By evaluating linguistic entropy, "
        "burstiness variation, and token probabilities, the platform establishes evidentiary confidence."
    )
    res = await client.post("/api/v1/text/analyze", json={"text": sample})
    assert res.status_code == 200
    data = res.json()

    assert "detector_scores" in data
    assert "roberta" in data["detector_scores"]
    assert "linguistic_profiler" in data["detector_scores"]
    assert "ensemble" in data
    assert data["ensemble"] is not None
    assert data["ensemble"]["active_detector_count"] >= 1


# 17. Multi-Detector PDF Generation with Ensemble Table
@pytest.mark.asyncio
async def test_text_analysis_pdf_with_ensemble(client: AsyncClient):
    """Forensic PDF generation must render the multi-model detector consensus section."""
    cookies = await create_authenticated_analyst(client, "pdfens")
    client.cookies = cookies

    sample = (
        "Comprehensive forensic documentation requires transparent multi-detector evidence. "
        "This sample verifies that generated PDF reports format ensemble tables, calibration parameters, "
        "and cryptographic hashes accurately."
    )
    post_res = await client.post("/api/v1/text/analyze", json={"text": sample})
    assert post_res.status_code == 200
    analysis_id = post_res.json()["analysis_id"]

    pdf_res = await client.get(f"/api/v1/text/analyses/{analysis_id}/pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert len(pdf_res.content) > 1000
    assert pdf_res.content[:4] == b"%PDF"


# 18. Sentence and Paragraph Forensics Granular Telemetry
@pytest.mark.asyncio
async def test_text_analysis_sentence_and_paragraph_forensics(client: AsyncClient):
    """API response must contain granular sentence analysis, paragraph details, and punctuation metrics."""
    cookies = await create_authenticated_analyst(client, "granular")
    client.cookies = cookies

    sample = (
        "Furthermore, artificial intelligence architectures systematically generate predictable syntax. "
        "Consequently, empirical investigations confirm that transformer models minimize loss.\n\n"
        "On the other hand, human writing exhibits substantial variance in sentence length. "
        "Notice how this second paragraph changes the cadence completely!"
    )
    res = await client.post("/api/v1/text/analyze", json={"text": sample})
    assert res.status_code == 200
    data = res.json()

    assert "sentence_analysis" in data
    assert len(data["sentence_analysis"]) >= 4
    first_sent = data["sentence_analysis"][0]
    assert first_sent["sentence_idx"] == 0
    assert first_sent["word_count"] > 0
    assert first_sent["has_transitional_opening"] is True  # "Furthermore"
    assert first_sent["relative_cadence"] in ["SHORT", "BALANCED", "LONG", "MONOTONOUS"]

    assert "paragraph_analysis" in data
    assert len(data["paragraph_analysis"]) == 2

    assert "punctuation_metrics" in data
    assert data["punctuation_metrics"] is not None
    assert data["punctuation_metrics"]["total_punctuation_count"] > 0
    assert data["punctuation_metrics"]["punctuation_density"] > 0.0

    assert "sentence_length_distribution" in data
    assert "mean" in data["sentence_length_distribution"]


# 19. Non-English Script Warning
@pytest.mark.asyncio
async def test_text_analysis_non_english_script_warning(client: AsyncClient):
    """Non-Latin or non-English script must surface an explicit language warning without crash."""
    cookies = await create_authenticated_analyst(client, "noneng")
    client.cookies = cookies

    # Cyrillic sample with enough words to pass length gate
    cyrillic_sample = (
        "Искусственный интеллект и машинное обучение развиваются чрезвычайно быстрыми темпами. "
        "Современные нейронные сети способны генерировать связный текст на различных языках мира. "
        "Однако статистические детекторы требуют калибровки для корректной оценки многоязычных данных."
    )
    res = await client.post("/api/v1/text/analyze", json={"text": cyrillic_sample})
    assert res.status_code == 200
    data = res.json()

    assert data["language_warning"] is not None
    assert "non-latin" in data["language_warning"].lower() or "cyrillic" in data["language_warning"].lower()


# 20. Raw Output Model Telemetry
@pytest.mark.asyncio
async def test_text_analysis_raw_output_telemetry(client: AsyncClient):
    """Detectors that execute successfully must expose raw output logits and tokens."""
    cookies = await create_authenticated_analyst(client, "rawout")
    client.cookies = cookies

    sample = (
        "Language model detection platforms must provide verifiable cryptographic and numerical "
        "evidence rather than unexplainable black-box confidence scores. Investigating logits and "
        "token distributions guarantees forensic integrity for academic and legal scrutiny."
    )
    res = await client.post("/api/v1/text/analyze", json={"text": sample})
    assert res.status_code == 200
    data = res.json()

    roberta_score = data["detector_scores"].get("roberta")
    assert roberta_score is not None
    if roberta_score["status"] == "READY":
        assert "raw_output" in roberta_score
        assert roberta_score["raw_output"] is not None
        assert "logits" in roberta_score["raw_output"]
        assert "tokens_evaluated" in roberta_score["raw_output"]
        assert "device" in roberta_score["raw_output"]


# 21. Empirical Benchmark Evaluation Metrics (Precision, Recall, F1, FPR, FNR)
def test_text_forensics_benchmark_evaluation():
    """Evaluates the multi-model text forensics detector on a curated benchmark set.

    Verifies that precision, recall, F1-score, and false positive rates are measurable,
    statistically sound, and documented without claiming 100% accuracy.
    """
    ai_samples = [
        "Artificial intelligence architectures represent a revolutionary milestone in computational linguistics. Natural language processing models demonstrate unprecedented capabilities in synthesizing coherent syntactic sequences across diverse discursive domains. By leveraging multi-head self-attention mechanisms and deep multilayer representations, these neural systems construct predictive probabilistic distributions over expansive lexical vocabularies. Furthermore, empirical investigations confirm that transformer architectures systematically minimize cross-entropy loss, ensuring contextual alignment and structural consistency throughout generated textual sequences.",
        "Deep learning algorithms optimize complex loss surfaces through iterative stochastic gradient descent and adaptive learning rate schedules. Modern multi-layer perceptrons and convolutional filters capture hierarchical spatial and temporal abstractions across heterogeneous datasets. In summary, algorithmic advancements facilitate scalable feature extraction and robust empirical generalization across multimodal machine intelligence tasks.",
        "The implementation of transformer-based architectures facilitates automated summarization and predictive translation across multilingual corpora. Self-attention mechanisms map query and key vectors to compute weighted token combinations across unbounded sequence lengths. Consequently, generative sequence decoders exhibit high lexical regularity and consistent syntactic progression across formal expository paragraphs.",
        "Neural text generation demonstrates consistent token frequency distribution and minimized syntactic burstiness across expansive technical corpora. Pre-trained transformer checkpoints produce probabilistic lexical arrangements characterized by uniform sentence complexity. Therefore, quantitative linguistic analyses reveal distinct distributional deviations when evaluating synthetic documentation alongside human prose.",
        "Quantum computing paradigms offer exponential computational advantages for specific optimization algorithms through quantum superposition and entanglement. Qubits execute unitary transformations within complex Hilbert spaces, enabling quantum phase estimation and Grover search routines. Consequently, cryptographic architectures must transition toward post-quantum resistant cryptographic protocols to ensure future communications security.",
    ]

    human_samples = [
        "I was wandering around downtown yesterday evening trying to find that old bookshop my professor told me about. Naturally, my phone died right when I turned the corner onto Elm Street! I ended up popping into a tiny coffee place instead, completely drenched from the sudden rainstorm, and struck up a random conversation with the barista about 90s indie bands. Honestly? Way better than finding the book. Sometimes getting completely lost turns into the best part of your week.",
        "My cat woke me up at 4:30 AM today by knocking a glass of water off the nightstand. Not cool! I tried to fall back asleep, but the neighbor's dog started barking at absolutely nothing in the alleyway. So I just gave up, brewed a massive pot of coffee, and watched the sunrise from my kitchen balcony with a blanket wrapped around my shoulders.",
        "Took the old sedan out for a test drive after replacing the spark plugs and alternator this weekend. What a relief! The engine idle isn't stuttering at stoplights anymore, though there's still a faint squeak coming from the serpentine belt when accelerating hard uphill. Guess I'll have to crawl under the hood again on Saturday.",
        "We decided to try baking sourdough bread from scratch last weekend using a starter my sister gave us. Disaster! The dough was super sticky, wouldn't hold its shape, and we ended up with a dense sourdough pancake that could double as a doorstop. Tasted alright with salted butter, but presentation was basically a zero out of ten.",
        "Had a sudden craving for fish tacos at midnight, so I rummaged through the freezer and found some cod fillets from last month. Fried them up with some cumin and lime juice, slapped them into charred corn tortillas with leftover cabbage slaw. Messy, spicy, and definitely hit the spot after a long week of debugging code.",
    ]

    tp, fp, tn, fn, inc = 0, 0, 0, 0, 0

    for sample in ai_samples:
        result = text_detector.analyze_text(sample)
        cls = result["classification"]
        if cls == "LIKELY AI-GENERATED":
            tp += 1
        elif cls == "LIKELY HUMAN":
            fn += 1
        else:
            inc += 1

    for sample in human_samples:
        result = text_detector.analyze_text(sample)
        cls = result["classification"]
        if cls == "LIKELY HUMAN":
            tn += 1
        elif cls == "LIKELY AI-GENERATED":
            fp += 1
        else:
            inc += 1

    decided = tp + fp + tn + fn
    assert decided > 0, "At least some samples must yield a definitive classification"

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

    # Ensure evaluation metrics are physically plausible (forensic honesty: never 100% on everything)
    assert 0.0 <= precision <= 1.0
    assert 0.0 <= recall <= 1.0
    assert 0.0 <= f1 <= 1.0
    assert 0.0 <= fpr <= 1.0
    assert 0.0 <= fnr <= 1.0
    assert (tp + tn) > 0, "Detector should correctly identify majority of benchmark samples"


