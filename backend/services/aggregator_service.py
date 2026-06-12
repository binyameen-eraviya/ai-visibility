"""Daily aggregator -- rolls a day's parsed answers into the report tables.

The dashboard reads only the aggregate tables (daily_metrics, source_metrics,
gap_scores), so after parsing we recompute a project's metrics for the affected
day. aggregate_daily() is idempotent: it deletes the project's rows for that
day and rewrites them from the parsed mentions / sentiment_scores / sources.

A "chat" = one answer (one scrape run). Scope for daily_metrics is
(project, brand, platform, country, date); platform/country come from the run's
tracking_config, the date from scrape_run.scraped_at (UTC).
"""

import uuid
import logging
from collections import defaultdict, Counter
from dataclasses import dataclass
from datetime import date as date_type

from sqlalchemy import select, delete, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.migrations.answer import Answer as AnswerTable
from backend.database.migrations.scrape_run import ScrapeRun as ScrapeRunTable
from backend.database.migrations.tracking_config import TrackingConfig as TrackingConfigTable
from backend.database.migrations.mention import Mention as MentionTable
from backend.database.migrations.sentiment_score import SentimentScore as SentimentScoreTable
from backend.database.migrations.source import Source as SourceTable
from backend.database.migrations.daily_metric import DailyMetric as DailyMetricTable
from backend.database.migrations.source_metric import SourceMetric as SourceMetricTable
from backend.database.migrations.gap_score import GapScore as GapScoreTable

from backend.database.models.brand import Brand as BrandDB
from backend.database.models.daily_metric import DailyMetric as DailyMetricDB
from backend.database.models.source_metric import SourceMetric as SourceMetricDB
from backend.database.models.gap_score import GapScore as GapScoreDB

logger = logging.getLogger(__name__)


@dataclass
class AggregateResult:
    project_id: uuid.UUID
    date: date_type
    total_chats: int = 0
    daily_metrics_written: int = 0
    source_metrics_written: int = 0
    gap_scores_written: int = 0


def _avg(values):
    return (sum(values) / len(values)) if values else None


