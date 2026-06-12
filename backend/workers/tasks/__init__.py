"""Celery task package.

Importing this package registers every task with the Celery app (celery_app's
`include` lists these submodules). A diagnostic `ping` task lives here.
"""

from backend.workers.celery_app import celery_app

# Import task modules so their @celery_app.task decorators run on package import.
from backend.workers.tasks import scrape_task  # noqa: F401
from backend.workers.tasks import parse_task  # noqa: F401
from backend.workers.tasks import aggregate_task  # noqa: F401
from backend.workers.tasks import scheduler_task  # noqa: F401


@celery_app.task(name="backend.workers.tasks.ping")
def ping():
    """Health-check task to verify the worker and broker are wired up.

    Usage (inside the api or worker container):
        from backend.workers.tasks import ping
        ping.delay().get(timeout=10)  # -> "pong"
    """
    return "pong"
