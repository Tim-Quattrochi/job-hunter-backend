from __future__ import annotations

import pytest

from app.core import auth


class _DummySettings:
    stack_auth_project_id = "test-project"

    def __init__(self, ttl: int = 300):
        self.jwks_cache_ttl_seconds = ttl


def _dummy_settings(ttl: int = 300):
    return _DummySettings(ttl=ttl)


@pytest.fixture(autouse=True)
def clear_cache():
    auth.clear_jwks_cache()
    yield
    auth.clear_jwks_cache()


@pytest.mark.asyncio
async def test_fetch_jwks_reuses_cache(monkeypatch):
    calls = {"count": 0}

    async def fake_download(uri: str):
        calls["count"] += 1
        return {"keys": [{"kid": calls["count"]}]}

    monkeypatch.setattr(auth, "_download_jwks", fake_download)
    monkeypatch.setattr(auth, "get_settings", lambda: _dummy_settings(ttl=300))
    monkeypatch.setattr(auth, "get_jwks_uri", lambda: "https://example.com/jwks.json")

    first = await auth.fetch_jwks()
    second = await auth.fetch_jwks()

    assert calls["count"] == 1
    assert first is second


@pytest.mark.asyncio
async def test_fetch_jwks_force_refresh(monkeypatch):
    calls = {"count": 0}

    async def fake_download(uri: str):
        calls["count"] += 1
        return {"keys": [{"kid": calls["count"]}]}

    monkeypatch.setattr(auth, "_download_jwks", fake_download)
    monkeypatch.setattr(auth, "get_settings", lambda: _dummy_settings(ttl=300))
    monkeypatch.setattr(auth, "get_jwks_uri", lambda: "https://example.com/jwks.json")

    await auth.fetch_jwks()
    await auth.fetch_jwks(force_refresh=True)

    assert calls["count"] == 2


@pytest.mark.asyncio
async def test_fetch_jwks_respects_zero_ttl(monkeypatch):
    calls = {"count": 0}

    async def fake_download(uri: str):
        calls["count"] += 1
        return {"keys": [{"kid": calls["count"]}]}

    monkeypatch.setattr(auth, "_download_jwks", fake_download)
    monkeypatch.setattr(auth, "get_settings", lambda: _dummy_settings(ttl=0))
    monkeypatch.setattr(auth, "get_jwks_uri", lambda: "https://example.com/jwks.json")

    await auth.fetch_jwks()
    await auth.fetch_jwks()

    assert calls["count"] == 2
