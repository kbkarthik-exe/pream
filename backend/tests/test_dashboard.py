import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_stats_unauthorized(client: AsyncClient):
    res = await client.get("/api/v1/dashboard/stats")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_stats_real_counts_zero_baseline(client: AsyncClient):
    # Register fresh user
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "stats_user@aicf.internal",
            "username": "stats_user",
            "password": "Password123!",
        },
    )
    cookie = reg.cookies

    # Stats must be exactly zero, never invented
    res = await client.get("/api/v1/dashboard/stats", cookies=cookie)
    assert res.status_code == 200
    data = res.json()
    assert data["total_reports"] == 0
    assert data["text_reports"] == 0
    assert data["image_reports"] == 0
    assert data["video_reports"] == 0
    assert data["audio_reports"] == 0
    assert data["active_sessions"] >= 1


@pytest.mark.asyncio
async def test_dashboard_stats_real_accumulation(client: AsyncClient):
    # Register User A
    user_a = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "accum_a@aicf.internal",
            "username": "accum_a",
            "password": "Password123!",
        },
    )
    cookie_a = user_a.cookies

    # Add 1 text report and 1 image report for User A
    await client.post(
        "/api/v1/reports",
        json={
            "title": "Text Analysis Case #1",
            "media_type": "text",
            "summary": "Sample text analysis findings.",
        },
        cookies=cookie_a,
    )
    await client.post(
        "/api/v1/reports",
        json={
            "title": "Image Forensics Case #2",
            "media_type": "image",
            "summary": "Sample image noise residuals.",
        },
        cookies=cookie_a,
    )

    stats_a = await client.get("/api/v1/dashboard/stats", cookies=cookie_a)
    assert stats_a.status_code == 200
    data_a = stats_a.json()
    assert data_a["total_reports"] == 2
    assert data_a["text_reports"] == 1
    assert data_a["image_reports"] == 1
    assert data_a["video_reports"] == 0
    assert data_a["audio_reports"] == 0

    # Register User B - User B must have 0 reports (isolated)
    user_b = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "accum_b@aicf.internal",
            "username": "accum_b",
            "password": "Password123!",
        },
    )
    cookie_b = user_b.cookies

    stats_b = await client.get("/api/v1/dashboard/stats", cookies=cookie_b)
    assert stats_b.status_code == 200
    data_b = stats_b.json()
    assert data_b["total_reports"] == 0
    assert data_b["text_reports"] == 0
    assert data_b["image_reports"] == 0


@pytest.mark.asyncio
async def test_profile_update(client: AsyncClient):
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "profile_user@aicf.internal",
            "username": "profile_user",
            "password": "Password123!",
        },
    )
    cookie = reg.cookies

    # Update full name
    res = await client.patch(
        "/api/v1/auth/profile",
        json={"full_name": "Chief Analyst Alan Turing"},
        cookies=cookie,
    )
    assert res.status_code == 200
    assert res.json()["full_name"] == "Chief Analyst Alan Turing"


@pytest.mark.asyncio
async def test_reports_filter_by_modality(client: AsyncClient):
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "filter_user@aicf.internal",
            "username": "filter_user",
            "password": "Password123!",
        },
    )
    cookie = reg.cookies

    # Create 1 audio and 1 video report
    await client.post(
        "/api/v1/reports",
        json={
            "title": "Audio Deepfake Case",
            "media_type": "audio",
            "summary": "Audio spectral traces",
        },
        cookies=cookie,
    )
    await client.post(
        "/api/v1/reports",
        json={
            "title": "Video Temporal Case",
            "media_type": "video",
            "summary": "Temporal facial boundary",
        },
        cookies=cookie,
    )

    # Filter by audio
    res_audio = await client.get("/api/v1/reports?media_type=audio", cookies=cookie)
    assert res_audio.status_code == 200
    items_audio = res_audio.json()
    assert len(items_audio) == 1
    assert items_audio[0]["media_type"] == "audio"

    # Filter by video
    res_video = await client.get("/api/v1/reports?media_type=video", cookies=cookie)
    assert res_video.status_code == 200
    items_video = res_video.json()
    assert len(items_video) == 1
    assert items_video[0]["media_type"] == "video"

    # Filter by text (none)
    res_text = await client.get("/api/v1/reports?media_type=text", cookies=cookie)
    assert res_text.status_code == 200
    assert len(res_text.json()) == 0

