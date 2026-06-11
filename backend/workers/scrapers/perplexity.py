"""Perplexity adapter -- the Milestone 2 proof-of-concept.

Perplexity is the friendliest scrape target: it answers unauthenticated, renders
server-side, and shows citations as visible links. This adapter drives a headless
stealth Chromium, types the prompt like a human, waits for the streamed answer to
settle, then extracts the answer text and cited source URLs.

One browser context per scrape, torn down afterwards. The account argument is
accepted for future use (rate-limit fallback) but unauthenticated runs work today.
"""

import time
import random
import asyncio

from playwright.async_api import async_playwright

from backend.workers.scrapers.base_adapter import BasePlatformAdapter, RawAnswer
from backend.workers.scrapers.exceptions import (
    ScraperTimeout,
    CaptchaDetected,
    RateLimited,
    UnexpectedLayout,
)

try:  # playwright-stealth masks automation fingerprints; degrade gracefully if absent.
    from playwright_stealth import Stealth
    _HAS_STEALTH = True
except Exception:  # pragma: no cover - import guard
    _HAS_STEALTH = False


# Rotate from a small list of recent desktop Chrome UAs.
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

# Candidate selectors for the prompt input and answer body. Perplexity's DOM
# shifts often, so each is tried in turn and we fall back to page heuristics.
INPUT_SELECTORS = [
    'textarea[placeholder]',
    'textarea[aria-label]',
    'div[contenteditable="true"]',
    'textarea',
]

# Phrases that mean "blocked", not "answer".
CAPTCHA_MARKERS = ["captcha", "just a moment", "cloudflare", "unusual traffic", "verify you are human"]
RATELIMIT_MARKERS = ["rate limit", "too many requests", "try again later", "429"]

# JS run in the page to read the current best answer block and the cited links.
_ANSWER_JS = """
() => {
  const sels = ['[data-testid="answer"]', 'div[class*="prose"]', '.markdown', 'main'];
  let best = '';
  for (const s of sels) {
    for (const el of document.querySelectorAll(s)) {
      const t = (el.innerText || '').trim();
      if (t.length > best.length) best = t;
    }
  }
  return best;
}
"""

_SOURCES_JS = """
() => {
  const urls = [];
  const seen = new Set();
  for (const a of document.querySelectorAll('a[href^="http"]')) {
    const href = a.href;
    let host;
    try { host = new URL(href).hostname; } catch (e) { continue; }
    if (host.includes('perplexity.ai')) continue;
    if (seen.has(href)) continue;
    seen.add(href);
    urls.push(href);
  }
  return urls;
}
"""

_FOLLOWUPS_JS = """
() => {
  const out = [];
  // "Related" follow-up suggestions are short clickable rows near the bottom.
  for (const el of document.querySelectorAll('[class*="related"] *, [data-testid*="related"] *')) {
    const t = (el.innerText || '').trim();
    if (t && t.length < 160 && !out.includes(t)) out.push(t);
  }
  return out.slice(0, 8);
}
"""


