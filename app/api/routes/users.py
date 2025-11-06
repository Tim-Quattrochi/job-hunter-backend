"""User profile API endpoints.

Story 1.1: User Registration - Protected endpoints for user profile management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id, get_current_token_payload
from app.main import get_db
from app.services.profile_service import (
    get_or_create_profile,
    get_profile,
    ProfileNotFoundError,
)
from app.schemas.auth import UserProfileResponse, CurrentUserResponse


router = APIRouter(prefix="/api", tags=["Users"])


@router.get("/me", response_model=CurrentUserResponse)
async def get_current_user(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    token_payload: dict = Depends(get_current_token_payload),
):
    """Get the current authenticated user's profile.

    This endpoint implements lazy profile creation (Approach A from Story 1.1):
    - If user profile exists, return it
    - If user profile doesn't exist, create it with 10 free swipes

    This endpoint is protected and requires a valid JWT token in the Authorization header.

    Returns:
        CurrentUserResponse: User ID, email, and profile data (swipes, credits)

    Raises:
        401: If authentication fails
        500: If profile creation fails

    Example:
        ```bash
        curl -H "Authorization: Bearer <token>" http://localhost:8000/api/me
        ```
    """
    try:
        # Get or create profile (lazy creation with 10 free swipes)
        profile = await get_or_create_profile(db, user_id, create_if_missing=True)

        # Extract email from token payload
        email = token_payload.get("email")

        return CurrentUserResponse(
            user_id=user_id,
            email=email,
            profile=UserProfileResponse.model_validate(profile),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve or create profile: {str(e)}",
        )


@router.get("/users/{user_id}/profile", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """Get a user's profile by ID.

    This endpoint does NOT create profiles if they don't exist.
    Only returns existing profiles.

    Currently, users can only access their own profile (security check).

    Args:
        user_id: The user ID to fetch profile for

    Returns:
        UserProfileResponse: Profile data (swipes, credits, timestamps)

    Raises:
        401: If authentication fails
        403: If trying to access another user's profile
        404: If profile doesn't exist

    Example:
        ```bash
        curl -H "Authorization: Bearer <token>" \\
            http://localhost:8000/api/users/abc123/profile
        ```
    """
    # Security: Users can only access their own profile
    # TODO: In future, add admin role check to allow admins to view any profile
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own profile",
        )

    profile = await get_profile(db, user_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile not found for user_id: {user_id}",
        )

    return UserProfileResponse.model_validate(profile)
