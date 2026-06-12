"""Parser service integration tests (real DB, fake storage + LLM)."""

import pytest_asyncio

from backend.utils.enums import ScrapeStatus, SourceType, UrlType
from backend.services import parser_service
from backend.database.models.brand import Brand
from backend.database.models.tracking_config import TrackingConfig
from backend.database.models.scrape_run import ScrapeRun
from backend.database.models.mention import Mention
from backend.database.models.sentiment_score import SentimentScore
from backend.database.models.source import Source
from backend.database.models.domain_classification import DomainClassification


class FakeStorage:
    def __init__(self, raw):
        self._raw = raw

    async def get_raw(self, path):
        return self._raw


class FakeLLM:
    """Stand-in for GeminiLLMService. has_key toggles the LLM path."""
    def __init__(self, response=None, has_key=True):
        self._response = response
        self._key = has_key
        self.calls = 0

    def _has_key(self):  # mimic GeminiLLMService._has_key
        return self._key

    async def generate_json(self, prompt, temperature=0.3):
        self.calls += 1
        return self._response


@pytest_asyncio.fixture
async def parse_setup(db_session, test_project, test_brand, test_prompt, seed_reference):
    """Acme (primary) + Globex (competitor) and a SUCCESS run with a raw path."""
    competitor = await Brand.create(
        db_session, project_id=test_project.id, name="Globex", is_primary=False,
    )
    config = await TrackingConfig.create(
        db_session,
        project_id=test_project.id,
        prompt_id=test_prompt.id,
        platform_id=seed_reference["platform"].id,
        country_id=seed_reference["country"].id,
    )
    run = await ScrapeRun.create(
        db_session,
        tracking_config_id=config.id,
        status=ScrapeStatus.SUCCESS,
        raw_storage_path="/fake/path.json",
    )
    return {"project": test_project, "primary": test_brand, "competitor": competitor, "run": run}


async def test_parse_full_path_with_llm(db_session, parse_setup):
    run = parse_setup["run"]
    raw = {
        "answer_text": "Acme is the best CRM, and Globex is a solid alternative.",
        "sources": ["https://www.reddit.com/r/crm/abc", "https://obscure-blog.io/best-crm"],
    }
    llm = FakeLLM(response={
        "sentiments": [
            {"brand": "Acme", "sentiment": 88, "reasoning": "best"},
            {"brand": "Globex", "sentiment": 60, "reasoning": "solid alternative"},
        ],
        "domains": [{"domain": "obscure-blog.io", "type": "Editorial"}],
    })

    result = await parser_service.parse_answer(run.id, db_session, storage=FakeStorage(raw), llm=llm)

    assert result.skipped is False
    assert result.answer_id is not None
    assert result.web_search_used is True
    assert result.llm_used is True

    mentions = await Mention.find_by_answer(db_session, result.answer_id)
    assert len(mentions) == 2
    assert all(m.mentioned for m in mentions)  # both brands present in text
    assert result.mentioned_count == 2

    sentiments = await SentimentScore.find_by_answer(db_session, result.answer_id)
    assert len(sentiments) == 2
    assert {s.score for s in sentiments} == {88, 60}

    sources = await Source.find_by_answer(db_session, result.answer_id)
    by_domain = {s.domain: s for s in sources}
    assert by_domain["reddit.com"].source_type == SourceType.UGC
    assert by_domain["obscure-blog.io"].source_type == SourceType.EDITORIAL  # from LLM
    assert by_domain["obscure-blog.io"].url_type == UrlType.LISTICLE  # /best-crm

    # The LLM-resolved domain is cached for next time.
    cached = await DomainClassification.get_many(db_session, ["obscure-blog.io"])
    assert cached["obscure-blog.io"].domain_type == SourceType.EDITORIAL


async def test_parse_without_llm_key_degrades(db_session, parse_setup):
    run = parse_setup["run"]
    raw = {
        "answer_text": "Acme leads the market in CRM tooling.",
        "sources": ["https://unknown-xyz.io/post"],
    }
    llm = FakeLLM(has_key=False)

    result = await parser_service.parse_answer(run.id, db_session, storage=FakeStorage(raw), llm=llm)

    assert result.llm_used is False
    assert llm.calls == 0  # no key -> never called

    mentions = await Mention.find_by_answer(db_session, result.answer_id)
    by_brand = {m.brand_id: m for m in mentions}
    assert by_brand[parse_setup["primary"].id].mentioned is True
    assert by_brand[parse_setup["competitor"].id].mentioned is False

    # No LLM -> no sentiment rows, unknown domain falls back to OTHER.
    assert await SentimentScore.find_by_answer(db_session, result.answer_id) == []
    sources = await Source.find_by_answer(db_session, result.answer_id)
    assert sources[0].source_type == SourceType.OTHER


async def test_parse_is_idempotent(db_session, parse_setup):
    run = parse_setup["run"]
    raw = {"answer_text": "Acme is great.", "sources": []}
    llm = FakeLLM(has_key=False)

    r1 = await parser_service.parse_answer(run.id, db_session, storage=FakeStorage(raw), llm=llm)
    r2 = await parser_service.parse_answer(run.id, db_session, storage=FakeStorage(raw), llm=llm)

    # Re-parsing replaces rather than duplicates.
    assert r1.web_search_used is False
    mentions = await Mention.find_by_answer(db_session, r2.answer_id)
    assert len(mentions) == 2  # one row per brand, not four
