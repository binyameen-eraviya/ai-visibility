"""Sentiment analysis (per brand, per answer).

Sentiment needs the LLM. This module exposes the prompt fragment + result
parser so the orchestrator can fold sentiment into its single batched Gemini
call, plus a standalone analyze_sentiment() for isolated use/tests.

Scores are 0..100 (0 = strongly negative, 100 = strongly positive); a brand
that isn't mentioned gets score=None and no row is written for it.
"""

from dataclasses import dataclass

_RUBRIC = (
    "SENTIMENT: Score the sentiment toward each brand from 0 to 100 based on how "
    "the answer talks about it:\n"
    "- 0-20: Very negative (criticized, warned against)\n"
    "- 21-40: Somewhat negative (mentioned limitations, caveats)\n"
    "- 41-60: Neutral (just listed, no opinion)\n"
    "- 61-80: Somewhat positive (recommended with caveats)\n"
    "- 81-100: Very positive (strongly recommended, praised)\n"
    "If a brand is not mentioned in the answer, return null for its sentiment."
)


@dataclass
class SentimentResult:
    brand_id: object
    brand_name: str
    score: int = None       # 0..100, or None if not mentioned / unscored
    reasoning: str = None


def build_sentiment_prompt_fragment(brands: list) -> str:
    """Scoring rubric + brand list for the batched LLM call's sentiment section."""
    names = ", ".join(b.name for b in brands if getattr(b, "name", None))
    return f"{_RUBRIC}\nBrands to score: {names}"


def parse_sentiment(llm_scores, brands: list) -> list:
    """Map the LLM sentiment list onto a SentimentResult per brand.

    Accepts items shaped like {"brand": name, "sentiment": int|null,
    "reasoning": str}. Scores are clamped to 0..100; null/missing -> None.
    """
    by_name = {}
    for s in llm_scores or []:
        if isinstance(s, dict):
            name = s.get("brand") or s.get("brand_name")
            if name:
                by_name[str(name).strip().lower()] = s

    results = []
    for brand in brands:
        s = by_name.get((brand.name or "").strip().lower())
        score = None
        reasoning = None
        if s is not None:
            raw = s.get("sentiment")
            if raw is None:
                raw = s.get("score")
            if raw is not None:
                try:
                    score = max(0, min(100, int(round(float(raw)))))
                except (TypeError, ValueError):
                    score = None
            r = s.get("reasoning")
            reasoning = str(r).strip()[:500] if r else None
        results.append(SentimentResult(
            brand_id=brand.id,
            brand_name=brand.name,
            score=score,
            reasoning=reasoning,
        ))
    return results


def _standalone_prompt(answer_text: str, brands: list) -> str:
    names = ", ".join(b.name for b in brands if getattr(b, "name", None))
    return (
        "Analyze the sentiment toward each brand mentioned in this AI-generated "
        "answer.\n"
        f"{_RUBRIC}\n\n"
        f"Brands to check: {names}\n\n"
        f"AI answer:\n{answer_text}\n\n"
        'Return ONLY valid JSON, no markdown:\n'
        '[{"brand": "BrandName", "sentiment": 72, "reasoning": "Brief explanation"}]'
    )


async def analyze_sentiment(answer_text: str, brands: list, llm) -> list:
    """Standalone single-call sentiment scoring (used when not batched)."""
    if not brands:
        return []
    data = await llm.generate_json(_standalone_prompt(answer_text, brands))
    if isinstance(data, dict):
        # Tolerate {"sentiments": [...]} or {"results": [...]} wrappers.
        for key in ("sentiments", "results", "data"):
            if isinstance(data.get(key), list):
                data = data[key]
                break
    return parse_sentiment(data if isinstance(data, list) else [], brands)
