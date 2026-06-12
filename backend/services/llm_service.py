"""LLM service for onboarding brand analysis.

Turns the light text signal from website_analyzer into structured brand,
competitor, and prompt suggestions. Behind an abstract interface so the
provider can be swapped (the scrapers/storage follow the same pattern).

If the LLM key is missing or the call fails/times out, analyze_brand returns a
minimal fallback (brand name guessed from the page title, empty lists) so
onboarding still works -- just without smart suggestions.
"""

import os
import re
import json
import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import httpx

from backend.services.website_analyzer import WebsiteAnalysis

logger = logging.getLogger(__name__)

_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
# Lighter model with a separate, more generous quota -- used when the primary
# model (LLM_MODEL) is rate-limited (429) or overloaded (5xx).
_FALLBACK_MODEL = "gemini-2.0-flash-lite"
_PLACEHOLDER_KEYS = {"", "your-api-key-here", "change-me"}


@dataclass
class BrandSuggestions:
    brand_name: str = ""
    brand_aliases: list = field(default_factory=list)
    industry: str = ""
    location: str = ""
    company_scale: str = ""
    # Each competitor is {"name": str, "reason": str}.
    competitors: list = field(default_factory=list)
    suggested_prompts: list = field(default_factory=list)
    prompt_topics: list = field(default_factory=list)


class BaseLLMService(ABC):
    @abstractmethod
    async def analyze_brand(self, website_data: WebsiteAnalysis) -> BrandSuggestions:
        raise NotImplementedError


def _brand_from_title(title: str) -> str:
    """Best-effort brand name from a <title> like 'Acme - Project Management'."""
    if not title:
        return ""
    # Titles are usually "Brand | Tagline" or "Brand - Tagline" or "Page — Brand".
    parts = re.split(r"\s*[|\-–—:·]\s*", title)
    parts = [p.strip() for p in parts if p.strip()]
    if not parts:
        return title.strip()
    # Heuristic: the shortest segment is usually the brand, not the tagline.
    return min(parts, key=len)


def _fallback(website_data: WebsiteAnalysis) -> BrandSuggestions:
    return BrandSuggestions(brand_name=_brand_from_title(website_data.title))


def _build_prompt(website_data: WebsiteAnalysis) -> str:
    headings = " | ".join(website_data.headings[:30])
    body = website_data.body_text[:4000]
    location = website_data.detected_location or "Not detected - infer from website content if possible"
    return f"""You are analyzing a company's website to help set up AI search visibility tracking. Your job is to provide accurate, contextually relevant suggestions.

CRITICAL RULES:
- Be SPECIFIC to this exact company's niche, size, and geography. Never give generic industry-wide answers.
- For aliases: ONLY include names people genuinely use for this brand. Look at how the brand refers to itself on the website. Never invent abbreviations or acronyms unless they appear on the site. If there are no real aliases, return an empty array.
- For competitors: Match the company's EXACT niche AND geographic market. A small software house in Pakistan competes with other software houses in Pakistan, NOT with Accenture or IBM. A global SaaS tool competes with similar global SaaS tools. Match the scale.
- For prompts: Write them as a real human would type into ChatGPT. Include location-specific queries when the brand serves a local/regional market (e.g. "best software house in Sahiwal", "top IT companies in Pakistan for custom development").

Company website: {website_data.url}
Detected location: {location}

Website content:
Title: {website_data.title}
Description: {website_data.description}
Headings: {headings}
Content: {body}

Return ONLY a valid JSON object (no markdown, no backticks, no explanation) with this exact structure:
{{
  "brand_name": "exact brand name as displayed on the website",
  "brand_aliases": ["only real alternate names found on the site or commonly used by people, empty array if none"],
  "industry": "specific niche, not broad category (e.g. 'Custom Software Development' not 'IT')",
  "location": "city, country if detectable, otherwise 'Global' or 'Unknown'",
  "company_scale": "local/regional/national/global - based on their market reach",
  "competitors": [
    {{"name": "Competitor Name", "reason": "specific reason they compete in the same niche and market"}}
  ],
  "suggested_prompts": ["..."],
  "prompt_topics": ["topic1", "topic2", "topic3", "topic4"]
}}

Provide exactly 5 competitors, each matched to the same niche AND geography AND scale. Generate 15-20 suggested prompts: conversational, buyer-intent (researching/comparing/about to purchase), location-aware where relevant. Mix "best [category] in [location]", "[brand] vs [competitor]", "is [brand] good for [use case]", "alternatives to [brand]", and "[category] companies that specialize in [specific service]". Never give a global/generic prompt when the brand clearly serves a local or regional market."""


