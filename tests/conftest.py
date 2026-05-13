"""
Test fixtures. Force BM25 scoring in tests to avoid OpenAI calls.
"""

import pytest
from app import orchestrator
from app.config import settings


@pytest.fixture(autouse=True)
def _force_bm25(monkeypatch):
    monkeypatch.setattr(settings, "scoring_mode", "bm25")
    monkeypatch.setattr(settings, "openai_api_key", "")
    orchestrator.cache_clear()
    yield
    orchestrator.cache_clear()
