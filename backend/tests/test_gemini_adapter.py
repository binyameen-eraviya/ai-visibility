"""Gemini API adapter unit tests (pure parsing + error mapping, no network)."""

import httpx
import pytest

from backend.workers.scrapers.gemini_api import GeminiAPIAdapter
from backend.workers.scrapers.exceptions import RateLimited, ScraperError
from backend.workers.scrapers.registry import get_adapter


def test_registry_returns_gemini_adapter():
    adapter = get_adapter("gemini")
    assert isinstance(adapter, GeminiAPIAdapter)
    assert adapter.platform_name == "gemini"


def test_extract_text_joins_parts():
    body = {"candidates": [{"content": {"parts": [{"text": "Hello"}, {"text": "world"}]}}]}
    assert GeminiAPIAdapter._extract_text(body) == "Hello\nworld"


def test_extract_text_tolerates_empty():
    assert GeminiAPIAdapter._extract_text({}) == ""
    assert GeminiAPIAdapter._extract_text({"candidates": []}) == ""


def test_extract_sources_merges_grounding_and_inline_dedup():
    answer = "See https://g2.com/crm and https://reddit.com/r/saas for details."
    body = {
        "candidates": [{
            "groundingMetadata": {
                "groundingChunks": [
                    {"web": {"uri": "https://forbes.com/best-crm"}},
                    {"web": {"uri": "https://g2.com/crm"}},  # also inline -> dedup
                ]
            }
        }]
    }
    sources = GeminiAPIAdapter._extract_sources(answer, body)
    # Grounded URLs come first, then inline; g2 appears once.
    assert sources[0] == "https://forbes.com/best-crm"
    assert "https://reddit.com/r/saas" in sources
    assert sources.count("https://g2.com/crm") == 1


def test_raise_for_status_maps_errors():
    adapter = GeminiAPIAdapter()
    req = httpx.Request("POST", "https://example.test")

    # 200 -> no raise
    adapter._raise_for_status(httpx.Response(200, request=req))
    # 429 -> retryable
    with pytest.raises(RateLimited):
        adapter._raise_for_status(httpx.Response(429, request=req))
    # 400 / 500 -> permanent
    with pytest.raises(ScraperError):
        adapter._raise_for_status(httpx.Response(400, request=req))
    with pytest.raises(ScraperError):
        adapter._raise_for_status(httpx.Response(500, request=req))


async def test_run_prompt_without_key_raises(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "")
    adapter = GeminiAPIAdapter()
    with pytest.raises(ScraperError):
        await adapter.run_prompt("best crm software")
