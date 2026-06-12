"""Aggregator integration tests (real DB; parse two chats, then roll up)."""

from datetime import datetime, timezone, date

import pytest_asyncio

from backend.utils.enums import ScrapeStatus, SourceType
from backend.services import parser_service, aggregator_service
from backend.database.models.brand import Brand
from backend.database.models.tracking_config import TrackingConfig
from backend.database.models.scrape_run import ScrapeRun
from backend.database.models.daily_metric import DailyMetric
from backend.database.models.source_metric import SourceMetric
from backend.database.models.gap_score import GapScore

DAY = date(2026, 6, 1)
WHEN = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)


class FakeStorage:
    def __init__(self, raw):
        self._raw = raw

    async def get_raw(self, path):
        return self._raw


class FakeLLM:
    def __init__(self, response):
        self._response = response

    def _has_key(self):
        return True

    async def generate_json(self, prompt, temperature=0.3):
        return self._response


@pytest_asyncio.fixture
async def two_chats(db_session, test_project, test_brand, test_prompt, seed_reference):
    """Acme (primary) + Globex (competitor); two parsed chats on DAY."""
    globex = await Brand.create(db_session, project_id=test_project.id, name="Globex", is_primary=False)
    config = await TrackingConfig.create(
        db_session, project_id=test_project.id, prompt_id=test_prompt.id,
        platform_id=seed_reference["platform"].id, country_id=seed_reference["country"].id,
    )

    async def _run_and_parse(answer_text, sources):
        run = await ScrapeRun.create(
            db_session, tracking_config_id=config.id, status=ScrapeStatus.SUCCESS,
            raw_storage_path="/fake.json", scraped_at=WHEN,
        )
        raw = {"answer_text": answer_text, "sources": sources}
        llm = FakeLLM({
            "sentiments": [
                {"brand": "Acme", "sentiment": 80, "reasoning": "x"},
                {"brand": "Globex", "sentiment": 55, "reasoning": "y"},
            ],
            "domains": [{"domain": "obscure-blog.io", "type": "Editorial"}],
        })
        await parser_service.parse_answer(run.id, db_session, storage=FakeStorage(raw), llm=llm)

    # chat 1: both brands; primary present.
    await _run_and_parse(
        "Acme is the best CRM. Globex is also good.",
        ["https://reddit.com/r/crm/a", "https://obscure-blog.io/best-crm"],
    )
    # chat 2: only competitor; primary absent -> a gap on obscure-blog.io.
    await _run_and_parse(
        "Globex dominates the market for sales teams.",
        ["https://obscure-blog.io/why-globex"],
    )
    return {"project": test_project, "acme": test_brand, "globex": globex}


async def test_aggregate_daily_metrics(db_session, two_chats):
    project = two_chats["project"]
    res = await aggregator_service.aggregate_daily(db_session, project.id, DAY)
    assert res.total_chats == 2

    metrics = await DailyMetric.get_report(db_session, project.id, DAY, DAY)
    by_brand = {m.brand_id: m for m in metrics}
    acme = by_brand[two_chats["acme"].id]
    globex = by_brand[two_chats["globex"].id]

    assert acme.total_runs == 2 and globex.total_runs == 2
    assert acme.visibility_pct == 0.5   # 1 of 2 chats
    assert globex.visibility_pct == 1.0  # 2 of 2 chats
    assert acme.mention_count == 1 and globex.mention_count == 2
    # Share of voice over 3 total mentions.
    assert round(acme.share_of_voice, 3) == round(1 / 3, 3)
    assert round(globex.share_of_voice, 3) == round(2 / 3, 3)
    assert acme.avg_sentiment == 80 and globex.avg_sentiment == 55
    assert acme.web_search_pct == 1.0  # both chats had sources


async def test_aggregate_source_and_gap(db_session, two_chats):
    project = two_chats["project"]
    await aggregator_service.aggregate_daily(db_session, project.id, DAY)

    sources = await SourceMetric.get_report(db_session, project.id, DAY, DAY)
    by_domain = {s.domain: s for s in sources}
    assert by_domain["obscure-blog.io"].citation_count == 2
    assert by_domain["obscure-blog.io"].source_type == SourceType.EDITORIAL
    assert by_domain["obscure-blog.io"].citation_rate == 1.0  # 2 citations / 2 chats
    assert by_domain["reddit.com"].citation_count == 1
    # retrieved_pct over 3 total citations.
    assert round(by_domain["obscure-blog.io"].retrieved_pct, 3) == round(2 / 3, 3)

    gaps = await GapScore.get_report(db_session, project.id, DAY, DAY)
    by_domain = {g.domain: g for g in gaps}
    # Only chat 2 (competitor present, our brand absent) cites obscure-blog.io.
    assert by_domain["obscure-blog.io"].gap_score == 1
    assert by_domain["obscure-blog.io"].competitor_mentions == 1
    # reddit.com only appeared in chat 1 (our brand present) -> no gap row.
    assert "reddit.com" not in by_domain
