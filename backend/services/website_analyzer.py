"""Website analyzer.

Fetches a homepage (and a few common marketing pages) with httpx -- NOT
Playwright -- so it stays fast (whole thing well under 10s). Extracts a light
text signal (title, meta description, h1-h3, leading body text) that the LLM
service turns into brand/competitor/prompt suggestions for onboarding.

SSRF hardening: the URL is user-supplied, so before every fetch we resolve the
host and reject any non-global address (loopback, link-local incl. the cloud
metadata IP, RFC1918, ULA, etc.), pin the connection to the validated IP so a
DNS rebind can't swap it, forbid credentials/odd schemes, and follow redirects
manually -- re-validating each hop -- instead of letting httpx chase them.

Deliberately dependency-free HTML parsing (regex + stdlib).
"""

import re
import socket
import asyncio
import logging
import ipaddress
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

import httpx

logger = logging.getLogger(__name__)

# Marketing pages worth a peek beyond the homepage. 404s are skipped silently.
COMMON_PATHS = ["/about", "/pricing", "/features", "/products"]
_USER_AGENT = "Mozilla/5.0 (compatible; AIScopeBot/1.0; +https://aiscope.app)"
_MAX_BODY_WORDS = 2000
_ALLOWED_SCHEMES = {"http", "https"}
_MAX_REDIRECTS = 3


class WebsiteUnreachableError(Exception):
    """Raised when the homepage cannot be fetched."""


class BlockedURLError(WebsiteUnreachableError):
    """The URL targets a non-public/disallowed address (SSRF guard).

    Subclasses WebsiteUnreachableError so callers map it to the same "couldn't
    reach that website" response -- we deliberately don't reveal to the client
    that an internal address was blocked.
    """


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


def _resolve_and_validate(url: str) -> tuple[str, str]:
    """Validate a URL and resolve it to a single public IP to pin against.

    Returns (hostname, pinned_ip). Raises BlockedURLError if the scheme isn't
    http(s), credentials are present, the host can't be resolved, or ANY
    resolved address is non-global.
    """
    parsed = urlparse(url)
    scheme = (parsed.scheme or "").lower()
    if scheme not in _ALLOWED_SCHEMES:
        raise BlockedURLError(f"Unsupported scheme: {scheme!r}")
    if "@" in (parsed.netloc or ""):
        raise BlockedURLError("Credentials in URL are not allowed")

    host = parsed.hostname
    if not host:
        raise BlockedURLError("Missing hostname")

    try:
        port = parsed.port or (443 if scheme == "https" else 80)
    except ValueError:
        raise BlockedURLError("Invalid port")

    try:
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise BlockedURLError(f"Could not resolve {host}")

    ips = sorted({info[4][0] for info in infos})
    if not ips:
        raise BlockedURLError(f"Could not resolve {host}")

    for ip in ips:
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            raise BlockedURLError(f"Unparseable address for {host}: {ip}")
        # is_global is False for loopback, link-local (169.254.169.254),
        # RFC1918, ULA, 0.0.0.0/8, CGNAT, and other non-routable ranges.
        if not addr.is_global:
            raise BlockedURLError(f"Host {host} resolves to a non-public address")

    return host, ips[0]


async def _safe_get(client: httpx.AsyncClient, url: str) -> str | None:
    """SSRF-guarded GET with manual, re-validated redirects.

    Returns HTML text on a 200 text/html response, else None. Raises
    BlockedURLError if a (current or redirected-to) URL targets a non-public
    address -- the homepage caller lets this surface; secondary-page callers
    swallow it.
    """
    current = url
    for _ in range(_MAX_REDIRECTS + 1):
        # Resolve + validate off the event loop (getaddrinfo is blocking).
        host, ip = await asyncio.to_thread(_resolve_and_validate, current)
        parsed = urlparse(current)
        # Pin to the validated IP so no second DNS lookup can rebind the host.
        # Keep the real hostname for the Host header and TLS SNI/cert check.
        connect_url = httpx.URL(current).copy_with(host=ip)
        req_headers = {"Host": host}
        extensions = {"sni_hostname": host} if parsed.scheme.lower() == "https" else {}
        try:
            resp = await client.get(connect_url, headers=req_headers, extensions=extensions)
        except Exception as e:
            logger.debug("website_analyzer: fetch failed for %s: %s", current, e)
            return None

        if resp.is_redirect and resp.headers.get("location"):
            # Resolve the redirect against the hostname URL, then re-validate.
            current = str(httpx.URL(current).join(resp.headers["location"]))
            continue
        if resp.status_code == 200 and "text/html" in resp.headers.get("content-type", "text/html"):
            return resp.text
        return None

    logger.debug("website_analyzer: too many redirects for %s", url)
    return None


# (HTML extraction helpers) ---------------------------------------------------

def _strip_blocks(html: str) -> str:
    return re.sub(
        r"<(script|style|noscript)[^>]*>.*?</\1>", " ", html, flags=re.IGNORECASE | re.DOTALL
    )


def _extract_title(html: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    return _clean(m.group(1)) if m else ""


def _extract_meta_description(html: str) -> str:
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
    for entity, char in (("&amp;", "&"), ("&nbsp;", " "), ("&#39;", "'"), ("&quot;", '"'), ("&apos;", "'")):
        text = text.replace(entity, char)
    return re.sub(r"\s+", " ", text).strip()


async def analyze_website(url: str) -> WebsiteAnalysis:
    """Fetch homepage + common pages and extract a light text signal.

    Raises WebsiteUnreachableError (incl. BlockedURLError) if the homepage
    cannot be fetched or targets a non-public address.
    """
    url = normalize_url(url)
    if not url or not urlparse(url).netloc:
        raise WebsiteUnreachableError(f"Invalid URL: {url!r}")

    headers = {"User-Agent": _USER_AGENT, "Accept": "text/html"}
    # follow_redirects=False: redirects are followed manually in _safe_get so
    # each hop is re-validated by the SSRF guard.
    async with httpx.AsyncClient(timeout=8.0, follow_redirects=False, headers=headers) as client:
        home = await _safe_get(client, url)  # may raise BlockedURLError
        if home is None:
            raise WebsiteUnreachableError(f"Could not reach {url}")

        raw_pages = {"/": home}

        async def _try(path: str):
            try:
                return await _safe_get(client, urljoin(url, path))
            except WebsiteUnreachableError:
                return None

        secondary = await asyncio.gather(*[_try(p) for p in COMMON_PATHS])
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
