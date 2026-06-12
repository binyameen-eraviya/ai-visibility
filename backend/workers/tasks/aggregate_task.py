"""aggregate task: roll up one project's metrics for a day (idempotent)."""

import uuid
import logging
from datetime import date

from backend.workers.celery_app import celery_app
from backend.workers.db import get_task_db, run_async
from backend.services.aggregator_service import aggregate_daily

logger = logging.getLogger(__name__)


async def _aggregate(project_id: str, date_str: str):
    async with get_task_db() as db:
        return await aggregate_daily(db, uuid.UUID(project_id), date.fromisoformat(date_str))


@celery_app.task(
    name="backend.workers.tasks.aggregate_task.run_aggregate_task",
    queue="aggregate",
    soft_time_limit=120,
    time_limit=180,
)
def run_aggregate_task(project_id: str, date_str: str):
    """Recompute daily_metrics/source_metrics/gap_scores for a project + day.

    Idempotent (the aggregator clears the day and upserts), so re-running is safe.
    """
    result = run_async(_aggregate(project_id, date_str))
    logger.info(
        "aggregate task: project=%s date=%s daily=%d sources=%d gaps=%d",
        project_id, date_str, result.daily_metrics_written,
        result.source_metrics_written, result.gap_scores_written,
    )
    return {
        "status": "aggregated",
        "project_id": project_id,
        "date": date_str,
        "daily_metrics": result.daily_metrics_written,
        "source_metrics": result.source_metrics_written,
        "gap_scores": result.gap_scores_written,
    }
