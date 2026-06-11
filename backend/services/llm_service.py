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
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import httpx

from backend.services.website_analyzer import WebsiteAnalysis

logger = logging.getLogger(__name__)

_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
_PLACEHOLDER_KEYS = {"", "your-api-key-here", "change-me"}


@dataclass
class BrandSuggestions:
    brand_name: str = ""
    brand_aliases: list = field(default_factory=list)
    industry: str = ""
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
    headings = " | ".join(website_data.headings[:25])
    body = website_data.body_text[:3000]
    return (
        "Analyze this website and return a JSON object with exactly this structure:\n"
        "{\n"
        '  "brand_name": "the company/product name",\n'
        '  "brand_aliases": ["list", "of", "alternate", "names", "abbreviations"],\n'
        '  "industry": "the niche/industry this brand operates in",\n'
        '  "competitors": [\n'
        '    {"name": "Competitor 1", "reason": "why they compete"}\n'
        "  ],\n"
        '  "suggested_prompts": ["..."],\n'
        '  "prompt_topics": ["topic1", "topic2", "topic3"]\n'
        "}\n\n"
        "Provide exactly 5 competitors. Generate 15-20 suggested prompts that real "
        "users would type into ChatGPT or Perplexity when researching this type of "
        "product/service. Make them conversational and buyer-intent focused, not "
        "keyword-style. Include comparison prompts, 'best of' prompts, "
        "alternative-seeking prompts, and use-case specific prompts.\n\n"
        "Return ONLY the JSON object, no markdown fences, no commentary.\n\n"
        "Website content:\n"
        f"Title: {website_data.title}\n"
        f"Description: {website_data.description}\n"
        f"Headings: {headings}\n"
        f"Content: {body}\n"
    )


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
    # Last resort: grab the outermost {...} block.
    m = re.search(r"\{.*\}", text, re.DOTALL)
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
        competitors=competitors,
        suggested_prompts=_str_list(data.get("suggested_prompts")),
        prompt_topics=_str_list(data.get("prompt_topics")),
    )


class GeminiLLMService(BaseLLMService):
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key if api_key is not None else os.getenv("LLM_API_KEY", "")
        self.model = model or os.getenv("LLM_MODEL", "gemini-1.5-flash")

    async def analyze_brand(self, website_data: WebsiteAnalysis) -> BrandSuggestions:
        fallback = _fallback(website_data)

        if not self.api_key or self.api_key.strip().lower() in _PLACEHOLDER_KEYS:
            logger.info("llm_service: no LLM_API_KEY configured; using fallback suggestions")
            return fallback

        url = _GEMINI_URL.format(model=self.model)
        payload = {
            "contents": [{"parts": [{"text": _build_prompt(website_data)}]}],
            "generationConfig": {"temperature": 0.7, "responseMimeType": "application/json"},
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, params={"key": self.api_key}, json=payload)
                resp.raise_for_status()
                body = resp.json()
            text = body["candidates"][0]["content"]["parts"][0]["text"]
            data = _parse_json(text)
            return _coerce(data, fallback)
        except Exception as e:
            logger.warning("llm_service: brand analysis failed, using fallback: %s", e)
            return fallback
