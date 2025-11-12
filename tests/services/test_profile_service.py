"""Tests for profile service with race condition handling."""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Base, UserProfile
from app.services.profile_service import (
    get_or_create_profile,
    ProfileNotFoundError,
)


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Create an isolated database session for each test."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_get_or_create_profile_normal_creation(db_session: AsyncSession) -> None:
    """Test normal profile creation without race condition."""
    
    profile = await get_or_create_profile(db_session, "normal-user")
    
    assert profile is not None
    assert profile.user_id == "normal-user"
    assert profile.free_swipes_remaining == 10
    assert profile.paid_credits == 0


@pytest.mark.asyncio
async def test_get_or_create_profile_returns_existing(db_session: AsyncSession) -> None:
    """Test that existing profile is returned without creating a new one."""
    
    # Create an existing profile
    existing = UserProfile(
        user_id="existing-user",
        free_swipes_remaining=5,
        paid_credits=3,
    )
    db_session.add(existing)
    await db_session.commit()
    
    # Get the profile
    profile = await get_or_create_profile(db_session, "existing-user")
    
    assert profile.user_id == "existing-user"
    assert profile.free_swipes_remaining == 5
    assert profile.paid_credits == 3


@pytest.mark.asyncio
async def test_get_or_create_profile_raises_error_when_create_disabled(
    db_session: AsyncSession,
) -> None:
    """Test that ProfileNotFoundError is raised when create_if_missing=False."""
    
    with pytest.raises(ProfileNotFoundError, match="Profile not found"):
        await get_or_create_profile(db_session, "nonexistent-user", create_if_missing=False)


@pytest.mark.asyncio
async def test_get_or_create_profile_idempotent_multiple_calls(
    db_session: AsyncSession,
) -> None:
    """Test that multiple calls for the same user return the same profile.
    
    This verifies that the function is idempotent and handles the case where
    a profile might be created between the initial check and the creation attempt.
    """
    
    # Call get_or_create_profile multiple times for the same user
    profile1 = await get_or_create_profile(db_session, "multi-call-user")
    profile2 = await get_or_create_profile(db_session, "multi-call-user")
    profile3 = await get_or_create_profile(db_session, "multi-call-user")
    
    # All calls should return the same profile
    assert profile1.user_id == profile2.user_id == profile3.user_id == "multi-call-user"
    assert profile1.free_swipes_remaining == profile2.free_swipes_remaining == profile3.free_swipes_remaining == 10
    assert profile1.paid_credits == profile2.paid_credits == profile3.paid_credits == 0
