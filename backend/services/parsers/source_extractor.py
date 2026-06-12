"""Source extraction + classification.

From a raw scrape capture we get a list of cited URLs (and may find more inline
in the answer text). For each we want:
  - the domain (reddit.com from https://www.reddit.com/r/saas/...)
  - a domain type (UGC / Reference / Editorial / Review site / Corporate /
    Competitor / Institutional / Other)
  - a url type (Listicle / Article / Homepage / ... ) from the path + title

Classification is tiered so the LLM is the last resort:
  Tier 1  brand match   -- domain belongs to the client (CORPORATE) or a tracked
                           competitor (COMPETITOR). Most specific, so checked first.
  Tier 2  known list    -- a static table of ~60 well-known domains + .gov/.edu rules.
  Tier 3  LLM           -- unknown domains are batched into the orchestrator's
                           single Gemini call; results are cached in
                           domain_classifications so we never re-ask.

This module is pure: it returns "needs LLM" signals and prompt fragments rather
than calling the LLM itself.
"""

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from backend.utils.enums import SourceType, UrlType, DomainClassifier

# Matches http(s) URLs embedded in answer prose. Trailing punctuation trimmed below.
_URL_RE = re.compile(r"https?://[^\s<>\")\]]+", re.IGNORECASE)
_TRAILING = ".,;:!?)]}'\"’”"

# Well-known domains -> SourceType. Keys are bare registrable domains; a host
# matches a key when it equals it or is a subdomain of it (en.wikipedia.org ->
# wikipedia.org). Reddit folds into UGC per the metric spec.
KNOWN_DOMAINS = {
    # UGC / social / community
    "reddit.com": SourceType.UGC,
    "linkedin.com": SourceType.UGC,
    "youtube.com": SourceType.UGC,
    "twitter.com": SourceType.UGC,
    "x.com": SourceType.UGC,
    "quora.com": SourceType.UGC,
    "medium.com": SourceType.UGC,
    "facebook.com": SourceType.UGC,
    "instagram.com": SourceType.UGC,
    "tiktok.com": SourceType.UGC,
    "substack.com": SourceType.UGC,
    "producthunt.com": SourceType.UGC,
    "news.ycombinator.com": SourceType.UGC,
    "ycombinator.com": SourceType.UGC,
    "pinterest.com": SourceType.UGC,
    "threads.net": SourceType.UGC,
    "discord.com": SourceType.UGC,
    "slack.com": SourceType.UGC,
    # Reference / docs / knowledge
    "arxiv.org": SourceType.REFERENCE,
    "wikipedia.org": SourceType.REFERENCE,
    "github.com": SourceType.REFERENCE,
    "gitlab.com": SourceType.REFERENCE,
    "bitbucket.org": SourceType.REFERENCE,
    "stackoverflow.com": SourceType.REFERENCE,
    "stackexchange.com": SourceType.REFERENCE,
    "developer.mozilla.org": SourceType.REFERENCE,
    "mozilla.org": SourceType.REFERENCE,
    "w3.org": SourceType.REFERENCE,
    "npmjs.com": SourceType.REFERENCE,
    "readthedocs.io": SourceType.REFERENCE,
    "wikihow.com": SourceType.REFERENCE,
    "scholar.google.com": SourceType.REFERENCE,
    "researchgate.net": SourceType.REFERENCE,
    "semanticscholar.org": SourceType.REFERENCE,
    # Review sites / analyst
    "g2.com": SourceType.REVIEW_SITE,
    "capterra.com": SourceType.REVIEW_SITE,
    "trustpilot.com": SourceType.REVIEW_SITE,
    "trustradius.com": SourceType.REVIEW_SITE,
    "getapp.com": SourceType.REVIEW_SITE,
    "softwareadvice.com": SourceType.REVIEW_SITE,
    "gartner.com": SourceType.REVIEW_SITE,
    "yelp.com": SourceType.REVIEW_SITE,
    "glassdoor.com": SourceType.REVIEW_SITE,
    "crozdesk.com": SourceType.REVIEW_SITE,
    "sourceforge.net": SourceType.REVIEW_SITE,
    # Editorial / press
    "techcrunch.com": SourceType.EDITORIAL,
    "forbes.com": SourceType.EDITORIAL,
    "wired.com": SourceType.EDITORIAL,
    "theverge.com": SourceType.EDITORIAL,
    "businessinsider.com": SourceType.EDITORIAL,
    "bloomberg.com": SourceType.EDITORIAL,
    "reuters.com": SourceType.EDITORIAL,
    "nytimes.com": SourceType.EDITORIAL,
    "wsj.com": SourceType.EDITORIAL,
    "cnbc.com": SourceType.EDITORIAL,
    "venturebeat.com": SourceType.EDITORIAL,
    "engadget.com": SourceType.EDITORIAL,
    "mashable.com": SourceType.EDITORIAL,
    "zdnet.com": SourceType.EDITORIAL,
    "cnet.com": SourceType.EDITORIAL,
    "arstechnica.com": SourceType.EDITORIAL,
    "thenextweb.com": SourceType.EDITORIAL,
    "fastcompany.com": SourceType.EDITORIAL,
    "inc.com": SourceType.EDITORIAL,
    "entrepreneur.com": SourceType.EDITORIAL,
    "theguardian.com": SourceType.EDITORIAL,
    "hbr.org": SourceType.EDITORIAL,
    # Institutional
    "who.int": SourceType.INSTITUTIONAL,
    "un.org": SourceType.INSTITUTIONAL,
    "europa.eu": SourceType.INSTITUTIONAL,
    "worldbank.org": SourceType.INSTITUTIONAL,
    "imf.org": SourceType.INSTITUTIONAL,
    "iso.org": SourceType.INSTITUTIONAL,
    "ieee.org": SourceType.INSTITUTIONAL,
    "nist.gov": SourceType.INSTITUTIONAL,
    "nih.gov": SourceType.INSTITUTIONAL,
    "nasa.gov": SourceType.INSTITUTIONAL,
}

