"""Gemini API adapter.

Unlike the Perplexity adapter, this does NOT drive a browser -- it calls the
Gemini API directly with the existing LLM_API_KEY. No Playwright, no account
pool, ~3-5s per run, and it's reliable (no bot challenges). Our fastest path to
real data.

Google Search grounding is requested via the `google_search` tool so Gemini
actually searches the web and cites real sources; grounded URLs are pulled from
the response's groundingMetadata (plus any URLs in the answer text). If the API
rejects the tool, we retry once without it so we still capture an answer.

Retry policy (the worker task maps these): 429 -> RateLimited (retryable);
4xx/5xx -> ScraperError (permanent).
"""

import os
import re
import time
import logging

import httpx

from backend.workers.scrapers.base_adapter import BasePlatformAdapter, RawAnswer
from backend.workers.scrapers.exceptions import RateLimited, ScraperError

logger = logging.getLogger(__name__)

_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
_PLACEHOLDER_KEYS = {"", "your-api-key-here", "change-me"}

_SYSTEM_INSTRUCTION = (
    "You are a helpful AI assistant. Answer the user's question thoroughly. "
    "When recommending products, services, or brands, cite your sources with "
    "URLs where possible."
)

# Matches http(s) URLs embedded in the answer text. Trailing punctuation trimmed.
_URL_RE = re.compile(r"https?://[^\s<>\")\]]+", re.IGNORECASE)
_TRAILING = ".,;:!?)]}'\"’”"


class GeminiAPIAdapter(BasePlatformAdapter):
    platform_name = "gemini"

    def __init__(self, model: str = None, timeout: float = 30.0):
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.model = model or os.getenv("GEMINI_API_MODEL", "gemini-2.0-flash")
        self.timeout = timeout

    async def run_prompt(self, prompt_text: str, account: dict = None, proxy: dict = None) -> RawAnswer:
        if not self.api_key or self.api_key.strip().lower() in _PLACEHOLDER_KEYS:
            raise ScraperError("LLM_API_KEY is not configured", platform=self.platform_name)

        started = time.monotonic()
        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}
        url = _GEMINI_URL.format(model=self.model)

        def _payload(with_tools: bool) -> dict:
            body = {
                "system_instruction": {"parts": [{"text": _SYSTEM_INSTRUCTION}]},
                "contents": [{"role": "user", "parts": [{"text": prompt_text}]}],
            }
            if with_tools:
                # Google Search grounding -> Gemini searches the web and cites real URLs.
                body["tools"] = [{"google_search": {}}]
            return body

        grounding_used = True
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.post(url, headers=headers, json=_payload(True))
            except (httpx.TimeoutException, httpx.TransportError) as e:
                # Network hiccup -> let the worker retry.
                raise RateLimited(f"Gemini API request failed: {type(e).__name__}", platform=self.platform_name)

            if resp.status_code == 400:
                # The model/region may not support the google_search tool -- retry
                # once without grounding so we still get an answer.
                logger.warning("gemini_api: grounded request got 400; retrying without google_search")
                grounding_used = False
                resp = await client.post(url, headers=headers, json=_payload(False))

        self._raise_for_status(resp)

        body = resp.json()
        answer_text = self._extract_text(body)
        sources = self._extract_sources(answer_text, body)
        elapsed_ms = int((time.monotonic() - started) * 1000)

        return RawAnswer(
            answer_text=answer_text,
            sources=sources,
            raw_html=None,
            screenshot=None,
            metadata={
                "platform": self.platform_name,
                "model": self.model,
                "response_time_ms": elapsed_ms,
                "grounding_requested": grounding_used,
                "web_search_used": len(sources) > 0,
                "source_count": len(sources),
            },
        )

    def _raise_for_status(self, resp: httpx.Response) -> None:
        if resp.status_code == 200:
            return
        # Never log resp.text/str(e) -- the request URL/key could leak.
        if resp.status_code == 429:
            raise RateLimited("Gemini API rate-limited (HTTP 429)", platform=self.platform_name)
        raise ScraperError(f"Gemini API error (HTTP {resp.status_code})", platform=self.platform_name)

    @staticmethod
    def _extract_text(body: dict) -> str:
        try:
            parts = body["candidates"][0]["content"]["parts"]
        except (KeyError, IndexError, TypeError):
            return ""
        texts = [p.get("text", "") for p in parts if isinstance(p, dict) and p.get("text")]
        return "\n".join(t for t in texts if t).strip()

    @classmethod
    def _extract_sources(cls, answer_text: str, body: dict) -> list:
        """Real grounded URLs (groundingMetadata) + any URLs in the answer text."""
        urls = []
        seen = set()

        def _add(u):
            u = (u or "").strip().rstrip(_TRAILING)
            if u and u.lower().startswith(("http://", "https://")) and u not in seen:
                seen.add(u)
                urls.append(u)

        # Grounding chunks: the actual web pages Gemini consulted.
        try:
            chunks = body["candidates"][0].get("groundingMetadata", {}).get("groundingChunks", [])
        except (KeyError, IndexError, TypeError):
            chunks = []
        for chunk in chunks or []:
            if isinstance(chunk, dict):
                web = chunk.get("web") or {}
                _add(web.get("uri"))

        # URLs the model wrote inline.
        for m in _URL_RE.finditer(answer_text or ""):
            _add(m.group(0))

        return urls
