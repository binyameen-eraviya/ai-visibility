"""Scrape orchestration -- the seam between request and worker.

`run_scrape` owns the full lifecycle of one scrape: create the run row, check out
an account (if any), drive the adapter, persist the capture, and record the final
status. It is deliberately decoupled from the request handler so that Milestone 4
can call the exact same function from a Celery task -- the endpoint just awaits it
synchronously today.

Scraping failures do NOT raise out of here: they are recorded as a FAILED run and
returned, so a manual trigger always gets a run record back.
"""

import time
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.enums import ScrapeStatus
from backend.database.models.scrape_run import ScrapeRun as ScrapeRunDB
from backend.services.storage import BaseStorageService, LocalStorageService
from backend.workers.pool.account_pool import AccountPool, NoAccountAvailable
from backend.workers.scrapers.registry import get_adapter


async def run_scrape(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    platform_id: uuid.UUID,
    platform_name: str,
    tracking_config_id: uuid.UUID,
    prompt_text: str,
    storage: BaseStorageService = None,
):
    """Run one prompt on one platform end to end; return the scrape_run row.

    The same callable backs both the manual endpoint (awaited inline) and the
    future Celery task.
    """
    storage = storage or LocalStorageService()
    pool = AccountPool(db)

    run = await ScrapeRunDB.create(db, tracking_config_id=tracking_config_id, status=ScrapeStatus.PENDING)

    # Try to check out an account. Perplexity answers unauthenticated, so an
    # empty pool is fine -- we just proceed without one.
    account = None
    account_payload = None
    try:
        account = await pool.checkout(platform_id)
        account_payload = {"email": account.email, "cookies": account.cookies}
    except NoAccountAvailable:
        account = None

    await ScrapeRunDB.update(
        db,
        run.id,
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
        raw_path = await storage.save_raw(project_id, run.id, data)

        screenshot_path = None
        if raw.screenshot:
            screenshot_path = await storage.save_screenshot(project_id, run.id, raw.screenshot)

        run = await ScrapeRunDB.update(
            db,
            run.id,
            status=ScrapeStatus.SUCCESS,
            raw_storage_path=raw_path,
            screenshot_path=screenshot_path,
            duration_ms=duration_ms,
            scraped_at=datetime.now(timezone.utc),
        )

        if account:
            await pool.release(account.id)
        return run
    except Exception as e:
        duration_ms = int((time.monotonic() - started) * 1000)
        run = await ScrapeRunDB.update(
            db,
            run.id,
            status=ScrapeStatus.FAILED,
            error=str(e),
            duration_ms=duration_ms,
        )
        if account:
            # Count the failure against the account, then cool it down.
            await pool.report_failure(account.id)
            await pool.release(account.id)
        return run
