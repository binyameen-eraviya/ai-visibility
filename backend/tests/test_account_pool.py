"""Account pool checkout / quota / cooldown / release / failure handling."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import update

from backend.workers.pool.account_pool import AccountPool, NoAccountAvailable
from backend.utils.enums import ScrapeAccountStatus
from backend.database.models.scrape_account import ScrapeAccount
from backend.database.migrations.scrape_account import ScrapeAccount as AccountTable


@pytest.fixture
async def platform_id(seed_reference):
    return seed_reference["platform"].id


async def test_checkout_returns_least_recently_used(db_session, platform_id):
    older = await ScrapeAccount.create(db_session, platform_id, "a@test.com")
    newer = await ScrapeAccount.create(db_session, platform_id, "b@test.com")
    now = datetime.now(timezone.utc)
    await db_session.execute(
        update(AccountTable).where(AccountTable.id == older.id)
        .values(last_used_at=now - timedelta(hours=2))
    )
    await db_session.execute(
        update(AccountTable).where(AccountTable.id == newer.id).values(last_used_at=now)
    )
    await db_session.commit()

    pool = AccountPool(db_session)
    chosen = await pool.checkout(platform_id)
    assert chosen.id == older.id


async def test_checkout_respects_quota(db_session, platform_id):
    acct = await ScrapeAccount.create(
        db_session, platform_id, "q@test.com", daily_quota_limit=1
    )
    await db_session.execute(
        update(AccountTable).where(AccountTable.id == acct.id).values(daily_quota_used=1)
    )
    await db_session.commit()

    pool = AccountPool(db_session)
    with pytest.raises(NoAccountAvailable):
        await pool.checkout(platform_id)


async def test_checkout_respects_cooldown(db_session, platform_id):
    acct = await ScrapeAccount.create(db_session, platform_id, "c@test.com")
    future = datetime.now(timezone.utc) + timedelta(minutes=30)
    await db_session.execute(
        update(AccountTable).where(AccountTable.id == acct.id).values(
            status=ScrapeAccountStatus.COOLDOWN, cooldown_until=future
        )
    )
    await db_session.commit()

    pool = AccountPool(db_session)
    with pytest.raises(NoAccountAvailable):
        await pool.checkout(platform_id)


async def test_release_sets_cooldown(db_session, platform_id):
    acct = await ScrapeAccount.create(db_session, platform_id, "r@test.com")
    pool = AccountPool(db_session)
    released = await pool.release(acct.id)
    assert released.status == ScrapeAccountStatus.COOLDOWN
    assert released.cooldown_until is not None


async def test_report_failure_disables_after_threshold(db_session, platform_id):
    acct = await ScrapeAccount.create(db_session, platform_id, "f@test.com")
    pool = AccountPool(db_session)
    result = None
    for _ in range(3):
        result = await pool.report_failure(acct.id)
    assert result.status == ScrapeAccountStatus.DISABLED


async def test_report_failure_ban_sets_banned(db_session, platform_id):
    acct = await ScrapeAccount.create(db_session, platform_id, "b2@test.com")
    pool = AccountPool(db_session)
    result = await pool.report_failure(acct.id, ban=True)
    assert result.status == ScrapeAccountStatus.BANNED
