"""Database health check endpoint for Story 0.3."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api", tags=["Health"])


def create_db_health_router(get_db_dependency) -> APIRouter:
    """Factory function to create database health router with database dependency.

    This factory pattern allows us to inject the database session dependency
    at runtime when the router is registered with the FastAPI app.

    Args:
        get_db_dependency: Callable that returns an AsyncSession dependency

    Returns:
        APIRouter: Configured router with database health endpoint
    """

    @router.get("/db-health")
    async def db_health_check(
        db: AsyncSession = Depends(get_db_dependency)
    ) -> dict[str, str]:
        """Check database connectivity and return current database name.

        This endpoint tests the database connection by executing a query
        to retrieve the current database name from PostgreSQL.

        Args:
            db: Database session (injected by FastAPI)

        Returns:
            dict: JSON with status and database name

        Raises:
            HTTPException: 503 error if database connection fails

        Example response:
            {"status": "connected", "database": "job_hunter_db"}
        """
        try:
            result = await db.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            return {"status": "connected", "database": db_name or "unknown"}
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Database connection failed: {str(e)}"
            )

    return router