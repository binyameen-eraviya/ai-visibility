"""Scrape execution -- drives one already-created scrape_run to completion.

Milestone 4 moved scraping into Celery. The flow is now:
  1. The caller (manual endpoint or daily scheduler) creates a `scrape_runs` row
     with status PENDING and enqueues `run_scrape_task(tracking_config_id, run_id)`.
  2. The task calls `execute_scrape_run(db, run_id)` here: it drives the adapter,
     stores the capture, and sets SUCCESS / FAILED / RETRYING.
  3. On SUCCESS the task chains parse -> aggregate (separate tasks).

`execute_scrape_run` does NOT create the run row and does NOT parse/aggregate --
those are the task's responsibility. It returns a ScrapeOutcome telling the task
whether to chain onward, retry, or give up. It never raises for an adapter
failure (the failure is recorded on the run); it only raises for truly
unexpected internal errors.
"""

import time
import uuid
import logging
from dataclasses import dataclass
from datetime import datetime, timezone, date as date_type

from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.enums import ScrapeStatus
from backend.database.models.scrape_run import ScrapeRun as ScrapeRunDB
from backend.database.models.tracking_config import TrackingConfig as TrackingConfigDB
from backend.database.models.platform import Platform as PlatformDB
from backend.database.models.prompt import Prompt as PromptDB
from backend.services.storage import BaseStorageService, LocalStorageService
from backend.workers.pool.account_pool import AccountPool, NoAccountAvailable
from backend.workers.scrapers.registry import get_adapter
from backend.workers.scrapers.exceptions import (
    ScraperTimeout,
    CaptchaDetected,
    RateLimited,
    UnexpectedLayout,
)

logger = logging.getLogger(__name__)


@dataclass
class ScrapeOutcome:
    status: str                 # "SUCCESS" | "FAILED" | "RETRY"
    project_id: uuid.UUID = None
    scraped_date: date_type = None
    error: str = None
    retryable: bool = False


async def execute_scrape_run(
    db: AsyncSession,
    scrape_run_id: uuid.UUID,
    storage: BaseStorageService = None,
) -> ScrapeOutcome:
    """Drive an existing PENDING run to SUCCESS / FAILED / RETRYING."""
    storage = storage or LocalStorageService()
    pool = AccountPool(db)

    run = await ScrapeRunDB.find_by_id(db, scrape_run_id)
    tracking_config = await TrackingConfigDB.find_by_id(db, run.tracking_config_id)
    project_id = tracking_config.project_id
    platform = await PlatformDB.find_by_id(db, tracking_config.platform_id)
    prompt = await PromptDB.find_by_id(db, tracking_config.prompt_id)
    platform_id = platform.id
    platform_name = platform.name
    prompt_text = prompt.text

    logger.info(
        "scrape run %s starting: platform=%s tracking_config=%s",
        scrape_run_id, platform_name, run.tracking_config_id,
    )

    # Best-effort account checkout. Perplexity answers unauthenticated, so an
    # empty pool is fine. NOTE: checkout() rolls back on NoAccountAvailable --
    # everything we need from run/tracking_config/platform is already captured.
    account = None
    account_payload = None
    try:
        account = await pool.checkout(platform_id)
        account_payload = {"email": account.email, "cookies": account.cookies}
    except NoAccountAvailable:
        account = None

    await ScrapeRunDB.update(
        db, scrape_run_id,
        status=ScrapeStatus.RUNNING,
        account_id=(account.id if account else None),
    )

    started = time.monotonic()
    try:
        adapter = get_adapter(platform_name)
        raw = await adapter.run_prompt(prompt_text, account=account_payload)
        duration_ms = int((time.monotonic() - started) * 1000)

        data = {
            "prompt": prompt_text,
            "platform": platform_name,
            "answer_text": raw.answer_text,
            "sources": raw.sources,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": raw.metadata,
        }
        raw_path = await storage.save_raw(project_id, scrape_run_id, data)
        screenshot_path = None
        if raw.screenshot:
            screenshot_path = await storage.save_screenshot(project_id, scrape_run_id, raw.screenshot)

        scraped_at = datetime.now(timezone.utc)
        await ScrapeRunDB.update(
            db, scrape_run_id,
            status=ScrapeStatus.SUCCESS,
            raw_storage_path=raw_path,
            screenshot_path=screenshot_path,
            duration_ms=duration_ms,
            scraped_at=scraped_at,
        )
        logger.info("scrape run %s succeeded in %dms", scrape_run_id, duration_ms)
        if account:
            await pool.release(account.id)
        return ScrapeOutcome("SUCCESS", project_id=project_id, scraped_date=scraped_at.date())

    except (ScraperTimeout, RateLimited) as e:
        # Transient: cool the account down and let the task retry.
        duration_ms = int((time.monotonic() - started) * 1000)
        logger.warning("scrape run %s transient failure in %dms: %s", scrape_run_id, duration_ms, e)
        await ScrapeRunDB.update(db, scrape_run_id, status=ScrapeStatus.RETRYING, error=str(e), duration_ms=duration_ms)
        if account:
            await pool.report_failure(account.id)
            await pool.release(account.id)
        return ScrapeOutcome("RETRY", project_id=project_id, error=str(e), retryable=True)

    except CaptchaDetected as e:
        # Permanent for this account: ban it, do not retry.
        duration_ms = int((time.monotonic() - started) * 1000)
        logger.error("scrape run %s captcha/ban in %dms: %s", scrape_run_id, duration_ms, e)
        await ScrapeRunDB.update(db, scrape_run_id, status=ScrapeStatus.FAILED, error=str(e), duration_ms=duration_ms)
        if account:
            await pool.report_failure(account.id, ban=True)
            await pool.release(account.id)
        return ScrapeOutcome("FAILED", project_id=project_id, error=str(e), retryable=False)

    except Exception as e:
        # UnexpectedLayout, missing adapter, or any other error: record FAILED,
        # don't retry (avoid hammering a broken target / looping on a bug).
        duration_ms = int((time.monotonic() - started) * 1000)
        logger.error("scrape run %s failed in %dms: %s", scrape_run_id, duration_ms, e)
        await ScrapeRunDB.update(db, scrape_run_id, status=ScrapeStatus.FAILED, error=str(e), duration_ms=duration_ms)
        if account:
            await pool.report_failure(account.id)
            await pool.release(account.id)
        return ScrapeOutcome("FAILED", project_id=project_id, error=str(e), retryable=False)


async def mark_run_failed(db: AsyncSession, scrape_run_id: uuid.UUID, error: str) -> None:
    """Force a run to FAILED (used when retries are exhausted)."""
    try:
        await ScrapeRunDB.update(db, scrape_run_id, status=ScrapeStatus.FAILED, error=error)
    except Exception as e:
        logger.warning("could not mark run %s failed: %s", scrape_run_id, e)
