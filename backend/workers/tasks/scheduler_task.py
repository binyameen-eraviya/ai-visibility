"""Beat-driven tasks: daily scheduling, quota reset, and old-run cleanup.

Each Celery task is a thin wrapper around a testable async core that takes a db
session (and, for scheduling, an injected enqueue callback + RNG) so the logic
can be unit-tested without a broker.
"""

import uuid
import random
import logging
from datetime import datetime, timezone, timedelta, date

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.workers.celery_app import celery_app
from backend.workers.db import get_task_db, run_async
from backend.utils.enums import TrackingFrequency, ScrapeStatus
from backend.workers.pool.account_pool import AccountPool
from backend.services.storage import LocalStorageService
from backend.database.models.tracking_config import TrackingConfig as TrackingConfigDB
from backend.database.models.scrape_run import ScrapeRun as ScrapeRunDB
from backend.database.migrations.scrape_run import ScrapeRun as ScrapeRunTable
from backend.database.migrations.answer import Answer as AnswerTable
from backend.database.migrations.mention import Mention as MentionTable
from backend.database.migrations.sentiment_score import SentimentScore as SentimentScoreTable
from backend.database.migrations.source import Source as SourceTable

logger = logging.getLogger(__name__)

# Spread daily jobs across this window so we don't fire hundreds at once and
# trip per-platform bot defenses.
SPREAD_SECONDS = 6 * 3600  # 6 hours
RETENTION_DAYS = 90


# --- testable cores ---------------------------------------------------------

async def schedule_runs(db: AsyncSession, *, enqueue, spread_seconds=SPREAD_SECONDS, rand=None) -> int:
    """Create a PENDING run per active DAILY config and enqueue it, staggered.

    enqueue(tracking_config_id: str, scrape_run_id: str, countdown: int) is
    injected so tests can capture calls without a broker. `rand(a, b)` returns a
    random delay in [a, b].
    """
    rand = rand or random.randint
    configs = await TrackingConfigDB.find_active(db, frequency=TrackingFrequency.DAILY)
    count = 0
    for tc in configs:
        run = await ScrapeRunDB.create(db, tracking_config_id=tc.id, status=ScrapeStatus.PENDING)
        countdown = rand(0, spread_seconds)
        enqueue(str(tc.id), str(run.id), countdown)
        count += 1
    return count


async def cleanup_runs(db: AsyncSession, *, storage=None, retention_days=RETENTION_DAYS, now=None) -> int:
    """Delete scrape_runs (and their parsed children + storage) older than N days.

    Aggregated metrics (daily_metrics, source_metrics, gap_scores) are NOT
    touched -- they're the durable record.
    """
    storage = storage or LocalStorageService()
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=retention_days)

    old_runs = (await db.execute(
        select(ScrapeRunTable.id, ScrapeRunTable.raw_storage_path, ScrapeRunTable.screenshot_path)
        .where(ScrapeRunTable.created_at < cutoff)
    )).all()
    if not old_runs:
        return 0
    run_ids = [r.id for r in old_runs]

    answer_ids = [a for (a,) in (await db.execute(
        select(AnswerTable.id).where(AnswerTable.scrape_run_id.in_(run_ids))
    )).all()]

    if answer_ids:
        await db.execute(delete(SourceTable).where(SourceTable.answer_id.in_(answer_ids)))
        await db.execute(delete(MentionTable).where(MentionTable.answer_id.in_(answer_ids)))
        await db.execute(delete(SentimentScoreTable).where(SentimentScoreTable.answer_id.in_(answer_ids)))
        await db.execute(delete(AnswerTable).where(AnswerTable.id.in_(answer_ids)))
    await db.execute(delete(ScrapeRunTable).where(ScrapeRunTable.id.in_(run_ids)))
    await db.commit()

    # Best-effort storage cleanup (after the DB rows are gone).
    for r in old_runs:
        await storage.delete(r.raw_storage_path)
        await storage.delete(r.screenshot_path)

    return len(run_ids)


# --- Celery tasks -----------------------------------------------------------

@celery_app.task(name="backend.workers.tasks.scheduler_task.schedule_daily_runs", queue="aggregate")
def schedule_daily_runs():
    """Beat entrypoint: enqueue today's daily scrape runs, spread over hours."""
    from backend.workers.tasks.scrape_task import run_scrape_task

    def enqueue(tracking_config_id, scrape_run_id, countdown):
        run_scrape_task.apply_async(args=[tracking_config_id, scrape_run_id], countdown=countdown)

    async def _run():
        async with get_task_db() as db:
            return await schedule_runs(db, enqueue=enqueue)

    count = run_async(_run())
    logger.info(
        "Scheduled %d scrape runs for %s, spread across %dh",
        count, date.today(), SPREAD_SECONDS // 3600,
    )
    return {"scheduled": count, "spread_hours": SPREAD_SECONDS // 3600}


@celery_app.task(name="backend.workers.tasks.scheduler_task.reset_account_quotas", queue="aggregate")
def reset_account_quotas():
    """Beat entrypoint: zero every account's daily_quota_used."""
    async def _run():
        async with get_task_db() as db:
            await AccountPool(db).reset_daily_quotas()
    run_async(_run())
    logger.info("Reset daily account quotas")
    return {"status": "reset"}


@celery_app.task(name="backend.workers.tasks.scheduler_task.cleanup_old_runs", queue="aggregate")
def cleanup_old_runs():
    """Beat entrypoint: delete scrape runs + raw storage older than retention."""
    async def _run():
        async with get_task_db() as db:
            return await cleanup_runs(db)
    deleted = run_async(_run())
    logger.info("Cleaned up %d scrape runs older than %d days", deleted, RETENTION_DAYS)
    return {"deleted": deleted}