# Path/title cues for url_type. Order matters: earlier wins.
_LISTICLE_RE = re.compile(r"(best-|top-|/best\b|/top\b|\d+-best|\d+-top|listicle|roundup)", re.I)
_COMPARISON_RE = re.compile(r"(\bvs\b|-vs-|/vs/|compare|comparison|alternative)", re.I)
_HOWTO_RE = re.compile(r"(how-to|how_to|/guide|tutorial|/docs?/|/learn|getting-started)", re.I)
_DISCUSSION_RE = re.compile(r"(/r/|/comments/|/thread|/forum|/community|/discussion|/questions?/)", re.I)
_ARTICLE_RE = re.compile(r"(/blog/|/article|/news/|/post/|/posts/|/insights/|/stories/)", re.I)
_PRODUCT_RE = re.compile(r"(/pricing|/product|/products|/features|/solutions|/plans)", re.I)


@dataclass
class ExtractedSource:
    url: str
    domain: str
    position: int
    source_type: SourceType = None          # None until classified
    url_type: UrlType = UrlType.OTHER
    classified_by: DomainClassifier = None  # provenance, None => needs LLM


def domain_of(url: str) -> str:
    """Bare host for a URL, lowercased, www. stripped. '' if unparseable."""
    try:
        host = (urlparse(url).hostname or "").lower()
    except Exception:
        return ""
    if host.startswith("www."):
        host = host[4:]
    return host


def extract_urls(raw_data: dict) -> list:
    """Cited URLs from the capture's `sources` plus any inline in answer_text.

    De-duplicated, order preserved (cited first, then inline).
    """
    urls = []
    seen = set()

    def _add(u):
        u = (u or "").strip().rstrip(_TRAILING)
        if u and u.lower().startswith(("http://", "https://")) and u not in seen:
            seen.add(u)
            urls.append(u)

    for u in (raw_data.get("sources") or []):
        if isinstance(u, str):
            _add(u)
        elif isinstance(u, dict):  # some adapters may store {url, title}
            _add(u.get("url"))

    for m in _URL_RE.finditer(raw_data.get("answer_text") or ""):
        _add(m.group(0))

    return urls


def classify_known(domain: str):
    """Tier 2: known-list / suffix classification. Returns SourceType or None."""
    if not domain:
        return None
    # .gov / .edu / .mil and academic ccTLDs are institutional regardless of host.
    if re.search(r"(\.gov|\.edu|\.mil)(\.[a-z]{2})?$", domain) or re.search(r"\.ac\.[a-z]{2}$", domain):
        return SourceType.INSTITUTIONAL
    for key, stype in KNOWN_DOMAINS.items():
        if domain == key or domain.endswith("." + key):
            return stype
    return None


def _labels(domain: str) -> set:
    return set(domain.split(".")) if domain else set()


