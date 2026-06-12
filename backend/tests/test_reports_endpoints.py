"""Report endpoint tests (real app over HTTP; metrics seeded via aggregator)."""

from datetime import datetime, timezone, date

import pytest_asyncio

from backend.utils.enums import ScrapeStatus
from backend.services import parser_service, aggregator_service
from backend.database.models.brand import Brand
from backend.database.models.tracking_config import TrackingConfig
from backend.database.models.scrape_run import ScrapeRun

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
async def seeded(db_session, test_project, test_brand, test_prompt, seed_reference):
    globex = await Brand.create(db_session, project_id=test_project.id, name="Globex", is_primary=False)
    config = await TrackingConfig.create(
        db_session, project_id=test_project.id, prompt_id=test_prompt.id,
        platform_id=seed_reference["platform"].id, country_id=seed_reference["country"].id,
    )

    async def _parse(answer_text, sources):
        run = await ScrapeRun.create(
            db_session, tracking_config_id=config.id, status=ScrapeStatus.SUCCESS,
            raw_storage_path="/fake.json", scraped_at=WHEN,
        )
        llm = FakeLLM({
            "sentiments": [
                {"brand": "Acme", "sentiment": 80, "reasoning": "x"},
                {"brand": "Globex", "sentiment": 55, "reasoning": "y"},
            ],
            "domains": [{"domain": "obscure-blog.io", "type": "Editorial"}],
        })
        await parser_service.parse_answer(
            run.id, db_session, storage=FakeStorage({"answer_text": answer_text, "sources": sources}), llm=llm,
        )

    await _parse("Acme is the best CRM. Globex is also good.",
                 ["https://reddit.com/r/crm/a", "https://obscure-blog.io/best-crm"])
    await _parse("Globex dominates the market for sales teams.",
                 ["https://obscure-blog.io/why-globex"])
    await aggregator_service.aggregate_daily(db_session, test_project.id, DAY)
    return {"project": test_project, "platform": seed_reference["platform"], "globex": globex}


def _params():
    return {"start_date": "2026-06-01", "end_date": "2026-06-01"}


async def test_daily_metrics_returns_web_search_pct(client, auth_headers, seeded):
    pid = seeded["project"].id
    r = await client.get(f"/api/projects/{pid}/reports/daily-metrics", params=_params(), headers=auth_headers)
    assert r.status_code == 200
    rows = r.json()
    assert rows and all("web_search_pct" in row for row in rows)
    assert any(row["mention_count"] == 2 for row in rows)  # Globex


async def test_daily_metrics_group_by_brand(client, auth_headers, seeded):
    pid = seeded["project"].id
    r = await client.get(
        f"/api/projects/{pid}/reports/daily-metrics",
        params={**_params(), "group_by": "brand"}, headers=auth_headers,
    )
    assert r.status_code == 200
    rows = r.json()
    # one bucket per brand, brand_id present, others collapsed
    assert {row["brand_id"] for row in rows} and all(row["brand_id"] for row in rows)


async def test_daily_metrics_group_by_invalid(client, auth_headers, seeded):
    pid = seeded["project"].id
    r = await client.get(
        f"/api/projects/{pid}/reports/daily-metrics",
        params={**_params(), "group_by": "nonsense"}, headers=auth_headers,
    )
    assert r.status_code == 400


async def test_source_metrics_has_new_fields(client, auth_headers, seeded):
    pid = seeded["project"].id
    r = await client.get(f"/api/projects/{pid}/reports/source-metrics", params=_params(), headers=auth_headers)
    assert r.status_code == 200
    rows = {row["domain"]: row for row in r.json()}
    assert rows["obscure-blog.io"]["retrieved_pct"] > 0
    assert rows["obscure-blog.io"]["citation_rate"] == 1.0
    assert "url_type" in rows["obscure-blog.io"]


async def test_gap_analysis_endpoint(client, auth_headers, seeded):
    pid = seeded["project"].id
    r = await client.get(f"/api/projects/{pid}/reports/gap-analysis", params=_params(), headers=auth_headers)
    assert r.status_code == 200
    rows = r.json()
    gap = {row["domain"]: row for row in rows}
    assert gap["obscure-blog.io"]["gap_score"] == 1
    assert gap["obscure-blog.io"]["competitor_mentions"] == 1
    assert "retrieved_pct" in gap["obscure-blog.io"]
    # min_competitors filter excludes it when raised.
    r2 = await client.get(
        f"/api/projects/{pid}/reports/gap-analysis",
        params={**_params(), "min_competitors": 5}, headers=auth_headers,
    )
    assert r2.status_code == 200 and r2.json() == []


async def test_brand_insights_endpoint(client, auth_headers, seeded):
    pid = seeded["project"].id
    r = await client.get(f"/api/projects/{pid}/reports/brand-insights", params=_params(), headers=auth_headers)
    assert r.status_code == 200
    brands = {b["brand_name"]: b for b in r.json()}
    assert "Acme" in brands and "Globex" in brands
    acme = brands["Acme"]
    assert acme["is_primary"] is True
    # Acme tracked on the seeded platform with visibility 0.5
    assert acme["platforms"]
    assert acme["platforms"][0]["visibility_pct"] == 0.5


async def test_reports_cross_tenant_404(client, other_org_headers, seeded):
    pid = seeded["project"].id
    r = await client.get(f"/api/projects/{pid}/reports/gap-analysis", params=_params(), headers=other_org_headers)
    assert r.status_code == 404
