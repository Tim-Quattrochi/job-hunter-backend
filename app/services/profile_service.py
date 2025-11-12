"""User profile service for managing user profiles with lazy creation.

Story 1.1: Implements Approach A (lazy profile creation).
Profiles are created automatically on first access, granting 10 free swipes.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import UserProfile


class ProfileNotFoundError(Exception):
    """Raised when a profile cannot be found and lazy creation is disabled."""

    pass


async def get_or_create_profile(
    db: AsyncSession, user_id: str, create_if_missing: bool = True
) -> UserProfile:
    """Get an existing profile or create a new one (lazy creation).

    This implements Approach A from Story 1.1: profiles are created
    automatically on first login when the user calls /api/me.

    New profiles are granted 10 free swipes on creation.

    Args:
        db: Database session
        user_id: Stack Auth user ID from JWT 'sub' claim
        create_if_missing: Whether to create profile if it doesn't exist (default: True)

    Returns:
        UserProfile: The existing or newly created profile

    Raises:
        ProfileNotFoundError: If profile doesn't exist and create_if_missing=False

    Example:
        ```python
        # In an endpoint with database dependency
        profile = await get_or_create_profile(db, user_id)
        return {"free_swipes": profile.free_swipes_remaining}
        ```
    """
    # Try to fetch existing profile
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    profile = result.scalar_one_or_none()

    if profile:
        return profile

    # Profile doesn't exist
    if not create_if_missing:
        raise ProfileNotFoundError(f"Profile not found for user_id: {user_id}")

    # Create new profile with 10 free swipes (Story 1.1 requirement)
    profile = UserProfile(
        user_id=user_id,
        free_swipes_remaining=10,
        paid_credits=0,
    )

    db.add(profile)
    
    try:
        await db.commit()
        await db.refresh(profile)
        return profile
    except IntegrityError:
        # Another request created the profile concurrently
        # Roll back and retry fetch
        await db.rollback()
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        profile = result.scalar_one_or_none()
        
        if profile:
            return profile
        
        # This should be extremely rare - profile was created and deleted
        raise ProfileNotFoundError(
            f"Profile creation failed due to race condition for user_id: {user_id}"
        )


async def get_profile(db: AsyncSession, user_id: str) -> UserProfile | None:
    """Get an existing profile without creating one.

    Use this when you want to check if a profile exists without
    triggering lazy creation.

    Args:
        db: Database session
        user_id: Stack Auth user ID

    Returns:
        UserProfile if found, None otherwise

    Example:
        ```python
        profile = await get_profile(db, user_id)
        if profile:
            print(f"User has {profile.total_swipes} swipes")
        else:
            print("Profile not yet created")
        ```
    """
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    return result.scalar_one_or_none()


async def update_swipes(
    db: AsyncSession, user_id: str, free_swipes_delta: int = 0, paid_credits_delta: int = 0
) -> UserProfile:
    """Update a user's swipe counts.

    Args:
        db: Database session
        user_id: Stack Auth user ID
        free_swipes_delta: Amount to add/subtract from free swipes (can be negative)
        paid_credits_delta: Amount to add/subtract from paid credits (can be negative)

    Returns:
        Updated UserProfile

    Raises:
        ProfileNotFoundError: If profile doesn't exist
        ValueError: If update would result in negative swipes

    Example:
        ```python
        # Consume one swipe
        profile = await update_swipes(db, user_id, free_swipes_delta=-1)

        # Add 50 paid credits
        profile = await update_swipes(db, user_id, paid_credits_delta=50)
        ```
    """
    profile = await get_profile(db, user_id)

    if not profile:
        raise ProfileNotFoundError(f"Profile not found for user_id: {user_id}")

    # Calculate new values
    new_free_swipes = profile.free_swipes_remaining + free_swipes_delta
    new_paid_credits = profile.paid_credits + paid_credits_delta

    # Validate non-negative constraint
    if new_free_swipes < 0:
        raise ValueError(
            f"Cannot update free_swipes: result would be negative ({new_free_swipes})"
        )

    if new_paid_credits < 0:
        raise ValueError(
            f"Cannot update paid_credits: result would be negative ({new_paid_credits})"
        )

    # Apply updates
    profile.free_swipes_remaining = new_free_swipes
    profile.paid_credits = new_paid_credits

    await db.commit()
    await db.refresh(profile)

    return profile


async def consume_swipe(db: AsyncSession, user_id: str) -> tuple[bool, UserProfile]:
    """Consume one swipe from the user's account (prioritizes free swipes).

    Args:
        db: Database session
        user_id: Stack Auth user ID

    Returns:
        Tuple of (success: bool, profile: UserProfile)
        - success is True if swipe was consumed, False if no swipes available

    Raises:
        ProfileNotFoundError: If profile doesn't exist

    Example:
        ```python
        success, profile = await consume_swipe(db, user_id)
        if success:
            print(f"Swipe consumed. Remaining: {profile.total_swipes}")
        else:
            print("No swipes available")
        ```
    """
    profile = await get_profile(db, user_id)

    if not profile:
        raise ProfileNotFoundError(f"Profile not found for user_id: {user_id}")

    # Try to consume a swipe using the model's method
    success = profile.consume_swipe()

    if success:
        await db.commit()
        await db.refresh(profile)

    return success, profile


async def add_paid_credits(db: AsyncSession, user_id: str, amount: int) -> UserProfile:
    """Add paid credits to a user's account.

    Args:
        db: Database session
        user_id: Stack Auth user ID
        amount: Number of credits to add (must be positive)

    Returns:
        Updated UserProfile

    Raises:
        ProfileNotFoundError: If profile doesn't exist
        ValueError: If amount is not positive

    Example:
        ```python
        # User purchases 100 credits
        profile = await add_paid_credits(db, user_id, 100)
        print(f"Total swipes: {profile.total_swipes}")
        ```
    """
    if amount <= 0:
        raise ValueError(f"Amount must be positive, got: {amount}")

    profile = await get_profile(db, user_id)

    if not profile:
        raise ProfileNotFoundError(f"Profile not found for user_id: {user_id}")

    profile.add_credits(amount)

    await db.commit()
    await db.refresh(profile)

    return profile
