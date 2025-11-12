"""Database models for the Job Hunter application."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


# Import all models here for Alembic autogenerate to detect them
from .profile import UserProfile  # noqa: F401

__all__ = ["Base", "UserProfile"]
