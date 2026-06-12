"""parse task: parse one answer, then chain to aggregate."""

import uuid
import logging
from datetime import datetime, timezone

from celery.exceptions import MaxRetriesExceededError

from backend.workers.celery_app import celery_app
from backend.workers.db import get_task_db, run_async
from backend.services.parser_service import parse_answer
from backend.database.models.scrape_run import ScrapeRun as ScrapeRunDB

logger = logging.getLogger(__name__)


async def _parse(scrape_run_id: str):
    async with get_task_db() as db:
        result = await parse_answer(uuid.UUID(scrape_run_id), db)
        run = await ScrapeRunDB.find_by_id(db, uuid.UUID(scrape_run_id))
        scraped_date = (run.scraped_at or datetime.now(timezone.utc)).date()
        return result, scraped_date


@celery_app.task(
    bind=True,
    name="backend.workers.tasks.parse_task.run_parse_task",
    queue="parse",
    rate_limit="10/m",
    max_retries=2,
    default_retry_delay=30,
    soft_time_limit=60,
    time_limit=90,
    acks_late=True,
)
def run_parse_task(self, scrape_run_id: str):
    """Parse a successful run; retry on LLM unavailability, then chain aggregate."""
    result, scraped_date = run_async(_parse(scrape_run_id))

    if result.skipped:
        logger.info("parse task %s skipped: %s", scrape_run_id, result.reason)
        return {"status": "skipped", "reason": result.reason}

    # The LLM was needed (sentiment / fuzzy / unknown domains) but unavailable.
    # Parsing is idempotent, so retry to fill those fields in once it recovers.
    if result.llm_unavailable:
        try:
            raise self.retry(countdown=self.default_retry_delay)
        except MaxRetriesExceededError:
            logger.warning("parse task %s: LLM still unavailable; keeping partial parse", scrape_run_id)

    if result.project_id:
        from backend.workers.tasks.aggregate_task import run_aggregate_task
        run_aggregate_task.delay(project_id=str(result.project_id), date_str=str(scraped_date))

    return {
        "status": "parsed",
        "scrape_run_id": scrape_run_id,
        "mentioned": result.mentioned_count,
        "sources": result.sources_count,
    }
