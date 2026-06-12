"""Parser service -- turns one raw scrape capture into structured analytics.

Loads a successful scrape run's stored answer, runs the three parsers (brand
mentions, sentiment, sources), and writes mentions / sentiment_scores /
sources rows plus the answer itself.

LLM economy (Part J): the LLM is used at most ONCE per answer. Deterministic
work runs first -- string mention matching, known-domain lookup -- and only the
genuinely uncertain pieces (fuzzy mentions when string matching found nothing,
sentiment, and unknown-domain classification) are folded into a single batched
Gemini call. Known/cached domains never reach the LLM; resolved unknowns are
cached in domain_classifications so they never reach it again.

Degrades gracefully: a missing/empty capture or an unavailable LLM yields a
partial (or empty-sentiment) result rather than raising into the scrape flow.
"""

import re
import uuid
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.enums import ScrapeStatus, SourceType, DomainClassifier
from backend.services.storage import BaseStorageService, LocalStorageService
from backend.services.llm_service import GeminiLLMService
from backend.services.parsers import mention_detector as md
from backend.services.parsers import sentiment_analyzer as sa
from backend.services.parsers import source_extractor as se

from backend.database.models.scrape_run import ScrapeRun as ScrapeRunDB
from backend.database.models.tracking_config import TrackingConfig as TrackingConfigDB
from backend.database.models.project import Project as ProjectDB
from backend.database.models.brand import Brand as BrandDB
from backend.database.models.answer import Answer as AnswerDB
from backend.database.models.mention import Mention as MentionDB
from backend.database.models.sentiment_score import SentimentScore as SentimentScoreDB
from backend.database.models.source import Source as SourceDB
from backend.database.models.domain_classification import DomainClassification as DomainClassificationDB

from backend.database.migrations.answer import Answer as AnswerTable
from backend.database.migrations.mention import Mention as MentionTable
from backend.database.migrations.sentiment_score import SentimentScore as SentimentScoreTable
from backend.database.migrations.source import Source as SourceTable

logger = logging.getLogger(__name__)


@dataclass
class ParseResult:
    scrape_run_id: uuid.UUID
    project_id: uuid.UUID = None
    answer_id: uuid.UUID = None
    mentions_total: int = 0       # rows written (true + false)
    mentioned_count: int = 0      # brands actually mentioned
    sentiment_count: int = 0
    sources_count: int = 0
    web_search_used: bool = False
    llm_used: bool = False
    skipped: bool = False
    reason: str = ""


def _competitor_keys(brands: list) -> set:
    """Normalized name tokens for competitor brands (for domain brand-matching)."""
    keys = set()
    for b in brands:
        if getattr(b, "is_primary", False):
            continue
        for term in [b.name] + (b.aliases or []):
            token = re.sub(r"[^a-z0-9]", "", str(term).lower())
            if len(token) >= 3:
                keys.add(token)
    return keys


def _build_combined_prompt(answer_text, brands, *, need_fuzzy, need_sentiment, unknown_domains) -> str:
    """One prompt with only the sections that are actually needed."""
    sections = []
    if need_fuzzy:
        sections.append(md.build_fuzzy_prompt_fragment(brands))
    if need_sentiment:
        sections.append(sa.build_sentiment_prompt_fragment(brands))
    if unknown_domains:
        sections.append(se.build_domain_prompt_fragment(unknown_domains))

    keys = []
    if need_fuzzy:
        keys.append('"mentions": [{"brand_name": str, "mentioned": bool, "position": int|null, "context_snippet": str|null}]')
    if need_sentiment:
        keys.append('"sentiments": [{"brand": str, "sentiment": int|null, "reasoning": str}]')
    if unknown_domains:
        keys.append('"domains": [{"domain": str, "type": "Corporate|UGC|Reference|Editorial|Review Site|Institutional|Other"}]')

    schema = "{\n  " + ",\n  ".join(keys) + "\n}"
    return (
        "You are analyzing one AI-generated answer to extract structured signals.\n"
        "Complete every task below for the SAME answer and return ONE JSON object.\n\n"
        + "\n\n".join(sections)
        + f"\n\nAI answer:\n{answer_text}\n\n"
        "Return ONLY valid JSON (no markdown, no backticks) with this exact shape:\n"
        + schema
    )


async def _clear_existing(db: AsyncSession, scrape_run_id: uuid.UUID) -> None:
    """Remove any prior parse for this run so re-parsing is idempotent."""
    try:
        answer = await AnswerDB.find_by_scrape_run(db, scrape_run_id)
    except Exception:
        return  # nothing parsed yet
    aid = answer.id
    await db.execute(delete(SourceTable).where(SourceTable.answer_id == aid))
    await db.execute(delete(MentionTable).where(MentionTable.answer_id == aid))
    await db.execute(delete(SentimentScoreTable).where(SentimentScoreTable.answer_id == aid))
    await db.execute(delete(AnswerTable).where(AnswerTable.id == aid))
    await db.commit()


