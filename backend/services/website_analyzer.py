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
import json
import socket
import asyncio
import logging
import ipaddress
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

import httpx

logger = logging.getLogger(__name__)

# Pages worth a peek beyond the homepage. 404s are skipped silently. The
# about/contact/team pages carry the richest location + niche signals.
COMMON_PATHS = [
    "/about", "/about-us", "/contact", "/contact-us", "/team", "/our-team",
    "/pricing", "/features", "/products", "/services",
]
_USER_AGENT = "Mozilla/5.0 (compatible; AIScopeBot/1.0; +https://aiscope.app)"
_MAX_BODY_WORDS = 2000
_ALLOWED_SCHEMES = {"http", "https"}
_MAX_REDIRECTS = 3

# Below this many chars of extracted body text -- combined with no headings and
# no JSON-LD -- the httpx fetch is treated as an empty client-rendered shell and
# we fall back to Playwright to render it.
SPA_DETECTION_THRESHOLD = 200  # chars of body text below which we suspect SPA

# A real desktop Chrome UA for the Playwright fallback (the bot UA above invites
# more blocking; a SPA we couldn't read statically is exactly where it matters).
_CHROME_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
# networkidle wait, then a hard ceiling on the whole Playwright attempt so the
# analyze-website endpoint still answers within ~30s even when rendering is slow.
_PLAYWRIGHT_NAV_TIMEOUT_MS = 15000
_PLAYWRIGHT_TOTAL_TIMEOUT_S = 20.0


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
    # Heuristic location hints (phrases / phone codes / currencies) for the LLM.
    detected_location: str = ""


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


def _extract_supplementary(html: str) -> tuple[str, str]:
    """Pull JSON-LD structured data + rich meta tags from raw HTML.

    SPAs frequently ship these in the static shell even when the visible body
    is JS-rendered, so this is often the only real signal for a client-rendered
    site. Returns (extra_text, location_hint).
    """
    texts: list = []
    locs: list = []

    # JSON-LD blocks (Organization/LocalBusiness schema: name, description,
    # address, areaServed). Stripped from body_text elsewhere, so harvest here.
    for block in re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.IGNORECASE | re.DOTALL,
    ):
        try:
            data = json.loads(block.strip())
        except Exception:
            continue
        stack = list(data) if isinstance(data, list) else [data]
        nodes: list = []
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                graph = node.get("@graph")
                if isinstance(graph, list):
                    stack.extend(graph)
                nodes.append(node)
        for node in nodes:
            for key in ("name", "description", "slogan"):
                val = node.get(key)
                if isinstance(val, str) and val.strip():
                    texts.append(val.strip())
            addr = node.get("address")
            if isinstance(addr, dict):
                # Each part may be a plain string or an object with a "name".
                def _part(v):
                    if isinstance(v, dict):
                        return str(v.get("name", "")).strip()
                    return str(v or "").strip()
                parts = [_part(addr.get(k)) for k in ("addressLocality", "addressRegion", "addressCountry")]
                parts = [p for p in parts if p]
                if parts:
                    locs.append(", ".join(parts))
            elif isinstance(addr, str) and addr.strip():
                locs.append(addr.strip())
            area = node.get("areaServed")
            if isinstance(area, str) and area.strip():
                locs.append(area.strip())

    # Rich meta tags (og:*, keywords, geo.*).
    for prop in ("og:site_name", "og:description", "og:title", "keywords"):
        m = re.search(
            r'<meta[^>]+(?:property|name)=["\']' + re.escape(prop) + r'["\'][^>]+content=["\']([^"\']*)["\']',
            html, re.IGNORECASE,
        )
        if m and m.group(1).strip():
            texts.append(_clean(m.group(1)))
    for prop in ("geo.placename", "geo.region", "og:locale"):
        m = re.search(
            r'<meta[^>]+(?:property|name)=["\']' + re.escape(prop) + r'["\'][^>]+content=["\']([^"\']*)["\']',
            html, re.IGNORECASE,
        )
        if m and m.group(1).strip():
            locs.append(_clean(m.group(1)))

    return _clean(" ".join(dict.fromkeys(texts))), " | ".join(dict.fromkeys(locs))[:200]


