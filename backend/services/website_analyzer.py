"""Website analyzer.

Fetches a homepage (and a few common marketing pages) with httpx -- NOT
Playwright -- so it stays fast (whole thing well under 10s). Extracts a light
text signal (title, meta description, h1-h3, leading body text) that the LLM
service turns into brand/competitor/prompt suggestions for onboarding.

Deliberately dependency-free parsing (regex + stdlib): good enough for the
"meaningful text" signal an LLM needs, and avoids pulling in BeautifulSoup.
"""

import re
import asyncio
import logging
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

import httpx

logger = logging.getLogger(__name__)

# Marketing pages worth a peek beyond the homepage. 404s are skipped silently.
COMMON_PATHS = ["/about", "/pricing", "/features", "/products"]
_USER_AGENT = "Mozilla/5.0 (compatible; AIScopeBot/1.0; +https://aiscope.app)"
_MAX_BODY_WORDS = 2000


class WebsiteUnreachableError(Exception):
    """Raised when the homepage itself cannot be fetched."""


@dataclass
class WebsiteAnalysis:
    url: str
    title: str = ""
    description: str = ""
    headings: list = field(default_factory=list)
    body_text: str = ""
    raw_pages: dict = field(default_factory=dict)


def normalize_url(url: str) -> str:
    """Accept example.com / www.example.com / https://example.com uniformly."""
    url = (url or "").strip()
    if not url:
        return ""
    if not re.match(r"^https?://", url, re.IGNORECASE):
        url = "https://" + url
    return url


def _strip_blocks(html: str) -> str:
    # Drop script/style/noscript blocks before any text extraction.
    return re.sub(
        r"<(script|style|noscript)[^>]*>.*?</\1>", " ", html, flags=re.IGNORECASE | re.DOTALL
    )


def _extract_title(html: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    return _clean(m.group(1)) if m else ""


def _extract_meta_description(html: str) -> str:
    # name="description" or property="og:description", attribute order-agnostic.
    for pattern in (
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']',
        r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+name=["\']description["\']',
        r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']*)["\']',
    ):
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            return _clean(m.group(1))
    return ""


def _extract_headings(html: str) -> list:
    headings = []
    for m in re.finditer(r"<h([1-3])[^>]*>(.*?)</h\1>", html, re.IGNORECASE | re.DOTALL):
        text = _clean(re.sub(r"<[^>]+>", " ", m.group(2)))
        if text and text not in headings:
            headings.append(text)
    return headings


def _strip_to_text(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", _strip_blocks(html))
    return _clean(text)


def _clean(text: str) -> str:
    # Unescape a few common entities and collapse whitespace.
    for entity, char in (("&amp;", "&"), ("&nbsp;", " "), ("&#39;", "'"), ("&quot;", '"'), ("&apos;", "'")):
        text = text.replace(entity, char)
    return re.sub(r"\s+", " ", text).strip()


async def _fetch(client: httpx.AsyncClient, url: str) -> str | None:
    try:
        resp = await client.get(url)
        if resp.status_code == 200 and "text/html" in resp.headers.get("content-type", "text/html"):
            return resp.text
    except Exception as e:
        logger.debug("website_analyzer: fetch failed for %s: %s", url, e)
    return None


async def analyze_website(url: str) -> WebsiteAnalysis:
    """Fetch homepage + common pages and extract a light text signal.

    Raises WebsiteUnreachableError if the homepage cannot be fetched.
    """
    url = normalize_url(url)
    if not url or not urlparse(url).netloc:
        raise WebsiteUnreachableError(f"Invalid URL: {url!r}")

    headers = {"User-Agent": _USER_AGENT, "Accept": "text/html"}
    # 8s per request keeps the whole analysis comfortably under 10s even with
    # the parallel secondary fetches.
    async with httpx.AsyncClient(
        timeout=8.0, follow_redirects=True, headers=headers
    ) as client:
        home = await _fetch(client, url)
        if home is None:
            raise WebsiteUnreachableError(f"Could not reach {url}")

        raw_pages = {"/": home}
        secondary = await asyncio.gather(
            *[_fetch(client, urljoin(url, path)) for path in COMMON_PATHS],
            return_exceptions=True,
        )
        for path, content in zip(COMMON_PATHS, secondary):
            if isinstance(content, str) and content:
                raw_pages[path] = content

    title = _extract_title(home)
    description = _extract_meta_description(home)

    headings: list = []
    for content in raw_pages.values():
        for h in _extract_headings(content):
            if h not in headings:
                headings.append(h)
    headings = headings[:40]

    # Body text: homepage first, then secondary pages, capped at ~2000 words.
    words: list = []
    for content in raw_pages.values():
        words.extend(_strip_to_text(content).split())
        if len(words) >= _MAX_BODY_WORDS:
            break
    body_text = " ".join(words[:_MAX_BODY_WORDS])

    return WebsiteAnalysis(
        url=url,
        title=title,
        description=description,
        headings=headings,
        body_text=body_text,
        raw_pages=raw_pages,
    )
