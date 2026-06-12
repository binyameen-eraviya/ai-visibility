"""Liveness/readiness health check.

Unprotected. Actually pings Postgres and Redis so Docker healthchecks and
future monitoring can distinguish "process is up" from "dependencies are
reachable". Returns 200 when both are connected, 503 otherwise.
"""

import os
import asyncio
import logging

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_db
from backend.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])

APP_VERSION = "0.1.0"
REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")


@router.get("/health")
async def health(response: Response, db: AsyncSession = Depends(get_db)):
    db_status = "connected"
    redis_status = "connected"

    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = "error"
        logger.warning("Health check: database ping failed: %s", e)

    client = aioredis.from_url(REDIS_URL)
    try:
        await client.ping()
    except Exception as e:
        redis_status = "error"
        logger.warning("Health check: redis ping failed: %s", e)
    finally:
        await client.aclose()

    # Celery is informational only: the worker is optional (behind a compose
    # profile), so a disconnected worker does NOT mark the app degraded.
    celery_status = "disconnected"
    try:
        replies = await asyncio.to_thread(celery_app.control.ping, timeout=0.5)
        if replies:
            celery_status = "connected"
    except Exception as e:
        logger.warning("Health check: celery ping failed: %s", e)

    healthy = db_status == "connected" and redis_status == "connected"
    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "healthy" if healthy else "degraded",
        "database": db_status,
        "redis": redis_status,
        "celery": celery_status,
        "version": APP_VERSION,
    }