def _extract_location_signals(text: str) -> str:
    """Pull cheap geographic hints (phrases, phone codes, currencies) for the LLM.

    Not a geocoder -- just surfaces signals so the LLM can pin the company's
    actual city/country/scale instead of guessing a global default.
    """
    text = text[:25000]
    hints: list = []

    # "based in / located in / headquartered in / offices in <Place>"
    loc_re = re.compile(
        r"\b(?:based in|located in|headquartered in|head ?office(?:\s+in)?|"
        r"offices?\s+in|serving|proudly serving)\s+([A-Z][A-Za-z .,&'\-]{2,50})",
        re.IGNORECASE,
    )
    for m in loc_re.finditer(text):
        phrase = _clean(m.group(0))
        if phrase and phrase not in hints:
            hints.append(phrase)
        if len(hints) >= 4:
            break

    # International phone prefixes like +92, +1, +44 (followed by more digits).
    codes = sorted(set(re.findall(r"\+\d{1,3}(?=[\s().-]*\d{2})", text)))
    if codes:
        hints.append("Phone country code(s): " + ", ".join(codes[:5]))

    # Explicit currency codes / symbols give away the market.
    cur = sorted(set(re.findall(r"\b(PKR|USD|EUR|GBP|INR|AED|SAR|CAD|AUD|NGN|ZAR|BDT)\b", text)))
    if cur:
        hints.append("Currency: " + ", ".join(cur[:6]))
    syms = sorted(set(re.findall(r"[₨£€₹]", text)))
    if syms:
        hints.append("Currency symbol(s): " + " ".join(syms))

    return " | ".join(hints[:8])


def _build_analysis(url: str, raw_pages: dict) -> WebsiteAnalysis:
    """Run the extraction pipeline over fetched HTML pages.

    Shared by the httpx path and the Playwright fallback so a JS-rendered SPA
    goes through exactly the same title/description/headings/JSON-LD/geo
    extraction as a server-rendered site. `raw_pages` maps path -> HTML; the
    homepage lives under "/".
    """
    home = raw_pages.get("/", "")
    title = _extract_title(home)
    description = _extract_meta_description(home)

    headings: list = []
    for content in raw_pages.values():
        for h in _extract_headings(content):
            if h not in headings:
                headings.append(h)
    headings = headings[:40]

    # JSON-LD + rich meta across all pages (the real signal for SPAs).
    supp_texts: list = []
    supp_locs: list = []
    for content in raw_pages.values():
        s_text, s_loc = _extract_supplementary(content)
        if s_text:
            supp_texts.append(s_text)
        if s_loc:
            supp_locs.append(s_loc)
    supp_blob = _clean(" ".join(dict.fromkeys(supp_texts)))

    if not description and supp_blob:
        description = supp_blob[:300]

    # Full stripped text (across all pages) + structured signals; capped body.
    page_texts = [_strip_to_text(content) for content in raw_pages.values()]
    full_text = " ".join(page_texts + supp_texts)

    phrase_signals = _extract_location_signals(full_text)
    structured_loc = " | ".join(dict.fromkeys(supp_locs))
    detected_location = " | ".join(p for p in (structured_loc, phrase_signals) if p)[:300]

    words = full_text.split()
    body_text = " ".join(words[:_MAX_BODY_WORDS])

    return WebsiteAnalysis(
        url=url,
        title=title,
        description=description,
        headings=headings,
        body_text=body_text,
        raw_pages=raw_pages,
        detected_location=detected_location,
    )


def _has_jsonld(raw_pages: dict) -> bool:
    """True if any page carries a non-empty application/ld+json block."""
    for content in raw_pages.values():
        for block in re.findall(
            r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            content, re.IGNORECASE | re.DOTALL,
        ):
            try:
                if json.loads(block.strip()):
                    return True
            except Exception:
                continue
    return False


