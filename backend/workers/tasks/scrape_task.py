"""scrape task: drive one scrape run, then chain to parse on success."""

import logging

from celery.exceptions import MaxRetriesExceededError, SoftTimeLimitExceeded

from backend.workers.celery_app import celery_app
from backend.workers.db import get_task_db, run_async
from backend.services.scrape_runner import execute_scrape_run, mark_run_failed

logger = logging.getLogger(__name__)


async def _execute(scrape_run_id: str):
    async with get_task_db() as db:
        return await execute_scrape_run(db, scrape_run_id)


async def _fail(scrape_run_id: str, error: str):
    async with get_task_db() as db:
        await mark_run_failed(db, scrape_run_id, error)


@celery_app.task(
    bind=True,
    name="backend.workers.tasks.scrape_task.run_scrape_task",
    queue="scrape",
    rate_limit="3/m",        # browser scraping is heavy + platforms rate-limit
    max_retries=3,
    default_retry_delay=60,  # 1 min between retries
    soft_time_limit=120,     # 2 min soft limit
    time_limit=180,          # 3 min hard kill
    acks_late=True,          # only ack after success (crashed tasks re-run)
)
def run_scrape_task(self, tracking_config_id: str, scrape_run_id: str):
    """Execute a PENDING scrape run; chain parse on success, retry on transient."""
    try:
        outcome = run_async(_execute(scrape_run_id))
    except SoftTimeLimitExceeded:
        logger.warning("scrape task %s hit soft time limit; retrying", scrape_run_id)
        raise self.retry(countdown=self.default_retry_delay)

    if outcome.status == "RETRY":
        try:
            raise self.retry(countdown=self.default_retry_delay, exc=Exception(outcome.error or "scrape retry"))
        except MaxRetriesExceededError:
            logger.error("scrape run %s: retries exhausted -> FAILED", scrape_run_id)
            run_async(_fail(scrape_run_id, outcome.error or "max retries exceeded"))
            return {"status": "FAILED", "scrape_run_id": scrape_run_id}

    if outcome.status == "SUCCESS":
        # Chain: parse this answer (which then chains aggregate).
        from backend.workers.tasks.parse_task import run_parse_task
        run_parse_task.delay(scrape_run_id=str(scrape_run_id))

    return {"status": outcome.status, "scrape_run_id": scrape_run_id}
