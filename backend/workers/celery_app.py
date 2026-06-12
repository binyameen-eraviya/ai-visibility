import os

from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv()

# Inside Docker the broker host is the "redis" service; locally it falls back
# to localhost (same pattern as backend/database/db.py for the db host).
BROKER_HOST = "redis" if os.getenv("ENVIRONMENT") == "production" else "localhost"

BROKER_URL = os.getenv("CELERY_BROKER_URL", f"redis://{BROKER_HOST}:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", f"redis://{BROKER_HOST}:6379/1")

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
