"""Onboarding analyze/detect-location: LLM coercion + endpoint shape."""

import pytest

from backend.services.llm_service import _coerce, BrandSuggestions
from backend.services.website_analyzer import WebsiteAnalysis


def test_coerce_parses_v2_fields():
    data = {
        "brand_name": "Stripe",
        "brand_aliases": ["stripe"],
        "brand_description": "Payments infrastructure for the internet.",
        "industry": "FinTech",
        "brand_identity": ["Reliable", "Developer-focused", "  "],
        "products_services": ["Payment Processing", "Stripe Billing"],
        "competitors": [
            {"name": "PayPal", "domain": "https://www.PayPal.com/checkout", "reason": "Direct competitor"},
            "Adyen",  # bare string tolerated
        ],
        "suggested_topics": ["Online Payments", "Subscription Billing"],
        "suggested_prompts": [
            {"topic": "Online Payments", "text": "Best payment gateway for ecommerce?"},
            "alternatives to Stripe",  # bare string tolerated
        ],
    }
    s = _coerce(data, BrandSuggestions())
    assert s.brand_description.startswith("Payments")
    assert s.brand_identity == ["Reliable", "Developer-focused"]  # blank dropped
    assert s.products_services == ["Payment Processing", "Stripe Billing"]
    # competitor domain normalized to bare host
    paypal = next(c for c in s.competitors if c["name"] == "PayPal")
    assert paypal["domain"] == "paypal.com"
    adyen = next(c for c in s.competitors if c["name"] == "Adyen")
    assert adyen["domain"] == ""
    assert s.suggested_topics == ["Online Payments", "Subscription Billing"]
    # prompts coerced to {topic, text}
    assert {"topic": "Online Payments", "text": "Best payment gateway for ecommerce?"} in s.suggested_prompts
    assert {"topic": "", "text": "alternatives to Stripe"} in s.suggested_prompts


class _FakeLLM:
    async def analyze_brand(self, website_data):
        return BrandSuggestions(
            brand_name="Stripe",
            brand_aliases=["stripe"],
            brand_description="Payments infra.",
            industry="FinTech",
            brand_identity=["Reliable", "Scalable"],
            products_services=["Payment Processing"],
            competitors=[{"name": "PayPal", "domain": "paypal.com", "reason": "competitor"}],
            suggested_topics=["Online Payments", "Security"],
            suggested_prompts=[{"topic": "Online Payments", "text": "Best gateway?"}],
        )


async def _fake_analyze_website(url):
    return WebsiteAnalysis(url=url, title="Stripe")


async def test_analyze_website_endpoint_returns_v2_shape(client, auth_headers, monkeypatch):
    from backend.interactors.project import analyze_website as interactor
    monkeypatch.setattr(interactor, "analyze_website", _fake_analyze_website)
    monkeypatch.setattr(interactor, "GeminiLLMService", lambda: _FakeLLM())

    resp = await client.post("/api/analyze-website", headers=auth_headers, json={"url": "stripe.com"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["brand_name"] == "Stripe"
    assert body["brand_description"] == "Payments infra."
    assert body["brand_identity"] == ["Reliable", "Scalable"]
    assert body["products_services"] == ["Payment Processing"]
    assert body["competitors"][0]["domain"] == "paypal.com"
    assert body["suggested_topics"] == ["Online Payments", "Security"]
    assert body["suggested_prompts"][0] == {"topic": "Online Payments", "text": "Best gateway?"}
    assert body["favicon_url"] == "https://www.google.com/s2/favicons?domain=stripe.com&sz=64"


async def test_detect_location_returns_structure(client, auth_headers):
    # Test client IP is loopback/private -> nulls, but 200 + shape.
    resp = await client.get("/api/detect-location", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert set(body.keys()) == {"ip", "country_code", "country_name"}
    assert body["country_code"] is None  # private/loopback test client


async def test_detect_location_requires_auth(client):
    resp = await client.get("/api/detect-location")
    assert resp.status_code == 401
