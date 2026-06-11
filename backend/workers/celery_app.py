import os

from celery import Celery
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
    ],
)

celery_app.conf.update(
    # Queues: scraping, parsing, and aggregation scale independently.
    task_default_queue="celery",
    task_routes={
        "backend.workers.scrapers.*": {"queue": "scrape"},
        "backend.workers.parsers.*": {"queue": "parse"},
        "backend.workers.aggregator.*": {"queue": "aggregate"},
    },
    # Scrape jobs are long and failure-prone: ack late so a crashed worker
    # does not silently drop a job.
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    timezone="UTC",
    enable_utc=True,
)

# Beat schedule: populated in Milestone 4 (daily scheduler reads
# tracking_configs and enqueues scrape jobs spread across hours).
celery_app.conf.beat_schedule = {}
