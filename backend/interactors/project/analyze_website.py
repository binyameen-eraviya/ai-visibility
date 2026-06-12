"""Analyze a website and return brand/competitor/prompt suggestions.

Orchestrates the website analyzer + LLM service. Saves nothing -- the frontend
uses the suggestions to pre-fill the onboarding forms. Degrades gracefully:
unreachable site -> 400; LLM failure -> partial results from the fallback.
"""

import logging
from urllib.parse import urlparse

from fastapi import HTTPException, status

from backend.utils.schema.request import AnalyzeWebsiteRequest
from backend.utils.schema.response import (
    WebsiteAnalysisResponse,
    CompetitorSuggestion,
    PromptSuggestion,
)
from backend.services.website_analyzer import (
    analyze_website,
    normalize_url,
    WebsiteUnreachableError,
)
from backend.services.llm_service import GeminiLLMService

logger = logging.getLogger(__name__)


def favicon_url(domain: str, size: int = 64) -> str:
    """Google's favicon service URL for a bare domain ('' if no domain)."""
    domain = (domain or "").strip().lower()
    if not domain:
        return ""
    return f"https://www.google.com/s2/favicons?domain={domain}&sz={size}"


def _domain_of(url: str) -> str:
    try:
        host = (urlparse(url).hostname or "").lower()
    except Exception:
        return ""
    return host[4:] if host.startswith("www.") else host


async def call(payload: AnalyzeWebsiteRequest, current_user) -> WebsiteAnalysisResponse:
    url = normalize_url(payload.url)
    if not url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A website URL is required.",
        )

    try:
        website = await analyze_website(url)
    except WebsiteUnreachableError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="We couldn't reach that website. Check the URL and try again.",
        )
    except Exception as e:
        logger.warning("analyze_website: unexpected failure for %s: %s", url, e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Something went wrong analyzing that website.",
        )

    # LLM failures are non-fatal: analyze_brand returns a fallback internally.
    suggestions = await GeminiLLMService().analyze_brand(website)

    return WebsiteAnalysisResponse(
        brand_name=suggestions.brand_name,
        brand_aliases=suggestions.brand_aliases,
        brand_description=suggestions.brand_description,
        industry=suggestions.industry,
        location=suggestions.location,
        company_scale=suggestions.company_scale,
        brand_identity=suggestions.brand_identity,
        products_services=suggestions.products_services,
        competitors=[
            CompetitorSuggestion(
                name=c.get("name", ""),
                domain=c.get("domain", ""),
                reason=c.get("reason", ""),
            )
            for c in suggestions.competitors
            if c.get("name")
        ],
        suggested_topics=suggestions.suggested_topics,
        suggested_prompts=[
            PromptSuggestion(topic=p.get("topic", ""), text=p.get("text", ""))
            for p in suggestions.suggested_prompts
            if p.get("text")
        ],
        favicon_url=favicon_url(_domain_of(url)),
    )