async def aggregate_daily(db: AsyncSession, project_id: uuid.UUID, day: date_type) -> AggregateResult:
    """Recompute daily_metrics, source_metrics and gap_scores for one day."""
    result = AggregateResult(project_id=project_id, date=day)

    # Chats: answers for this project whose run was scraped on `day`.
    chat_stmt = (
        select(
            AnswerTable.id,
            AnswerTable.web_search_used,
            TrackingConfigTable.platform_id,
            TrackingConfigTable.country_id,
        )
        .join(ScrapeRunTable, AnswerTable.scrape_run_id == ScrapeRunTable.id)
        .join(TrackingConfigTable, ScrapeRunTable.tracking_config_id == TrackingConfigTable.id)
        .where(
            TrackingConfigTable.project_id == project_id,
            cast(ScrapeRunTable.scraped_at, Date) == day,
        )
    )
    chats = (await db.execute(chat_stmt)).all()

    # Always clear the day first so removed/zeroed metrics don't linger.
    await db.execute(delete(DailyMetricTable).where(
        DailyMetricTable.project_id == project_id, DailyMetricTable.date == day))
    await db.execute(delete(SourceMetricTable).where(
        SourceMetricTable.project_id == project_id, SourceMetricTable.date == day))
    await db.execute(delete(GapScoreTable).where(
        GapScoreTable.project_id == project_id, GapScoreTable.date == day))
    await db.commit()

    if not chats:
        return result
    result.total_chats = len(chats)

    answer_ids = [c.id for c in chats]
    scope_of = {c.id: (c.platform_id, c.country_id) for c in chats}
    web_search_of = {c.id: bool(c.web_search_used) for c in chats}

    # Parsed rows for those answers.
    mentions = (await db.execute(
        select(MentionTable.answer_id, MentionTable.brand_id, MentionTable.mentioned, MentionTable.position)
        .where(MentionTable.answer_id.in_(answer_ids))
    )).all()
    sentiments = (await db.execute(
        select(SentimentScoreTable.answer_id, SentimentScoreTable.brand_id, SentimentScoreTable.score)
        .where(SentimentScoreTable.answer_id.in_(answer_ids))
    )).all()
    sources = (await db.execute(
        select(SourceTable.answer_id, SourceTable.domain, SourceTable.source_type, SourceTable.url_type)
        .where(SourceTable.answer_id.in_(answer_ids))
    )).all()

    brands = await BrandDB.find_by_project(db, project_id)
    primary_ids = {b.id for b in brands if b.is_primary}

    mentions_by_answer = defaultdict(list)
    for m in mentions:
        mentions_by_answer[m.answer_id].append((m.brand_id, m.mentioned, m.position))
    sentiments_by_answer = defaultdict(list)
    for s in sentiments:
        sentiments_by_answer[s.answer_id].append((s.brand_id, s.score))

    # --- daily_metrics, grouped by (platform, country) scope ---------------
    scopes = defaultdict(list)
    for aid in answer_ids:
        scopes[scope_of[aid]].append(aid)

    for (platform_id, country_id), aids in scopes.items():
        total_runs = len(aids)
        web_search_pct = sum(1 for a in aids if web_search_of[a]) / total_runs

        # brand_id -> {mc, positions, sentiments}
        stats = defaultdict(lambda: {"mc": 0, "pos": [], "sent": []})
        for aid in aids:
            for brand_id, mentioned, position in mentions_by_answer.get(aid, []):
                bs = stats[brand_id]
                if mentioned:
                    bs["mc"] += 1
                    if position is not None:
                        bs["pos"].append(position)
            for brand_id, score in sentiments_by_answer.get(aid, []):
                if score is not None:
                    stats[brand_id]["sent"].append(score)

        total_mentions = sum(bs["mc"] for bs in stats.values())
        for brand_id, bs in stats.items():
            mc = bs["mc"]
            await DailyMetricDB.upsert(
                db,
                project_id=project_id,
                brand_id=brand_id,
                platform_id=platform_id,
                country_id=country_id,
                date=day,
                visibility_pct=(mc / total_runs) if total_runs else 0.0,
                share_of_voice=(mc / total_mentions) if total_mentions else 0.0,
                total_runs=total_runs,
                mention_count=mc,
                avg_position=_avg(bs["pos"]),
                avg_sentiment=_avg(bs["sent"]),
                web_search_pct=web_search_pct,
            )
            result.daily_metrics_written += 1

    # --- source_metrics, project-wide for the day -------------------------
    domain_citations = Counter()
    domain_answers = defaultdict(set)
    domain_types = defaultdict(Counter)
    domain_urltypes = defaultdict(Counter)
    total_citations = 0
    for answer_id, domain, source_type, url_type in sources:
        if not domain:
            continue
        domain_citations[domain] += 1
        domain_answers[domain].add(answer_id)
        domain_types[domain][source_type] += 1
        domain_urltypes[domain][url_type] += 1
        total_citations += 1

    for domain, count in domain_citations.items():
        stype = domain_types[domain].most_common(1)[0][0]
        utype = domain_urltypes[domain].most_common(1)[0][0]
        n_chats = len(domain_answers[domain])
        await SourceMetricDB.upsert(
            db,
            project_id=project_id,
            domain=domain,
            date=day,
            citation_count=count,
            source_type=stype,
            url_type=utype,
            retrieved_pct=(count / total_citations) if total_citations else 0.0,
            citation_rate=(count / n_chats) if n_chats else 0.0,
        )
        result.source_metrics_written += 1

    # --- gap_scores: domains that pull competitors when we're absent ------
    # Per chat: competitor mention count + whether our own brand showed up.
    answer_flags = {}
    for aid in answer_ids:
        comp_count = 0
        primary_mentioned = False
        for brand_id, mentioned, _ in mentions_by_answer.get(aid, []):
            if mentioned:
                if brand_id in primary_ids:
                    primary_mentioned = True
                else:
                    comp_count += 1
        answer_flags[aid] = (comp_count, primary_mentioned)

    for domain, aids_set in domain_answers.items():
        gap = 0
        comp_total = 0
        for aid in aids_set:
            comp_count, primary_mentioned = answer_flags.get(aid, (0, False))
            if comp_count > 0 and not primary_mentioned:
                gap += 1
                comp_total += comp_count
        if gap > 0:
            await GapScoreDB.upsert(
                db, project_id=project_id, domain=domain, date=day,
                gap_score=gap, competitor_mentions=comp_total,
            )
            result.gap_scores_written += 1

    logger.info(
        "aggregator: project=%s date=%s chats=%d daily=%d sources=%d gaps=%d",
        project_id, day, result.total_chats, result.daily_metrics_written,
        result.source_metrics_written, result.gap_scores_written,
    )
    return result
