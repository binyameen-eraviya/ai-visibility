"""Sentiment parser unit tests (pure mapping/clamping, no LLM)."""

import uuid
from dataclasses import dataclass, field

from backend.services.parsers import sentiment_analyzer as sa


@dataclass
class FakeBrand:
    name: str
    aliases: list = field(default_factory=list)
    is_primary: bool = False
    id: uuid.UUID = field(default_factory=uuid.uuid4)


def _by_name(results):
    return {r.brand_name: r for r in results}


def test_parse_sentiment_maps_and_clamps():
    a = FakeBrand("Stripe")
    b = FakeBrand("PayPal")
    c = FakeBrand("Square")
    llm = [
        {"brand": "Stripe", "sentiment": 85, "reasoning": "strongly recommended"},
        {"brand": "PayPal", "sentiment": 150, "reasoning": "out of range -> clamp"},
        {"brand": "Square", "sentiment": None, "reasoning": "not mentioned"},
    ]
    r = _by_name(sa.parse_sentiment(llm, [a, b, c]))
    assert r["Stripe"].score == 85
    assert r["PayPal"].score == 100  # clamped
    assert r["Square"].score is None


def test_parse_sentiment_handles_floats_and_missing_brand():
    a = FakeBrand("Acme")
    b = FakeBrand("Globex")  # absent from LLM output
    llm = [{"brand": "Acme", "sentiment": 61.7}]
    r = _by_name(sa.parse_sentiment(llm, [a, b]))
    assert r["Acme"].score == 62  # rounded
    assert r["Globex"].score is None


def test_parse_sentiment_tolerates_empty():
    a = FakeBrand("Acme")
    r = sa.parse_sentiment(None, [a])
    assert len(r) == 1 and r[0].score is None
