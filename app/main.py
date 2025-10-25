"""FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title="Job Hunter API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
async def read_root() -> dict[str, str]:
    """Return basic API metadata for quick diagnostics."""

    return {"name": "Job Hunter API", "version": app.version}


@app.get("/api/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Simple health-check endpoint used by infrastructure probes."""

    return {"status": "healthy"}
