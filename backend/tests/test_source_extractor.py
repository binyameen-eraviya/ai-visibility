"""Source extractor unit tests (pure functions, no DB/LLM)."""

from backend.utils.enums import SourceType, UrlType, DomainClassifier
from backend.services.parsers import source_extractor as se


def test_domain_of_strips_www_and_lowercases():
    assert se.domain_of("https://www.Reddit.com/r/saas/abc") == "reddit.com"
    assert se.domain_of("http://EN.WIKIPEDIA.org/wiki/X") == "en.wikipedia.org"
    assert se.domain_of("not a url") == ""


def test_extract_urls_merges_cited_and_inline_dedup():
    raw = {
        "sources": ["https://g2.com/products/x", "https://reddit.com/r/saas"],
        "answer_text": "See https://reddit.com/r/saas and https://forbes.com/article.",
    }
    urls = se.extract_urls(raw)
    assert urls[0] == "https://g2.com/products/x"
    assert "https://reddit.com/r/saas" in urls
    assert "https://forbes.com/article" in urls
    # reddit cited + inline collapses to one entry
    assert urls.count("https://reddit.com/r/saas") == 1


def test_classify_known_list_and_suffixes():
    assert se.classify_known("reddit.com") == SourceType.UGC
    assert se.classify_known("en.wikipedia.org") == SourceType.REFERENCE
    assert se.classify_known("g2.com") == SourceType.REVIEW_SITE
    assert se.classify_known("techcrunch.com") == SourceType.EDITORIAL
    assert se.classify_known("data.gov") == SourceType.INSTITUTIONAL
    assert se.classify_known("mit.edu") == SourceType.INSTITUTIONAL
    assert se.classify_known("someunknownblog.xyz") is None


def test_classify_brand_match_corporate_and_competitor():
    # own domain -> CORPORATE
    assert se.classify_brand_match("acme.com", own_domain="acme.com") == SourceType.CORPORATE
    assert se.classify_brand_match("blog.acme.com", own_domain="www.acme.com") == SourceType.CORPORATE
    # competitor token matches a domain label -> COMPETITOR
    assert se.classify_brand_match("paypal.com", competitor_keys={"paypal"}) == SourceType.COMPETITOR
    assert se.classify_brand_match("random.com", competitor_keys={"paypal"}) is None


def test_classify_domain_tier_priority():
    # brand match beats known list
    stype, by = se.classify_domain("github.com", competitor_keys={"github"})
    assert stype == SourceType.COMPETITOR and by == DomainClassifier.BRAND_MATCH
    # known list when no brand match
    stype, by = se.classify_domain("github.com")
    assert stype == SourceType.REFERENCE and by == DomainClassifier.KNOWN_LIST
    # unknown -> needs LLM
    stype, by = se.classify_domain("weird-unknown-domain.io")
    assert stype is None and by is None
    # cache hit
    stype, by = se.classify_domain("weird-unknown-domain.io", cache={"weird-unknown-domain.io": SourceType.EDITORIAL})
    assert stype == SourceType.EDITORIAL


def test_classify_url_type_heuristics():
    assert se.classify_url_type("https://x.com/") == UrlType.HOMEPAGE
    assert se.classify_url_type("https://x.com/best-crm-tools-2026") == UrlType.LISTICLE
    assert se.classify_url_type("https://x.com/stripe-vs-paypal") == UrlType.COMPARISON
    assert se.classify_url_type("https://reddit.com/r/saas/comments/abc") == UrlType.DISCUSSION
    assert se.classify_url_type("https://x.com/blog/payments-101") == UrlType.ARTICLE
    assert se.classify_url_type("https://x.com/how-to-accept-payments") == UrlType.HOW_TO
    assert se.classify_url_type("https://x.com/pricing") == UrlType.PRODUCT_PAGE
    assert se.classify_url_type("https://x.com/something/random") == UrlType.OTHER


def test_build_sources_marks_unknowns_for_llm():
    raw = {"sources": ["https://reddit.com/r/x", "https://obscure-blog.io/post"], "answer_text": ""}
    sources = se.build_sources(raw, own_domain="acme.com", competitor_keys=set())
    by_domain = {s.domain: s for s in sources}
    assert by_domain["reddit.com"].source_type == SourceType.UGC
    assert by_domain["reddit.com"].position == 1
    # unknown stays unclassified for the LLM tier
    assert by_domain["obscure-blog.io"].source_type is None
    assert by_domain["obscure-blog.io"].classified_by is None


def test_parse_domain_classifications_maps_labels():
    out = se.parse_domain_classifications([
        {"domain": "Obscure-Blog.io", "type": "Editorial"},
        {"domain": "weird.com", "category": "Review Site"},
        {"domain": "huh.net", "type": "nonsense"},
    ])
    assert out["obscure-blog.io"] == SourceType.EDITORIAL
    assert out["weird.com"] == SourceType.REVIEW_SITE
    assert out["huh.net"] == SourceType.OTHER
