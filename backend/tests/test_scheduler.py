"""Scheduler / cleanup task-core tests (real DB, no broker)."""

from datetime import datetime, timezone, timedelta

import pytest_asyncio
from sqlalchemy import update, select, func

from backend.utils.enums import ScrapeStatus
from backend.workers.tasks import scheduler_task
from backend.workers.pool.account_pool import AccountPool
from backend.database.models.tracking_config import TrackingConfig
from backend.database.models.scrape_run import ScrapeRun
from backend.database.models.scrape_account import ScrapeAccount
from backend.database.migrations.scrape_run import ScrapeRun as ScrapeRunTable
from backend.database.migrations.scrape_account import ScrapeAccount as ScrapeAccountTable


@pytest_asyncio.fixture
async def tracking(db_session, test_project, test_prompt, seed_reference):
    return await TrackingConfig.create(
        db_session, project_id=test_project.id, prompt_id=test_prompt.id,
        platform_id=seed_reference["platform"].id, country_id=seed_reference["country"].id,
    )


async def test_schedule_runs_creates_pending_and_enqueues(db_session, tracking):
    calls = []

    def enqueue(tc_id, run_id, countdown):
        calls.append((tc_id, run_id, countdown))

    # Deterministic "random": always the midpoint.
    count = await scheduler_task.schedule_runs(
        db_session, enqueue=enqueue, spread_seconds=21600, rand=lambda a, b: (a + b) // 2,
    )
    assert count == 1
    assert len(calls) == 1
    tc_id, run_id, countdown = calls[0]
    assert tc_id == str(tracking.id)
    assert 0 <= countdown <= 21600
    # A PENDING run row was created for it.
    run = await ScrapeRun.find_by_id(db_session, run_id)
    assert run.status == ScrapeStatus.PENDING


async def test_schedule_runs_skips_inactive(db_session, tracking):
    # Deactivate the only config -> nothing scheduled.
    await TrackingConfig.toggle_active(db_session, tracking.id)
    calls = []
    count = await scheduler_task.schedule_runs(db_session, enqueue=lambda *a: calls.append(a))
    assert count == 0 and calls == []


async def test_reset_account_quotas(db_session, seed_reference):
    acct = await ScrapeAccount.create(
        db_session, platform_id=seed_reference["platform"].id, email="bot@test.local",
    )
    # Bump usage, then reset.
    await db_session.execute(update(ScrapeAccountTable).values(daily_quota_used=7))
    await db_session.commit()
    await AccountPool(db_session).reset_daily_quotas()
    refreshed = await ScrapeAccount.find_by_id(db_session, acct.id)
    assert refreshed.daily_quota_used == 0


async def test_cleanup_runs_deletes_old_keeps_recent(db_session, tracking):
    # One old run (backdated 100 days) and one fresh run.
    old = await ScrapeRun.create(db_session, tracking_config_id=tracking.id, status=ScrapeStatus.SUCCESS)
    fresh = await ScrapeRun.create(db_session, tracking_config_id=tracking.id, status=ScrapeStatus.SUCCESS)
    await db_session.execute(
        update(ScrapeRunTable).where(ScrapeRunTable.id == old.id)
        .values(created_at=datetime.now(timezone.utc) - timedelta(days=100))
    )
    await db_session.commit()

    class _NoopStorage:
        async def delete(self, path):
            return False

    deleted = await scheduler_task.cleanup_runs(
        db_session, storage=_NoopStorage(), retention_days=90,
    )
    assert deleted == 1
    # Old gone, fresh kept.
    remaining = (await db_session.execute(select(func.count()).select_from(ScrapeRunTable))).scalar()
    assert remaining == 1
    survivor = await ScrapeRun.find_by_id(db_session, fresh.id)
    assert survivor.id == fresh.id
