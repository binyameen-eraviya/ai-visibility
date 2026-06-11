"""Manual scrape run, history, and detail.

The manual-run test mocks the adapter at the runner's `get_adapter` seam and
points storage at a tmp dir, exercising the real DB + storage orchestration
without launching Playwright. History/detail seed rows directly (the runner's
internal account-pool rollback would otherwise poison the shared test session
before a second request).
"""

import uuid

import pytest

from backend.workers.scrapers.base_adapter import RawAnswer


class _FakeAdapter:
    async def run_prompt(self, prompt_text, account=None, proxy=None):
        return RawAnswer(
            answer_text="Acme is a top choice.",
            sources=["https://review.test/acme"],
            metadata={"model": "fake-1"},
        )


@pytest.fixture
def mock_adapter(monkeypatch, tmp_path):
    # Route the runner's adapter lookup to the fake, and storage to tmp.
    monkeypatch.setattr(
        "backend.services.scrape_runner.get_adapter",
        lambda platform_name: _FakeAdapter(),
    )
    monkeypatch.setenv("SCRAPE_STORAGE_DIR", str(tmp_path))
    return tmp_path


async def _make_tracking_config(db_session, project, prompt, seed_reference):
    from backend.database.models.tracking_config import TrackingConfig
    return await TrackingConfig.create(
        db_session,
        project_id=project.id,
        prompt_id=prompt.id,
        platform_id=seed_reference["platform"].id,
        country_id=seed_reference["country"].id,
    )


async def test_manual_run_creates_scrape_run_record(
    client, auth_headers, test_project, test_prompt, seed_reference, mock_adapter
):
    resp = await client.post(
        f"/api/projects/{test_project.id}/prompts/{test_prompt.id}/run",
        headers=auth_headers,
        json={"platform_id": str(seed_reference["platform"].id)},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "SUCCESS"
    assert body["id"]


async def test_run_history_returns_runs(
    client, auth_headers, db_session, test_project, test_prompt, seed_reference
):
    from backend.database.models.scrape_run import ScrapeRun
    from backend.utils.enums import ScrapeStatus
    tc = await _make_tracking_config(db_session, test_project, test_prompt, seed_reference)
    await ScrapeRun.create(
        db_session, tracking_config_id=tc.id, status=ScrapeStatus.SUCCESS
    )
    resp = await client.get(
        f"/api/projects/{test_project.id}/runs", headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    assert len(resp.json()) >= 1


async def test_run_detail_returns_stored_data(
    client, auth_headers, db_session, test_project, test_prompt, seed_reference, tmp_path
):
    from backend.database.models.scrape_run import ScrapeRun
    from backend.services.storage import LocalStorageService
    from backend.utils.enums import ScrapeStatus
    tc = await _make_tracking_config(db_session, test_project, test_prompt, seed_reference)
    # Write a raw capture to disk, then point a run row at its absolute path.
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
