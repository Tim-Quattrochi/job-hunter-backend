"""User profile model for storing additional user data beyond Stack Auth."""

from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import func

from app.models import Base


class UserProfile(Base):
    """User profile model that extends Stack Auth user data.

    This table stores application-specific user data, while Stack Auth
    handles the core authentication and user identity.

    Attributes:
        user_id: Primary key, references Stack Auth user ID (from JWT 'sub' claim)
        free_swipes_remaining: Number of free job application swipes remaining
        paid_credits: Number of paid credits purchased by user
        created_at: Timestamp when profile was created
        updated_at: Timestamp when profile was last updated
    """

    __tablename__ = "profiles"

    user_id = Column(
        String(255),
        primary_key=True,
        comment="Stack Auth user ID from JWT 'sub' claim",
    )
    free_swipes_remaining = Column(
        Integer,
        nullable=False,
        default=10,
        comment="Free job application swipes (10 granted on registration)",
    )
    paid_credits = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Paid credits purchased by user",
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Profile creation timestamp",
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last profile update timestamp",
    )

    def __repr__(self) -> str:
        """Return string representation of UserProfile."""
        return (
            f"<UserProfile(user_id='{self.user_id}', "
            f"free_swipes={self.free_swipes_remaining}, "
            f"paid_credits={self.paid_credits})>"
        )

    @property
    def total_swipes(self) -> int:
        """Calculate total available swipes (free + paid)."""
        return self.free_swipes_remaining + self.paid_credits

    def has_swipes(self) -> bool:
        """Check if user has any swipes remaining."""
        return self.total_swipes > 0

    def consume_swipe(self) -> bool:
        """Consume one swipe (prioritizes free swipes over paid credits).

        Returns:
            bool: True if swipe was consumed, False if no swipes available
        """
        if self.free_swipes_remaining > 0:
            self.free_swipes_remaining -= 1
            return True
        elif self.paid_credits > 0:
            self.paid_credits -= 1
            return True
        return False

    def add_credits(self, amount: int) -> None:
        """Add paid credits to user's account.

        Args:
            amount: Number of credits to add (must be positive)

        Raises:
            ValueError: If amount is not positive
        """
        if amount <= 0:
            raise ValueError("Credit amount must be positive")
        self.paid_credits += amount
