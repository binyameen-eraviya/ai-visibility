"""Shared/diagnostic Celery tasks."""

from backend.workers.celery_app import celery_app


@celery_app.task(name="backend.workers.tasks.ping")
def ping():
    """Health-check task to verify the worker and broker are wired up.

    Usage (inside the api or worker container):
        from backend.workers.tasks import ping
        ping.delay().get(timeout=10)  # -> "pong"
    """
    return "pong"
