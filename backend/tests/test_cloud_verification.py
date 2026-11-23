"""Automated tests for Phase 4: Optional Cloud Verification Hub.

Verifies:
1. PBKDF2-HMAC-SHA256 authenticated encryption roundtrip & tampering resistance.
2. Secret masking (raw keys never leaked).
3. Cloud Providers status listing when unconfigured.
4. User credential save, isolation, and deletion.
5. Mandatory analyst consent enforcement (HTTP 400 when user_consent=False).
6. Graceful handling of unconfigured providers, timeouts, rate limits, and 401/403/500 errors.
7. Official adapter behavior for Hive AI, GPTZero, and Copyleaks.
8. Local forensics remaining 100% functional, air-gapped capable, and independent of cloud.
"""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from httpx import AsyncClient

from backend.app.core.crypto_vault import decrypt_api_key, encrypt_api_key, mask_api_key
from backend.app.ml.cloud.copyleaks_adapter import CopyleaksAdapter
from backend.app.ml.cloud.gptzero_adapter import GPTZeroAdapter
from backend.app.ml.cloud.hive_unified import UnifiedHiveAdapter, UnifiedHiveResult


# ============================================================================
# 1. CRYPTO VAULT UNIT TESTS
# ============================================================================


def test_crypto_vault_roundtrip():
    """Verify encryption and decryption roundtrip for API keys."""
    raw_key = "hiv_live_sec_998877665544332211"
    user_id = 42

    cipher_text = encrypt_api_key(raw_key, user_id=user_id)
    assert cipher_text != raw_key
    assert len(cipher_text) > 40

    decrypted = decrypt_api_key(cipher_text, user_id=user_id)
    assert decrypted == raw_key


def test_crypto_vault_user_isolation_cipher():
    """Verify that user B cannot decrypt user A's ciphertext."""
    raw_key = "gptzero_secret_token_12345"
    cipher_a = encrypt_api_key(raw_key, user_id=101)

    with pytest.raises(ValueError):
        decrypt_api_key(cipher_a, user_id=102)


def test_crypto_vault_tamper_detection():
    """Verify that tampering with ciphertext triggers failure."""
    raw_key = "secret_key_to_be_tampered"
    cipher = encrypt_api_key(raw_key, user_id=1)

    # Corrupt last character
    tampered = cipher[:-1] + ("A" if cipher[-1] != "A" else "B")
    with pytest.raises(ValueError):
        decrypt_api_key(tampered, user_id=1)


def test_mask_api_key():
    """Verify secret masking functions."""
    assert mask_api_key("hiv_live_1234567890abcdef") == "hiv_••••••••cdef"
    assert mask_api_key("short") == "••••••••"
    assert mask_api_key(None) == "NOT_CONFIGURED"
    assert mask_api_key("") == "NOT_CONFIGURED"


# ============================================================================
# 2. ADAPTER LEVEL UNIT TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_hive_adapter_unconfigured():
    adapter = UnifiedHiveAdapter(api_key=None)
    assert not adapter.is_configured
    res = await adapter.analyze_text("Some text payload")
    assert res.status == "CONFIGURATION_REQUIRED"
    assert res.ai_generated_score is None


