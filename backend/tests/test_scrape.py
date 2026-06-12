"""Manual scrape run (now async via Celery), history, detail, and the
execute_scrape_run core used by the worker task.

The manual-run endpoint no longer blocks: it creates a PENDING run and enqueues
a Celery task (stubbed here). The core scrape logic is exercised directly against
the test DB with a fake adapter -- no Playwright, no broker.
"""

import uuid

import pytest

from backend.utils.enums import ScrapeStatus
from backend.services import scrape_runner
from backend.services.scrape_runner import execute_scrape_run
from backend.services.storage import LocalStorageService
from backend.workers.scrapers.base_adapter import RawAnswer
from backend.workers.scrapers.exceptions import RateLimited, CaptchaDetected
from backend.database.models.scrape_run import ScrapeRun
from backend.database.models.scrape_account import ScrapeAccount
from backend.database.models.tracking_config import TrackingConfig


class _FakeAdapter:
    async def run_prompt(self, prompt_text, account=None, proxy=None):
        return RawAnswer(
            answer_text="Acme is a top choice.",
            sources=["https://review.test/acme"],
            metadata={"model": "fake-1"},
        )


class _RateLimitedAdapter:
    async def run_prompt(self, prompt_text, account=None, proxy=None):
        raise RateLimited("too many requests", platform="perplexity")


class _CaptchaAdapter:
    async def run_prompt(self, prompt_text, account=None, proxy=None):
        raise CaptchaDetected("bot challenge", platform="perplexity")


async def _make_tracking_config(db_session, project, prompt, seed_reference):
    return await TrackingConfig.create(
        db_session,
        project_id=project.id,
        prompt_id=prompt.id,
        platform_id=seed_reference["platform"].id,
        country_id=seed_reference["country"].id,
    )


async def _seed_account(db_session, seed_reference):
    # Seed an ACTIVE account so checkout succeeds; an empty pool makes checkout
    # roll back the savepoint-isolated test session, poisoning it for the reload.
    return await ScrapeAccount.create(
        db_session, platform_id=seed_reference["platform"].id, email="bot@test.local",
    )


async def test_manual_run_returns_pending_and_enqueues(
    client, auth_headers, test_project, test_prompt, seed_reference, monkeypatch
):
    # Stub the Celery enqueue so the endpoint doesn't touch a real broker.
    calls = {}
    from backend.workers.tasks import scrape_task
    monkeypatch.setattr(
        scrape_task.run_scrape_task, "delay",
        lambda **kw: calls.update(kw),
    )

    resp = await client.post(
        f"/api/projects/{test_project.id}/prompts/{test_prompt.id}/run",
        headers=auth_headers,
        json={"platform_id": str(seed_reference["platform"].id)},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "PENDING"  # async now -- not SUCCESS
    assert body["id"]
    # The task was enqueued with this run's id.
    assert calls.get("scrape_run_id") == body["id"]


async def test_execute_scrape_run_success(
    db_session, test_project, test_prompt, seed_reference, tmp_path, monkeypatch
):
    monkeypatch.setattr(scrape_runner, "get_adapter", lambda name: _FakeAdapter())
    await _seed_account(db_session, seed_reference)
    tc = await _make_tracking_config(db_session, test_project, test_prompt, seed_reference)
    run = await ScrapeRun.create(db_session, tracking_config_id=tc.id, status=ScrapeStatus.PENDING)

    storage = LocalStorageService(storage_dir=str(tmp_path))
    outcome = await execute_scrape_run(db_session, run.id, storage=storage)

    assert outcome.status == "SUCCESS"
    assert outcome.project_id == test_project.id
    reloaded = await ScrapeRun.find_by_id(db_session, run.id)
    assert reloaded.status == ScrapeStatus.SUCCESS
    assert reloaded.raw_storage_path


async def test_execute_scrape_run_retry_on_rate_limit(
    db_session, test_project, test_prompt, seed_reference, tmp_path, monkeypatch
):
    monkeypatch.setattr(scrape_runner, "get_adapter", lambda name: _RateLimitedAdapter())
    await _seed_account(db_session, seed_reference)
    tc = await _make_tracking_config(db_session, test_project, test_prompt, seed_reference)
    run = await ScrapeRun.create(db_session, tracking_config_id=tc.id, status=ScrapeStatus.PENDING)

    outcome = await execute_scrape_run(db_session, run.id, storage=LocalStorageService(storage_dir=str(tmp_path)))

    assert outcome.status == "RETRY" and outcome.retryable is True
    reloaded = await ScrapeRun.find_by_id(db_session, run.id)
    assert reloaded.status == ScrapeStatus.RETRYING


async def test_execute_scrape_run_captcha_fails_no_retry(
    db_session, test_project, test_prompt, seed_reference, tmp_path, monkeypatch
):
    monkeypatch.setattr(scrape_runner, "get_adapter", lambda name: _CaptchaAdapter())
    await _seed_account(db_session, seed_reference)
    tc = await _make_tracking_config(db_session, test_project, test_prompt, seed_reference)
    run = await ScrapeRun.create(db_session, tracking_config_id=tc.id, status=ScrapeStatus.PENDING)

    outcome = await execute_scrape_run(db_session, run.id, storage=LocalStorageService(storage_dir=str(tmp_path)))

    assert outcome.status == "FAILED" and outcome.retryable is False
    reloaded = await ScrapeRun.find_by_id(db_session, run.id)
    assert reloaded.status == ScrapeStatus.FAILED


async def test_run_history_returns_runs(
    client, auth_headers, db_session, test_project, test_prompt, seed_reference
):
    tc = await _make_tracking_config(db_session, test_project, test_prompt, seed_reference)
    await ScrapeRun.create(db_session, tracking_config_id=tc.id, status=ScrapeStatus.SUCCESS)
    resp = await client.get(f"/api/projects/{test_project.id}/runs", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert len(resp.json()) >= 1


async def test_run_detail_returns_stored_data(
    client, auth_headers, db_session, test_project, test_prompt, seed_reference, tmp_path
):
    tc = await _make_tracking_config(db_session, test_project, test_prompt, seed_reference)
    storage = LocalStorageService(storage_dir=str(tmp_path))
    raw_path = await storage.save_raw(
        test_project.id, uuid.uuid4(),
        {"answer_text": "Acme is a top choice.", "sources": []},
    )
    run = await ScrapeRun.create(
        db_session, tracking_config_id=tc.id,
        status=ScrapeStatus.SUCCESS, raw_storage_path=raw_path,
    )
    resp = await client.get(
        f"/api/projects/{test_project.id}/runs/{run.id}", headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["raw"]["answer_text"] == "Acme is a top choice."
