"""Celery application configuration."""

from __future__ import annotations

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "job_hunter",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.task_routes = {
    "app.celery_app.test_task": {"queue": "celery"},
}


@celery_app.task(name="app.celery_app.test_task")
def test_task(message: str) -> str:
    """Simple task used to confirm the worker is processing jobs."""

    result = f"Worker received: {message}"
    print(result)  # Visible in worker logs for quick verification
    return result