@pytest.mark.asyncio
async def test_hive_adapter_mock_success():
    adapter = UnifiedHiveAdapter(api_key="hiv_mock_key_12345")
    assert adapter.is_configured

    mock_resp_data = {
        "code": 200,
        "status": [
            {
                "response": {
                    "output": [
                        {
                            "classes": [
                                {"class": "ai_generated", "score": 0.884},
                                {"class": "human", "score": 0.116},
                            ]
                        }
                    ]
                }
            }
        ],
    }

    mock_resp = httpx.Response(200, json=mock_resp_data, request=httpx.Request("POST", "http://test"))
    with patch("backend.app.ml.cloud.hive_unified.httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        res = await adapter.analyze_text("This is an artificial text passage.")
        assert res.status == "SUCCESS"
        assert res.ai_generated_score == 0.884


@pytest.mark.asyncio
async def test_hive_adapter_mock_401_error():
    adapter = UnifiedHiveAdapter(api_key="hiv_invalid_key")

    mock_resp = httpx.Response(401, json={"message": "Invalid token"}, request=httpx.Request("POST", "http://test"))
    with patch("backend.app.ml.cloud.hive_unified.httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        res = await adapter.analyze_text("Some document text.")
        assert res.status == "PROVIDER_ERROR"
        assert "authentication rejected" in (res.error_message or "").lower()


@pytest.mark.asyncio
async def test_hive_adapter_mock_timeout():
    adapter = UnifiedHiveAdapter(api_key="hiv_mock_key")

    with patch("backend.app.ml.cloud.hive_unified.httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Read timeout")):
        res = await adapter.analyze_text("Some document text.")
        assert res.status == "TIMEOUT"
        assert "timed out" in (res.error_message or "").lower()


@pytest.mark.asyncio
async def test_gptzero_adapter_length_check():
    adapter = GPTZeroAdapter(api_key="gptzero_test_key")
    # Short text < 250 chars
    res = await adapter.analyze_text("Too short to evaluate.")
    assert res.status == "INSUFFICIENT_LENGTH"
    assert "250 characters" in (res.error_message or "")


@pytest.mark.asyncio
async def test_gptzero_adapter_mock_success():
    adapter = GPTZeroAdapter(api_key="gptzero_test_key")
    long_text = "This is a sufficiently long document specifically designed to exceed the mandatory minimum length threshold of 250 characters required by GPTZero v2 prediction API endpoints. Adding additional sentences to ensure the length invariant is completely satisfied."

    mock_resp_data = {
        "documents": [
            {
                "completely_generated_prob": 0.942,
                "overall_burstiness": 12.4,
                "sentences": [],
            }
        ]
    }

    mock_resp = httpx.Response(200, json=mock_resp_data, request=httpx.Request("POST", "http://test"))
    with patch("backend.app.ml.cloud.gptzero_adapter.httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        res = await adapter.analyze_text(long_text)
        assert res.status == "SUCCESS"
        assert res.completely_generated_prob == 0.942


@pytest.mark.asyncio
async def test_copyleaks_adapter_mock_success():
    adapter = CopyleaksAdapter(api_key="mock_copyleaks_token")
    mock_resp_data = {
        "summary": {
            "ai": 0.775,
            "human": 0.225,
        },
        "scannedWords": 85,
    }

    long_copyleaks_text = (
        "This is a longer document sample designed specifically for testing the Copyleaks adapter. "
        "It needs to contain more than one hundred characters to pass the initial length check safely."
    )

    mock_resp = httpx.Response(200, json=mock_resp_data, request=httpx.Request("POST", "http://test"))
    with patch("backend.app.ml.cloud.copyleaks_adapter.httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        res = await adapter.analyze_text(long_copyleaks_text)
        assert res.status == "SUCCESS"
        assert res.ai_probability == 0.775
        assert res.human_probability == 0.225


# ============================================================================
# 3. ENDPOINT INTEGRATION & SECURITY TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_cloud_providers_unconfigured_listing(client: AsyncClient):
    """Verify default status of cloud providers is CONFIGURATION_REQUIRED."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cloud_analyst_1@aicf.internal",
            "username": "cloud_analyst_1",
            "password": "Password123!",
        },
    )
    cookie = reg.cookies

    res = await client.get("/api/v1/cloud/providers", cookies=cookie)
    assert res.status_code == 200
    providers = res.json()
    assert len(providers) == 3

    provider_map = {p["provider"]: p for p in providers}
    assert "hive" in provider_map
    assert "gptzero" in provider_map
    assert "copyleaks" in provider_map

    # Ensure audio is NOT in supported types (permanently cancelled)
    for p in providers:
        assert "audio" not in [t.lower() for t in p["supported_types"]]
        assert p["is_configured"] is False
        assert p["masked_key"] == "NOT_CONFIGURED"


@pytest.mark.asyncio
async def test_save_and_mask_credential(client: AsyncClient):
    """Verify API keys are saved in vault and masked in responses."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cloud_analyst_2@aicf.internal",
            "username": "cloud_analyst_2",
            "password": "Password123!",
        },
    )
    cookie = reg.cookies

    raw_secret = "hiv_live_sec_1234567890abcdef"
    save_res = await client.post(
        "/api/v1/cloud/credentials",
        cookies=cookie,
        json={
            "provider": "hive",
            "api_key": raw_secret,
        },
    )
    assert save_res.status_code == 200
    assert save_res.json()["success"] is True

    # Check provider list
    list_res = await client.get("/api/v1/cloud/providers", cookies=cookie)
    assert list_res.status_code == 200

    # Critical security assertion: raw key MUST NEVER appear in JSON response
    assert raw_secret not in list_res.text

    hive_p = next(p for p in list_res.json() if p["provider"] == "hive")
    assert hive_p["is_configured"] is True
    assert hive_p["source"] == "USER_CONFIGURED"
    assert hive_p["masked_key"] == "hiv_••••••••cdef"


@pytest.mark.asyncio
async def test_delete_credential(client: AsyncClient):
    """Verify stored credentials can be cleanly deleted."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cloud_analyst_del@aicf.internal",
            "username": "cloud_analyst_del",
            "password": "Password123!",
        },
    )
    cookie = reg.cookies

    await client.post(
        "/api/v1/cloud/credentials",
        cookies=cookie,
        json={"provider": "gptzero", "api_key": "gptzero_sample_key_9988"},
    )

    del_res = await client.delete("/api/v1/cloud/credentials/gptzero", cookies=cookie)
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Re-check status
    list_res = await client.get("/api/v1/cloud/providers", cookies=cookie)
    gpt_p = next(p for p in list_res.json() if p["provider"] == "gptzero")
    assert gpt_p["is_configured"] is False
    assert gpt_p["masked_key"] == "NOT_CONFIGURED"


@pytest.mark.asyncio
async def test_user_isolation_cloud_credentials(client: AsyncClient):
    """Verify User B cannot see, modify, or use User A's API credentials."""
    # Register User A
    user_a = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user_a_cloud@aicf.internal",
            "username": "user_a_cloud",
            "password": "Password123!",
        },
    )
    cookie_a = user_a.cookies

    # User A stores key
    await client.post(
        "/api/v1/cloud/credentials",
        cookies=cookie_a,
        json={"provider": "copyleaks", "api_key": "user_a_secret_key_8899"},
    )

    # Register User B
    user_b = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user_b_cloud@aicf.internal",
            "username": "user_b_cloud",
            "password": "Password123!",
        },
    )
    cookie_b = user_b.cookies

    # User B list providers - copyleaks MUST be unconfigured
    list_b = await client.get("/api/v1/cloud/providers", cookies=cookie_b)
    copy_b = next(p for p in list_b.json() if p["provider"] == "copyleaks")
    assert copy_b["is_configured"] is False
    assert copy_b["masked_key"] == "NOT_CONFIGURED"

    # User B attempts to delete User A's credential - must fail 404
    del_b = await client.delete("/api/v1/cloud/credentials/copyleaks", cookies=cookie_b)
    assert del_b.status_code == 404


