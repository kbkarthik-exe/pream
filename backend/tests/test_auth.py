from datetime import UTC, datetime, timedelta

import pytest
from backend.app.core.config import settings
from backend.app.core.security import hash_session_token
from backend.app.models.session import UserSession
from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    payload = {
        "email": "analyst.doe@forensics.aicf.internal",
        "username": "analyst_doe",
        "password": "SecurePassword123!",
        "full_name": "Analyst Jane Doe",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["username"] == payload["username"]
    assert "hashed_password" not in data
    assert settings.COOKIE_NAME in response.cookies


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    payload = {
        "email": "duplicate@aicf.internal",
        "username": "user_one",
        "password": "Password123!",
    }
    r1 = await client.post("/api/v1/auth/register", json=payload)
    assert r1.status_code == 201

    payload2 = {
        "email": "duplicate@aicf.internal",
        "username": "user_two",
        "password": "Password123!",
    }
    r2 = await client.post("/api/v1/auth/register", json=payload2)
    assert r2.status_code == 409
    assert "email address already exists" in r2.json()["detail"]


@pytest.mark.asyncio
async def test_register_weak_password_validation(client: AsyncClient):
    # Missing uppercase and special characters / digits
    payload = {
        "email": "weak@aicf.internal",
        "username": "weak_user",
        "password": "short",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_rate_limiting(client: AsyncClient):
    # Attempt more than max allowed registrations in window
    for i in range(settings.RATE_LIMIT_REGISTER_MAX):
        res = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"rate_{i}@aicf.internal",
                "username": f"rate_user_{i}",
                "password": "SecurePassword123!",
            },
        )
        assert res.status_code == 201

    # Next attempt must trigger 429
    res_limited = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "rate_over@aicf.internal",
            "username": "rate_user_over",
            "password": "SecurePassword123!",
        },
    )
    assert res_limited.status_code == 429
    assert "Retry-After" in res_limited.headers
    assert "Rate limit exceeded" in res_limited.json()["detail"]


@pytest.mark.asyncio
async def test_login_success_and_me(client: AsyncClient):
    # Register first
    reg_payload = {
        "email": "agent@aicf.internal",
        "username": "agent_alpha",
        "password": "AlphaPassword99!",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)

    # Login with username
    login_payload = {
        "identifier": "agent_alpha",
        "password": "AlphaPassword99!",
    }
    login_res = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    assert settings.COOKIE_NAME in login_res.cookies

    # Get /me with cookie
    me_res = await client.get("/api/v1/auth/me", cookies=login_res.cookies)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["username"] == "agent_alpha"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    reg_payload = {
        "email": "valid@aicf.internal",
        "username": "valid_user",
        "password": "ValidPassword123!",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)

    # Wrong password
    res = await client.post(
        "/api/v1/auth/login",
        json={"identifier": "valid_user", "password": "WrongPassword!"},
    )
    assert res.status_code == 401
    assert "Invalid email/username or password" in res.json()["detail"]

    # Non-existent user
    res_non_existent = await client.post(
        "/api/v1/auth/login",
        json={"identifier": "ghost_user", "password": "ValidPassword123!"},
    )
    assert res_non_existent.status_code == 401


@pytest.mark.asyncio
async def test_logout_invalidates_session(client: AsyncClient):
    reg_payload = {
        "email": "logout@aicf.internal",
        "username": "logout_user",
        "password": "ValidPassword123!",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    session_cookie = reg_res.cookies

    # Profile succeeds with active session
    me_before = await client.get("/api/v1/auth/me", cookies=session_cookie)
    assert me_before.status_code == 200

    # Logout
    logout_res = await client.post("/api/v1/auth/logout", cookies=session_cookie)
    assert logout_res.status_code == 200

    # Profile fails after logout
    me_after = await client.get("/api/v1/auth/me", cookies=session_cookie)
    assert me_after.status_code == 401


@pytest.mark.asyncio
async def test_expired_session_fails(client: AsyncClient, db_session: AsyncSession):
    reg_payload = {
        "email": "expired@aicf.internal",
        "username": "expired_user",
        "password": "ValidPassword123!",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    cookie_token = reg_res.cookies.get(settings.COOKIE_NAME)
    assert cookie_token is not None

    # Manually expire the session in the test DB
    token_hash = hash_session_token(cookie_token)
    stmt_select = select(UserSession).where(UserSession.token_hash == token_hash)
    session_record = (await db_session.execute(stmt_select)).scalars().first()
    assert session_record is not None

    past_date = datetime.now(UTC) - timedelta(hours=2)
    stmt_update = (
        update(UserSession).where(UserSession.token_hash == token_hash).values(expires_at=past_date)
    )
    await db_session.execute(stmt_update)
    await db_session.commit()

    # Accessing /me with expired token returns 401
    res = await client.get("/api/v1/auth/me", cookies={settings.COOKIE_NAME: cookie_token})
    assert res.status_code == 401
    assert "expired" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_user_cannot_access_another_user_private_report(client: AsyncClient):
    # Register User A
    user_a_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user.a@aicf.internal",
            "username": "analyst_a",
            "password": "PasswordA123!",
        },
    )
    cookie_a = user_a_res.cookies

    # User A creates a private investigation report
    create_report_res = await client.post(
        "/api/v1/reports",
        json={
            "title": "Suspected Synthetic Audio Deepfake #402",
            "media_type": "audio",
            "summary": "Phase alignment traces detect pitch vocoder artifacts.",
            "is_private": True,
        },
        cookies=cookie_a,
    )
    assert create_report_res.status_code == 201
    report_id = create_report_res.json()["id"]

    # User A can access their own report
    get_a = await client.get(f"/api/v1/reports/{report_id}", cookies=cookie_a)
    assert get_a.status_code == 200
    assert get_a.json()["id"] == report_id

    # Register User B
    user_b_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user.b@aicf.internal",
            "username": "analyst_b",
            "password": "PasswordB123!",
        },
    )
    cookie_b = user_b_res.cookies

    # User B attempts to access User A's private report -> must fail with 403 Forbidden
    get_b = await client.get(f"/api/v1/reports/{report_id}", cookies=cookie_b)
    assert get_b.status_code == 403
    assert "cannot access another user's private" in get_b.json()["detail"]