def _parse_json(text: str) -> dict:
    """Parse JSON, tolerating markdown fences / surrounding prose."""
    text = (text or "").strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    # Strip ```json ... ``` fences and retry.
    fenced = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE).strip()
    try:
        return json.loads(fenced)
    except Exception:
        pass
    # Last resort: grab the outermost {...} or [...] block.
    m = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if m:
        return json.loads(m.group(0))
    raise ValueError("No JSON object found in LLM response")


def _coerce(data: dict, fallback: BrandSuggestions) -> BrandSuggestions:
    def _str_list(value) -> list:
        if not isinstance(value, list):
            return []
        return [str(v).strip() for v in value if str(v).strip()]

    competitors = []
    for c in data.get("competitors", []) if isinstance(data.get("competitors"), list) else []:
        if isinstance(c, dict) and c.get("name"):
            competitors.append({"name": str(c["name"]).strip(), "reason": str(c.get("reason", "")).strip()})
        elif isinstance(c, str) and c.strip():
            competitors.append({"name": c.strip(), "reason": ""})

    return BrandSuggestions(
        brand_name=str(data.get("brand_name") or fallback.brand_name).strip(),
        brand_aliases=_str_list(data.get("brand_aliases")),
        industry=str(data.get("industry") or "").strip(),
        location=str(data.get("location") or "").strip(),
        company_scale=str(data.get("company_scale") or "").strip(),
        competitors=competitors,
        suggested_prompts=_str_list(data.get("suggested_prompts")),
        prompt_topics=_str_list(data.get("prompt_topics")),
    )


class GeminiLLMService(BaseLLMService):
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key if api_key is not None else os.getenv("LLM_API_KEY", "")
        self.model = model or os.getenv("LLM_MODEL", "gemini-2.5-flash")

    def _has_key(self) -> bool:
        return bool(self.api_key) and self.api_key.strip().lower() not in _PLACEHOLDER_KEYS

    async def _generate_text(self, prompt: str, temperature: float = 0.7, timeout: float = 12.0):
        """Call Gemini with model fallback; return the response text or None.

        Tries the configured model first; on rate-limit (429) / overload (5xx) /
        timeout it retries once with the lighter fallback model (separate, more
        generous quota). Returns None if every model fails or the request is
        rejected (4xx) -- callers decide what fallback to use. The API key is
        sent as a header and never logged (str(e) would contain the URL).
        """
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature, "responseMimeType": "application/json"},
        }
        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}

        models = [self.model]
        if _FALLBACK_MODEL not in models:
            models.append(_FALLBACK_MODEL)

        for model in models:
            url = _GEMINI_URL.format(model=model)
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code in (429, 500, 502, 503, 504):
                    logger.warning(
                        "llm_service: model %s unavailable (HTTP %s); trying fallback model",
                        model, resp.status_code,
                    )
                    await asyncio.sleep(0.5)
                    continue  # try the next model
                resp.raise_for_status()
                body = resp.json()
                text = body["candidates"][0]["content"]["parts"][0]["text"]
                logger.debug("llm_service: raw LLM response (%s):\n%s", model, text)
                return text
            except httpx.HTTPStatusError as e:
                # 4xx (bad key/request) -- no point retrying other models.
                logger.warning(
                    "llm_service: request failed (HTTP %s) on %s", e.response.status_code, model,
                )
                return None
            except (httpx.TimeoutException, httpx.TransportError):
                logger.warning("llm_service: %s timed out; trying fallback model", model)
                continue
            except Exception as e:
                logger.warning("llm_service: request failed (%s) on %s", type(e).__name__, model)
                return None

        logger.warning("llm_service: all models rate-limited/unavailable")
        return None

    async def generate_json(self, prompt: str, temperature: float = 0.3):
        """Run a JSON-returning prompt; return the parsed object/list or None.

        Generic entry point reused by the parser (mention/sentiment/source
        classification). Returns None when the LLM is unavailable or the
        response can't be parsed as JSON -- callers degrade gracefully.
        """
        if not self._has_key():
            logger.info("llm_service: no LLM_API_KEY configured; skipping LLM call")
            return None
        text = await self._generate_text(prompt, temperature=temperature)
        if text is None:
            return None
        try:
            return _parse_json(text)
        except Exception:
            logger.warning("llm_service: could not parse JSON from LLM response")
            return None

    async def analyze_brand(self, website_data: WebsiteAnalysis) -> BrandSuggestions:
        fallback = _fallback(website_data)

        if not self._has_key():
            logger.info("llm_service: no LLM_API_KEY configured; using fallback suggestions")
            return fallback

        text = await self._generate_text(_build_prompt(website_data), temperature=0.7)
        if text is None:
            return fallback
        try:
            return _coerce(_parse_json(text), fallback)
        except Exception as e:
            logger.warning("llm_service: brand analysis parse failed (%s), using fallback", type(e).__name__)
            return fallback
