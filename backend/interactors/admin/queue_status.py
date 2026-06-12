"""Queue/worker visibility for SUPER_ADMINs.

Combines broker backlog (Redis list length per queue) with live worker state
(Celery inspect: active / reserved / scheduled / ping). Everything degrades to
zeros when no worker is running, so the endpoint never errors just because the
worker profile is down -- which is exactly when you'd hit it to find out why.
"""

import os
import asyncio
import logging

import redis.asyncio as aioredis

from backend.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
QUEUES = ["scrape", "parse", "aggregate", "celery"]


def _count(mapping) -> int:
    """Total items across a {worker: [tasks]} inspect reply (None-safe)."""
    if not mapping:
        return 0
    return sum(len(v) for v in mapping.values())


def _inspect_snapshot() -> dict:
    """Blocking Celery inspect broadcast -- run in a thread by the caller."""
    inspect = celery_app.control.inspect(timeout=1.0)
    ping = inspect.ping() or {}
    return {
        "worker_names": sorted(ping.keys()),
        "active_tasks": _count(inspect.active()),
        "reserved_tasks": _count(inspect.reserved()),
        "scheduled_tasks": _count(inspect.scheduled()),
    }


async def call(db, current_user) -> dict:
    # Worker state (broadcast + wait); off the event loop since it blocks.
    try:
        snap = await asyncio.to_thread(_inspect_snapshot)
    except Exception as e:
        logger.warning("queue-status: inspect failed: %s", e)
        snap = {"worker_names": [], "active_tasks": 0, "reserved_tasks": 0, "scheduled_tasks": 0}

    # Broker backlog: length of each queue's Redis list.
    queues = {q: 0 for q in QUEUES}
    client = aioredis.from_url(REDIS_URL)
    try:
        for q in QUEUES:
            try:
                queues[q] = int(await client.llen(q))
            except Exception:
                queues[q] = 0
    finally:
        await client.aclose()

    return {
        "workers": len(snap["worker_names"]),
        "worker_names": snap["worker_names"],
        "active_tasks": snap["active_tasks"],
        "reserved_tasks": snap["reserved_tasks"],
        "scheduled_tasks": snap["scheduled_tasks"],
        "queues": queues,
    }