def classify_brand_match(domain: str, own_domain: str = None, competitor_keys=None):
    """Tier 1: does this domain belong to a tracked brand?

    own_domain    -- the client's project website host (-> CORPORATE).
    competitor_keys -- normalized competitor name tokens (-> COMPETITOR) matched
                       against the domain's labels.
    Returns SourceType or None.
    """
    if not domain:
        return None
    if own_domain:
        own = own_domain.lower()
        if own.startswith("www."):
            own = own[4:]
        if own and (domain == own or domain.endswith("." + own) or own.endswith("." + domain)):
            return SourceType.CORPORATE
    if competitor_keys:
        labels = _labels(domain)
        for key in competitor_keys:
            if key and key in labels:
                return SourceType.COMPETITOR
    return None


def classify_domain(domain: str, *, own_domain=None, competitor_keys=None, cache=None):
    """Full tiered domain classification (no LLM).

    Returns (SourceType, DomainClassifier) when resolved, or (None, None) when
    the domain is unknown and must go to the LLM. `cache` is an optional
    {domain: SourceType} of previously-classified domains.
    """
    if cache and domain in cache:
        return cache[domain], DomainClassifier.KNOWN_LIST

    brand = classify_brand_match(domain, own_domain, competitor_keys)
    if brand is not None:
        return brand, DomainClassifier.BRAND_MATCH

    known = classify_known(domain)
    if known is not None:
        return known, DomainClassifier.KNOWN_LIST

    return None, None


def classify_url_type(url: str, title: str = None) -> UrlType:
    """Heuristic page-type from the URL path (+ optional page title)."""
    try:
        parsed = urlparse(url)
    except Exception:
        return UrlType.OTHER
    path = (parsed.path or "").lower()
    hay = f"{path} {(title or '').lower()}"

    if not path or path == "/":
        return UrlType.HOMEPAGE
    if _COMPARISON_RE.search(hay):
        return UrlType.COMPARISON
    if _LISTICLE_RE.search(hay):
        return UrlType.LISTICLE
    if _DISCUSSION_RE.search(path):
        return UrlType.DISCUSSION
    if _HOWTO_RE.search(hay):
        return UrlType.HOW_TO
    if _ARTICLE_RE.search(path):
        return UrlType.ARTICLE
    if _PRODUCT_RE.search(path):
        return UrlType.PRODUCT_PAGE
    return UrlType.OTHER


def build_sources(raw_data: dict, *, own_domain=None, competitor_keys=None, cache=None) -> list:
    """Extract + best-effort-classify every cited URL (no LLM).

    Sources whose domain couldn't be resolved keep source_type=None /
    classified_by=None so the orchestrator can batch them to the LLM.
    """
    sources = []
    for pos, url in enumerate(extract_urls(raw_data), start=1):
        domain = domain_of(url)
        stype, by = classify_domain(
            domain, own_domain=own_domain, competitor_keys=competitor_keys, cache=cache,
        )
        sources.append(ExtractedSource(
            url=url,
            domain=domain,
            position=pos,
            source_type=stype,
            url_type=classify_url_type(url),
            classified_by=by,
        ))
    return sources


# --- LLM tier (batched by the orchestrator) ---------------------------------

_TYPE_BY_LABEL = {
    "corporate": SourceType.CORPORATE,
    "ugc": SourceType.UGC,
    "reference": SourceType.REFERENCE,
    "editorial": SourceType.EDITORIAL,
    "review site": SourceType.REVIEW_SITE,
    "review_site": SourceType.REVIEW_SITE,
    "reviewsite": SourceType.REVIEW_SITE,
    "institutional": SourceType.INSTITUTIONAL,
    "competitor": SourceType.COMPETITOR,
    "other": SourceType.OTHER,
}


def build_domain_prompt_fragment(domains: list) -> str:
    """Instruction block for the batched LLM call's domain-classification section."""
    listed = ", ".join(domains)
    return (
        "DOMAINS: Classify each of these domains into exactly one of: Corporate, "
        "UGC, Reference, Editorial, Review Site, Institutional, Other.\n"
        f"Domains: {listed}"
    )


def parse_domain_classifications(llm_domains) -> dict:
    """Map the LLM's domain output to {domain: SourceType}.

    Accepts items like {"domain": "x.com", "type": "Editorial"} (or "category").
    Unrecognized types fall back to OTHER.
    """
    out = {}
    for d in llm_domains or []:
        if not isinstance(d, dict):
            continue
        domain = d.get("domain") or d.get("name")
        label = (d.get("type") or d.get("category") or d.get("domain_type") or "").strip().lower()
        if domain:
            out[str(domain).strip().lower()] = _TYPE_BY_LABEL.get(label, SourceType.OTHER)
    return out
