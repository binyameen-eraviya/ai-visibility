import os
from pathlib import Path
from importlib import import_module

from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv()


def _import_all_models() -> None:
    """Import every migration module so all SQLAlchemy mappers are registered.

    The worker/beat processes don't import the FastAPI routes, so without this a
    cross-model relationship (e.g. Organization -> User) fails to configure on
    the first query: "expression 'User' failed to locate a name". Mirrors
    backend/alembic/env.py:import_all_migration_models.
    """
    migrations_dir = Path(__file__).resolve().parents[1] / "database" / "migrations"
    for model_file in migrations_dir.glob("*.py"):
        if model_file.name.startswith("_"):
            continue
        import_module(f"backend.database.migrations.{model_file.stem}")


_import_all_models()

# Compose injects CELERY_BROKER_URL / CELERY_RESULT_BACKEND from the root
# .env (host "redis" inside Docker); localhost fallbacks cover running the
# worker directly on the host.
BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

celery_app = Celery(
    "ai_visibility",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=[
        "backend.workers.tasks",
        "backend.workers.tasks.scrape_task",
        "backend.workers.tasks.parse_task",
        "backend.workers.tasks.aggregate_task",
        "backend.workers.tasks.scheduler_task",
    ],
)

celery_app.conf.update(
    # Queues: scraping, parsing, and aggregation scale independently.
    task_default_queue="celery",
    task_routes={
        # Browser scraping is heavy and platforms rate-limit aggressively, so the
        # scrape queue is throttled hard. Parse is lighter (LLM + DB); aggregate
        # is just SQL. (rate_limit is also set on each task decorator.)
        "backend.workers.tasks.scrape_task.*": {"queue": "scrape", "rate_limit": "3/m"},
        "backend.workers.tasks.parse_task.*": {"queue": "parse", "rate_limit": "10/m"},
        "backend.workers.tasks.aggregate_task.*": {"queue": "aggregate"},
        "backend.workers.tasks.scheduler_task.*": {"queue": "aggregate"},
    },
    # Max concurrent tasks per worker, and a global ceiling.
    worker_concurrency=4,
    task_default_rate_limit="10/m",
    # Scrape jobs are long and failure-prone: ack late so a crashed worker
    # does not silently drop a job.
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    timezone="UTC",
    enable_utc=True,
)

# Beat schedule (tasks live in backend/workers/tasks/scheduler_task.py).
celery_app.conf.beat_schedule = {
    "schedule-daily-runs": {
        "task": "backend.workers.tasks.scheduler_task.schedule_daily_runs",
        "schedule": crontab(hour=2, minute=0),  # 2 AM UTC daily
    },
    "reset-account-quotas": {
        "task": "backend.workers.tasks.scheduler_task.reset_account_quotas",
        "schedule": crontab(hour=0, minute=0),  # midnight UTC daily
    },
    "cleanup-old-runs": {
        "task": "backend.workers.tasks.scheduler_task.cleanup_old_runs",
        "schedule": crontab(hour=3, minute=0, day_of_week=0),  # Sunday 3 AM UTC
    },
}
