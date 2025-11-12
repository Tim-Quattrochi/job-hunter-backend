"""FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.api.routes.db_health import create_db_health_router
from app.api.routes.auth_verify import create_auth_verify_router
from app.core.config import get_settings

settings = get_settings()

# Story 0.3: Database engine configuration
# Use asyncpg driver for PostgreSQL async operations (required for Neon DB)
# Remove query parameters and let asyncpg handle SSL automatically for Neon
database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
# Remove all query parameters - asyncpg will use SSL by default for cloud providers
database_url = database_url.split("?")[0]

engine = create_async_engine(
    database_url,
    echo=True,  # Log SQL queries (disable in production)
    future=True,
    pool_pre_ping=True,  # Verify connections before using them
    connect_args={"ssl": "require"},  # Explicitly require SSL for Neon DB
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """Dependency that provides a database session.

    Yields:
        AsyncSession: Database session

    Example usage in a route:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


app = FastAPI(title="Job Hunter API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Story 0.3: Include database health check router
db_health_router = create_db_health_router(get_db)
app.include_router(db_health_router)

# Story 0.3: Include Stack Auth verification router (test endpoint)
auth_verify_router = create_auth_verify_router()
app.include_router(auth_verify_router)

# Story 1.1: Include user profile routes
from app.api.routes.users import router as users_router
app.include_router(users_router)

@app.get("/", tags=["Health"])
async def read_root() -> dict[str, str]:
    """Return basic API metadata for quick diagnostics."""

    return {"name": "Job Hunter API", "version": app.version}


@app.get("/api/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Simple health-check endpoint used by infrastructure probes."""

    return {"status": "healthy"}