async def parse_answer(
    scrape_run_id: uuid.UUID,
    db: AsyncSession,
    storage: BaseStorageService = None,
    llm: GeminiLLMService = None,
) -> ParseResult:
    """Parse one successful scrape run into mentions / sentiment / sources."""
    storage = storage or LocalStorageService()
    llm = llm or GeminiLLMService()
    result = ParseResult(scrape_run_id=scrape_run_id)

    run = await ScrapeRunDB.find_by_id(db, scrape_run_id)
    if run.status != ScrapeStatus.SUCCESS or not run.raw_storage_path:
        result.skipped = True
        result.reason = f"run not parseable (status={run.status}, path={bool(run.raw_storage_path)})"
        return result

    # Resolve project + brands.
    config = await TrackingConfigDB.find_by_id(db, run.tracking_config_id)
    project_id = config.project_id
    result.project_id = project_id
    project = await ProjectDB.find_by_id(db, project_id)
    own_domain = se.domain_of(project.website_url) if project.website_url else None
    brands = await BrandDB.find_by_project(db, project_id)
    if not brands:
        result.skipped = True
        result.reason = "no brands configured for project"
        return result

    # Load the raw capture.
    raw = await storage.get_raw(run.raw_storage_path)
    answer_text = (raw or {}).get("answer_text") or ""

    # Deterministic passes.
    pass1 = md.detect_mentions(answer_text, brands)
    comp_keys = _competitor_keys(brands)
    cache_rows = await DomainClassificationDB.get_many(
        db, list({se.domain_of(u) for u in se.extract_urls(raw or {})})
    )
    cache = {d: row.domain_type for d, row in cache_rows.items()}
    sources = se.build_sources(raw or {}, own_domain=own_domain, competitor_keys=comp_keys, cache=cache)

    result.web_search_used = len(sources) > 0
    unknown_domains = sorted({s.domain for s in sources if s.source_type is None and s.domain})

    # Decide what (if anything) the LLM must do -- single batched call.
    need_fuzzy = md.needs_llm_fallback(answer_text, pass1)
    any_mentioned = any(r.mentioned for r in pass1)
    need_sentiment = bool(brands) and (any_mentioned or need_fuzzy)
    mentions = pass1
    sentiments = sa.parse_sentiment([], brands)  # all-None default

    if llm._has_key() and (need_fuzzy or need_sentiment or unknown_domains):
        prompt = _build_combined_prompt(
            answer_text, brands,
            need_fuzzy=need_fuzzy, need_sentiment=need_sentiment, unknown_domains=unknown_domains,
        )
        data = await llm.generate_json(prompt)
        if isinstance(data, dict):
            result.llm_used = True
            if need_fuzzy and isinstance(data.get("mentions"), list):
                mentions = md.parse_fuzzy_mentions(data["mentions"], brands)
            if need_sentiment and isinstance(data.get("sentiments"), list):
                sentiments = sa.parse_sentiment(data["sentiments"], brands)
            if unknown_domains and isinstance(data.get("domains"), list):
                resolved = se.parse_domain_classifications(data["domains"])
                for s in sources:
                    if s.source_type is None:
                        s.source_type = resolved.get(s.domain, SourceType.OTHER)
                        s.classified_by = DomainClassifier.LLM
                # Cache resolved domains so we never re-ask.
                for domain, stype in resolved.items():
                    try:
                        await DomainClassificationDB.upsert(
                            db, domain=domain, domain_type=stype, classified_by=DomainClassifier.LLM,
                        )
                    except Exception as e:
                        logger.warning("parser: failed to cache domain %s: %s", domain, e)

    # Any domain still unresolved (LLM unavailable) defaults to OTHER.
    for s in sources:
        if s.source_type is None:
            s.source_type = SourceType.OTHER

    # Persist: clear any prior parse, then write the answer + children.
    await _clear_existing(db, scrape_run_id)
    answer = await AnswerDB.create(
        db,
        scrape_run_id=scrape_run_id,
        answer_text=answer_text,
        parsed_at=datetime.now(timezone.utc),
        web_search_used=result.web_search_used,
    )
    result.answer_id = answer.id

    mentioned_ids = set()
    for m in mentions:
        await MentionDB.create(
            db, answer_id=answer.id, brand_id=m.brand_id,
            mentioned=m.mentioned, position=m.position, context_snippet=m.context_snippet,
        )
        if m.mentioned:
            mentioned_ids.add(m.brand_id)
    result.mentions_total = len(mentions)
    result.mentioned_count = len(mentioned_ids)

    for s in sentiments:
        # Score only brands that were actually mentioned and got a score.
        if s.score is not None and s.brand_id in mentioned_ids:
            await SentimentScoreDB.create(
                db, answer_id=answer.id, brand_id=s.brand_id, score=s.score, reasoning=s.reasoning,
            )
            result.sentiment_count += 1

    for s in sources:
        await SourceDB.create(
            db, answer_id=answer.id, url=s.url, domain=s.domain,
            source_type=s.source_type, url_type=s.url_type, position=s.position,
        )
    result.sources_count = len(sources)

    logger.info(
        "parser: run=%s parsed answer=%s mentions=%d/%d sentiment=%d sources=%d web_search=%s llm=%s",
        scrape_run_id, answer.id, result.mentioned_count, result.mentions_total,
        result.sentiment_count, result.sources_count, result.web_search_used, result.llm_used,
    )
    return result