def _is_empty_shell(analysis: WebsiteAnalysis, raw_pages: dict) -> bool:
    """Detect a client-rendered SPA whose static HTML carries no real signal.

    Empty shell = under SPA_DETECTION_THRESHOLD chars of body text AND no
    headings AND no JSON-LD. All three must hold: a site with structured data
    or visible headings gave us something usable even if the body is short.
    """
    return (
        len(analysis.body_text) < SPA_DETECTION_THRESHOLD
        and not analysis.headings
        and not _has_jsonld(raw_pages)
    )


async def _render_with_playwright(url: str) -> str | None:
    """Render a client-side SPA with headless Chromium; return its HTML or None.

    Playwright is heavy, so it's imported lazily here and only ever used as the
    empty-shell fallback. One browser, one context, one page -- no reuse. The
    URL is re-validated against the SSRF guard before we navigate (Chromium does
    its own DNS, bypassing _safe_get's IP pinning, so a rebind would otherwise
    slip through). Returns None on any failure so the caller keeps httpx's data.
    """
    # Re-validate: reject if the host now resolves to a non-public address.
    try:
        await asyncio.to_thread(_resolve_and_validate, url)
    except BlockedURLError:
        logger.warning("website_analyzer: %s blocked by SSRF guard; skipping Playwright", url)
        return None

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.warning("website_analyzer: playwright not installed; cannot render SPA")
        return None

    try:  # playwright-stealth masks automation fingerprints; degrade if absent.
        from playwright_stealth import Stealth
        pw_cm = Stealth().use_async(async_playwright())
    except Exception:
        pw_cm = async_playwright()

    async with pw_cm as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        try:
            context = await browser.new_context(user_agent=_CHROME_USER_AGENT, locale="en-US")
            page = await context.new_page()
            await page.goto(url, wait_until="networkidle", timeout=_PLAYWRIGHT_NAV_TIMEOUT_MS)
            return await page.content()
        finally:
            await browser.close()


async def analyze_website(url: str) -> WebsiteAnalysis:
    """Fetch homepage + common pages and extract a light text signal.

    Fast path is httpx (SSR sites resolve in well under 10s). If the static HTML
    is an empty client-rendered shell, falls back to Playwright to render the
    SPA, then runs the same extraction over the rendered HTML.

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

    analysis = _build_analysis(url, raw_pages)

    if not _is_empty_shell(analysis, raw_pages):
        logger.info("[website_analyzer] %s: using httpx (SSR)", url)
        return analysis

    # Empty shell: likely a JS-rendered SPA. Try Playwright, but timebox the whole
    # attempt -- partial httpx data beats hanging the endpoint past its budget.
    logger.info(
        "[website_analyzer] %s: httpx returned empty shell, falling back to Playwright (SPA)", url
    )
    try:
        rendered = await asyncio.wait_for(
            _render_with_playwright(url), timeout=_PLAYWRIGHT_TOTAL_TIMEOUT_S
        )
    except asyncio.TimeoutError:
        logger.warning("[website_analyzer] %s: Playwright timed out; using httpx data", url)
        rendered = None
    except Exception as e:
        logger.warning(
            "[website_analyzer] %s: Playwright render failed (%s); using httpx data",
            url, type(e).__name__,
        )
        rendered = None

    if rendered:
        # Re-run extraction over the rendered HTML, keeping any secondary pages
        # httpx did manage to fetch.
        rendered_pages = dict(raw_pages)
        rendered_pages["/"] = rendered
        rendered_analysis = _build_analysis(url, rendered_pages)
        # Only prefer the rendered result if it actually gave us more to work with.
        if not _is_empty_shell(rendered_analysis, rendered_pages):
            logger.info("[website_analyzer] %s: Playwright render succeeded (SPA)", url)
            return rendered_analysis

    return analysis