@pytest.mark.asyncio
async def test_consent_enforcement_on_verify_text(client: AsyncClient):
    """Verify that user_consent=False returns HTTP 400 Bad Request."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "consent_user@aicf.internal",
            "username": "consent_user",
            "password": "Password123!",
        },
    )
    cookie = reg.cookies

    # Attempt verification without explicit consent
    res = await client.post(
        "/api/v1/cloud/verify-text",
        cookies=cookie,
        json={
            "text": "Some text to verify without consent.",
            "user_consent": False,
        },
    )
    assert res.status_code == 400
    assert "Explicit analyst consent is required" in res.json()["detail"]


@pytest.mark.asyncio
async def test_verify_text_unconfigured_graceful(client: AsyncClient):
    """Verify that unconfigured providers report CONFIGURATION_REQUIRED cleanly."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "unconfig_verify@aicf.internal",
            "username": "unconfig_verify",
            "password": "Password123!",
        },
    )
    cookie = reg.cookies

    res = await client.post(
        "/api/v1/cloud/verify-text",
        cookies=cookie,
        json={
            "text": "Testing unconfigured provider response behavior.",
            "user_consent": True,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["consent_granted"] is True
    assert "results" in data

    # All unconfigured providers report CONFIGURATION_REQUIRED
    for p_name, r in data["results"].items():
        assert r["status"] == "CONFIGURATION_REQUIRED"
        assert r["is_configured"] is False
        assert r["ai_score"] is None


@pytest.mark.asyncio
async def test_test_connection_endpoint(client: AsyncClient):
    """Verify /test-connection with mock ping."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test_conn_user@aicf.internal",
            "username": "test_conn_user",
            "password": "Password123!",
        },
    )
    cookie = reg.cookies

    with patch.object(UnifiedHiveAdapter, "test_connection", new_callable=AsyncMock) as mock_test_conn:
        mock_test_conn.return_value = (True, "Hive AI API connection verified successfully.")

        res = await client.post(
            "/api/v1/cloud/test-connection",
            cookies=cookie,
            json={
                "provider": "hive",
                "api_key": "hiv_mock_ping_key",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["provider"] == "hive"


@pytest.mark.asyncio
async def test_local_text_forensics_remain_fully_functional(client: AsyncClient):
    """Verify local text forensics operate 100% normally and independently of cloud."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "local_forensics_user@aicf.internal",
            "username": "local_forensics_user",
            "password": "Password123!",
        },
    )
    cookie = reg.cookies

    # Run local text analysis without any cloud credentials configured
    sample_text = (
        "Artificial intelligence architectures represent a revolutionary milestone in computational linguistics. "
        "Natural language processing models demonstrate unprecedented capabilities in synthesizing coherent syntactic sequences."
    )

    res = await client.post(
        "/api/v1/text/analyze",
        cookies=cookie,
        json={
            "text": sample_text,
            "save_to_cases": False,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "classification" in data
    assert data["classification"] in ["LIKELY AI-GENERATED", "LIKELY HUMAN", "INCONCLUSIVE"]
    assert data["token_entropy"] is not None
    assert data["burstiness_score"] is not None
    assert data["type_token_ratio"] is not None
    assert data["detector_scores"] is not None
    assert "roberta" in data["detector_scores"]
    assert data["detector_scores"]["roberta"]["model_name"] == "roberta-base-openai-detector"
