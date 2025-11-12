"""Tests for the `/api/me` endpoint's lazy profile creation contract."""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.auth import get_current_token_payload, get_current_user_id
from app.main import app, get_db
from app.models import Base, UserProfile

TEST_USER_ID = "stack-user-123"
TEST_EMAIL = "mock-user@example.com"


@pytest_asyncio.fixture
async def test_app() -> tuple:
    """Create an isolated FastAPI app + database for each test."""

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db() -> AsyncSession:
        async with session_factory() as session:
            yield session

    async def override_get_current_user_id() -> str:
        return TEST_USER_ID

    async def override_get_current_token_payload() -> dict:
        return {"sub": TEST_USER_ID, "email": TEST_EMAIL}

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id
    app.dependency_overrides[get_current_token_payload] = (
        override_get_current_token_payload
    )

    try:
        yield app, session_factory
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()
@pytest.mark.asyncio
async def test_lazy_profile_creation_creates_profile_when_missing(test_app: tuple) -> None:
    """Calling `/api/me` should create a profile when one does not exist."""

    app_instance, session_factory = test_app

    transport = ASGITransport(app=app_instance)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/me", headers={"Authorization": "Bearer test"})

    assert response.status_code == 200
    data = response.json()

    assert data["user_id"] == TEST_USER_ID
    assert data["email"] == TEST_EMAIL
    assert data["profile"]["free_swipes_remaining"] == 10
    assert data["profile"]["paid_credits"] == 0

    async with session_factory() as session:
        result = await session.execute(
            select(UserProfile).where(UserProfile.user_id == TEST_USER_ID)
        )
        profile = result.scalar_one_or_none()

        assert profile is not None, "Profile should be created lazily"
        assert profile.free_swipes_remaining == 10
        assert profile.paid_credits == 0


@pytest.mark.asyncio
async def test_lazy_profile_creation_returns_existing_profile(test_app: tuple) -> None:
    """Calling `/api/me` should return an existing profile without modifying it."""

    app_instance, session_factory = test_app

    async with session_factory() as session:
        session.add(
            UserProfile(
                user_id=TEST_USER_ID,
                free_swipes_remaining=4,
                paid_credits=2,
            )
        )
        await session.commit()

    transport = ASGITransport(app=app_instance)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/me", headers={"Authorization": "Bearer test"})

    assert response.status_code == 200
    data = response.json()

    assert data["profile"]["free_swipes_remaining"] == 4
    assert data["profile"]["paid_credits"] == 2

    async with session_factory() as session:
        result = await session.execute(
            select(UserProfile).where(UserProfile.user_id == TEST_USER_ID)
        )
        profile = result.scalar_one()

        assert profile.free_swipes_remaining == 4
        assert profile.paid_credits == 2