class PerplexityAdapter(BasePlatformAdapter):
    platform_name = "perplexity"

    BASE_URL = "https://www.perplexity.ai/"

    def __init__(
        self,
        headless: bool = True,
        nav_timeout_ms: int = 30000,
        answer_timeout_ms: int = 60000,
        stable_seconds: float = 2.0,
    ):
        self.headless = headless
        self.nav_timeout_ms = nav_timeout_ms
        self.answer_timeout_ms = answer_timeout_ms
        self.stable_seconds = stable_seconds

    async def run_prompt(self, prompt_text: str, account: dict = None, proxy: dict = None) -> RawAnswer:
        started = time.monotonic()
        user_agent = random.choice(USER_AGENTS)
        viewport = {
            "width": random.randint(1280, 1440),
            "height": random.randint(800, 900),
        }

        launch_kwargs = {
            "headless": self.headless,
            "args": ["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        }
        if proxy and proxy.get("server"):
            launch_kwargs["proxy"] = {"server": proxy["server"]}

        # With stealth, the context manager auto-injects fingerprint masking into
        # every new context/page; without it we still run, just less disguised.
        pw_cm = Stealth().use_async(async_playwright()) if _HAS_STEALTH else async_playwright()

        async with pw_cm as p:
            browser = await p.chromium.launch(**launch_kwargs)
            context = await browser.new_context(
                user_agent=user_agent,
                viewport=viewport,
                locale="en-US",
            )
            try:
                await self._maybe_load_cookies(context, account)
                page = await context.new_page()
                page.set_default_timeout(self.nav_timeout_ms)

                await page.goto(self.BASE_URL, wait_until="domcontentloaded", timeout=self.nav_timeout_ms)
                # Random 1-3s pause to look like a human reading the page.
                await asyncio.sleep(random.uniform(1.0, 3.0))

                await self._detect_blockers(page)

                input_el = await self._find_input(page)
                await self._type_prompt(page, input_el, prompt_text)
                await page.keyboard.press("Enter")

                answer_text = await self._wait_for_answer(page)
                await self._detect_blockers(page)

                sources = await self._safe_eval(page, _SOURCES_JS, default=[])
                followups = await self._safe_eval(page, _FOLLOWUPS_JS, default=[])
                screenshot = await self._safe_screenshot(page)
                raw_html = await page.content()

                elapsed_ms = int((time.monotonic() - started) * 1000)
                return RawAnswer(
                    answer_text=answer_text,
                    sources=sources,
                    raw_html=raw_html,
                    screenshot=screenshot,
                    metadata={
                        "platform": self.platform_name,
                        "response_time_ms": elapsed_ms,
                        "user_agent": user_agent,
                        "viewport": viewport,
                        "account_used": (account or {}).get("email"),
                        "follow_ups": followups,
                        "source_count": len(sources),
                    },
                )
            finally:
                # One context per scrape: always tear it down.
                await context.close()
                await browser.close()

    async def _maybe_load_cookies(self, context, account):
        """Load session cookies from a checked-out account, if provided and valid."""
        if not account:
            return
        cookies = account.get("cookies")
        # Expect Playwright cookie dicts; ignore anything malformed (POC tolerance).
        if isinstance(cookies, list) and cookies:
            try:
                await context.add_cookies(cookies)
            except Exception:
                pass

    async def _find_input(self, page):
        for selector in INPUT_SELECTORS:
            try:
                el = await page.wait_for_selector(selector, timeout=5000, state="visible")
                if el:
                    return el
            except Exception:
                continue
        excerpt = await self._page_excerpt(page)
        raise UnexpectedLayout(
            "Could not locate the prompt input on the page",
            platform=self.platform_name,
            page_excerpt=excerpt,
        )

    async def _type_prompt(self, page, input_el, prompt_text):
        await input_el.click()
        # Per-character delay randomized 50-150ms to mimic human typing.
        for ch in prompt_text:
            await page.keyboard.type(ch)
            await asyncio.sleep(random.uniform(0.05, 0.15))

    async def _wait_for_answer(self, page) -> str:
        """Poll the answer block until it stops growing for `stable_seconds`.

        Perplexity streams its response, so "done" is detected as text that is
        non-empty and unchanged across a short window, rather than a fixed wait.
        """
        deadline = time.monotonic() + (self.answer_timeout_ms / 1000)
        last_text = ""
        stable_since = None

        while time.monotonic() < deadline:
            await asyncio.sleep(0.5)
            current = await self._safe_eval(page, _ANSWER_JS, default="")
            if current and current == last_text:
                if stable_since is None:
                    stable_since = time.monotonic()
                elif time.monotonic() - stable_since >= self.stable_seconds:
                    return current
            else:
                stable_since = None
                last_text = current

        if last_text:
            # Timed out but we did capture something -- return the partial answer.
            return last_text

        excerpt = await self._page_excerpt(page)
        raise ScraperTimeout(
            f"Answer did not render within {self.answer_timeout_ms}ms",
            platform=self.platform_name,
            page_excerpt=excerpt,
        )

    async def _detect_blockers(self, page):
        try:
            content = (await page.content()).lower()
        except Exception:
            return
        if any(m in content for m in CAPTCHA_MARKERS):
            raise CaptchaDetected(
                "CAPTCHA / bot challenge detected",
                platform=self.platform_name,
                page_excerpt=content[:2000],
            )
        if any(m in content for m in RATELIMIT_MARKERS):
            raise RateLimited(
                "Rate-limit page detected",
                platform=self.platform_name,
                page_excerpt=content[:2000],
            )

    async def _safe_eval(self, page, js, default):
        try:
            return await page.evaluate(js)
        except Exception:
            return default

    async def _safe_screenshot(self, page):
        try:
            return await page.screenshot(full_page=True)
        except Exception:
            return None

    async def _page_excerpt(self, page, limit: int = 2000) -> str:
        try:
            return (await page.content())[:limit]
        except Exception:
            return ""
