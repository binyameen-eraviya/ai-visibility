"""Mention detector unit tests (pure functions, no DB)."""

import uuid
from dataclasses import dataclass, field

from backend.services.parsers import mention_detector as md


@dataclass
class FakeBrand:
    name: str
    aliases: list = field(default_factory=list)
    is_primary: bool = False
    id: uuid.UUID = field(default_factory=uuid.uuid4)


def _by_name(results):
    return {r.brand_name: r for r in results}


def test_detects_brand_and_ranks_by_order():
    stripe = FakeBrand("Stripe")
    paypal = FakeBrand("PayPal")
    square = FakeBrand("Square")
    text = "For online payments, PayPal is popular, then Stripe, and Square too."
    results = md.detect_mentions(text, [stripe, paypal, square])
    r = _by_name(results)
    assert r["PayPal"].mentioned and r["PayPal"].position == 1
    assert r["Stripe"].mentioned and r["Stripe"].position == 2
    assert r["Square"].mentioned and r["Square"].position == 3


def test_whole_word_only_no_substring_match():
    stripe = FakeBrand("Stripe")
    # "Striped" must NOT count as a Stripe mention.
    results = md.detect_mentions("The shirt was striped and stripey.", [stripe])
    assert results[0].mentioned is False
    assert results[0].position is None


def test_case_insensitive_and_alias_match():
    brand = FakeBrand("Stripe", aliases=["stripe.com", "Stripe Inc"])
    results = md.detect_mentions("I used STRIPE.COM to accept cards.", [brand])
    assert results[0].mentioned is True


def test_unmentioned_brand_gets_false_row():
    a = FakeBrand("Acme")
    b = FakeBrand("Globex")
    results = md.detect_mentions("Acme is a great tool for teams.", [a, b])
    r = _by_name(results)
    assert r["Acme"].mentioned is True
    assert r["Globex"].mentioned is False
    # Every brand produces a row (needed for visibility = true / total).
    assert len(results) == 2


def test_context_snippet_is_the_sentence():
    brand = FakeBrand("Stripe")
    text = "Many options exist. Stripe is the developer favorite. Others lag."
    results = md.detect_mentions(text, [brand])
    assert "Stripe is the developer favorite" in results[0].context_snippet


def test_needs_llm_fallback_only_when_long_and_empty():
    brand = FakeBrand("Stripe")
    long_text = "x" * 200
    empty = md.detect_mentions(long_text, [brand])
    assert md.needs_llm_fallback(long_text, empty) is True
    # Short answer with no match -> not worth an LLM call.
    short = md.detect_mentions("nothing here", [brand])
    assert md.needs_llm_fallback("nothing here", short) is False
    # A match present -> never fall back.
    hit = md.detect_mentions("Stripe " + "x" * 200, [brand])
    assert md.needs_llm_fallback("Stripe " + "x" * 200, hit) is False


def test_parse_fuzzy_mentions_maps_llm_output():
    stripe = FakeBrand("Stripe")
    paypal = FakeBrand("PayPal")
    llm = [
        {"brand_name": "Stripe", "mentioned": True, "position": 1, "context_snippet": "the processor by Patrick Collison"},
        {"brand_name": "PayPal", "mentioned": False, "position": None, "context_snippet": None},
    ]
    results = md.parse_fuzzy_mentions(llm, [stripe, paypal])
    r = _by_name(results)
    assert r["Stripe"].mentioned is True and r["Stripe"].position == 1
    assert r["Stripe"].context_snippet.startswith("the processor")
    assert r["PayPal"].mentioned is False
