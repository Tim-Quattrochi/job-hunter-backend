"""Pydantic schemas for authentication-related data."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class TokenPayload(BaseModel):
    """JWT token payload from Stack Auth.

    Attributes:
        sub: Subject (user ID from Stack Auth)
        exp: Expiration timestamp
        iat: Issued at timestamp
        email: User's email address (if available)
    """

    sub: str = Field(..., description="User ID from Stack Auth")
    exp: int | None = Field(None, description="Token expiration timestamp")
    iat: int | None = Field(None, description="Token issued at timestamp")
    email: str | None = Field(None, description="User email address")

    class Config:
        """Pydantic config."""

        from_attributes = True


class UserProfileResponse(BaseModel):
    """User profile response model.

    Attributes:
        user_id: User ID from Stack Auth
        free_swipes_remaining: Number of free swipes remaining
        paid_credits: Number of paid credits
        created_at: Profile creation timestamp
        updated_at: Last update timestamp
    """

    user_id: str
    free_swipes_remaining: int
    paid_credits: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True

    @property
    def total_swipes(self) -> int:
        """Calculate total available swipes."""
        return self.free_swipes_remaining + self.paid_credits


class CurrentUserResponse(BaseModel):
    """Complete current user response including Stack Auth data and profile.

    Attributes:
        user_id: User ID from Stack Auth
        email: User email from JWT token
        profile: User profile data (swipes, credits)
    """

    user_id: str
    email: str | None = None
    profile: UserProfileResponse

    class Config:
        """Pydantic config."""

        from_attributes = True
