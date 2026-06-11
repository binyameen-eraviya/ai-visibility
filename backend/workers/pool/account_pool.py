"""Account pool (v1).

Hands out the least-recently-used available account for a platform, tracks
daily quota, and cools down / disables / bans accounts. Intentionally minimal:
enough to prove the checkout -> use -> release flow. Proxy matching, richer
health checks, and a Celery-driven daily reset arrive in Milestone 4.

Concurrency: checkout uses SELECT ... FOR UPDATE SKIP LOCKED so two workers
never grab the same account.
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.enums import ScrapeAccountStatus
from backend.database.migrations.scrape_account import ScrapeAccount as ScrapeAccountTable


# Consecutive failures before an account is auto-disabled.
FAILURE_DISABLE_THRESHOLD = 3


class NoAccountAvailable(Exception):
    """Raised by checkout() when no usable account exists for a platform."""


class AccountPool:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def checkout(self, platform_id: uuid.UUID) -> ScrapeAccountTable:
        """Reserve the least-recently-used available account for a platform.

        Available means: not BANNED/DISABLED, off cooldown, and under its daily
        quota. Marks the account in-use (status ACTIVE, last_used_at = now) and
        increments daily_quota_used.

        Raises NoAccountAvailable if nothing is usable.
        """
        now = datetime.now(timezone.utc)
        try:
            stmt = (
                select(ScrapeAccountTable)
                .where(
                    ScrapeAccountTable.platform_id == platform_id,
                    ScrapeAccountTable.status.in_(
                        [ScrapeAccountStatus.ACTIVE, ScrapeAccountStatus.COOLDOWN]
                    ),
                    ScrapeAccountTable.daily_quota_used < ScrapeAccountTable.daily_quota_limit,
                    (ScrapeAccountTable.cooldown_until.is_(None))
                    | (ScrapeAccountTable.cooldown_until <= now),
                )
                .order_by(ScrapeAccountTable.last_used_at.asc().nullsfirst())
                .limit(1)
                .with_for_update(skip_locked=True)
            )
            result = await self.db.execute(stmt)
            account = result.scalars().first()
            if not account:
                raise NoAccountAvailable(
                    f"No available scrape account for platform {platform_id}"
                )

            account.status = ScrapeAccountStatus.ACTIVE
            account.cooldown_until = None
            account.last_used_at = now
            account.daily_quota_used = (account.daily_quota_used or 0) + 1
            await self.db.commit()
            await self.db.refresh(account)
            return account
        except NoAccountAvailable:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            raise Exception(f"Error checking out scrape account: {str(e)}")

    async def release(self, account_id: uuid.UUID, cooldown_minutes: int = 5):
        """Return an account to the pool with a short cooldown."""
        now = datetime.now(timezone.utc)
        try:
            stmt = select(ScrapeAccountTable).where(ScrapeAccountTable.id == account_id)
            result = await self.db.execute(stmt)
            account = result.scalars().first()
            if not account:
                return None

            # Don't re-activate an account that was banned/disabled mid-run.
            if account.status not in (ScrapeAccountStatus.BANNED, ScrapeAccountStatus.DISABLED):
                account.status = ScrapeAccountStatus.COOLDOWN
            account.cooldown_until = now + timedelta(minutes=cooldown_minutes)
            await self.db.commit()
            await self.db.refresh(account)
            return account
        except Exception as e:
            await self.db.rollback()
            raise Exception(f"Error releasing scrape account: {str(e)}")

    async def report_failure(self, account_id: uuid.UUID, ban: bool = False):
        """Record a failed run. Ban outright, or disable after repeated failures."""
        try:
            stmt = select(ScrapeAccountTable).where(ScrapeAccountTable.id == account_id)
            result = await self.db.execute(stmt)
            account = result.scalars().first()
            if not account:
                return None

            if ban:
                account.status = ScrapeAccountStatus.BANNED
            else:
                attrs = dict(account.attrs or {})
                failures = int(attrs.get("failure_count", 0)) + 1
                attrs["failure_count"] = failures
                account.attrs = attrs
                if failures >= FAILURE_DISABLE_THRESHOLD:
                    account.status = ScrapeAccountStatus.DISABLED
            await self.db.commit()
            await self.db.refresh(account)
            return account
        except Exception as e:
            await self.db.rollback()
            raise Exception(f"Error reporting scrape account failure: {str(e)}")

    async def reset_daily_quotas(self):
        """Reset every account's daily quota counter (daily Celery task in M4)."""
        try:
            await self.db.execute(update(ScrapeAccountTable).values(daily_quota_used=0))
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise Exception(f"Error resetting daily quotas: {str(e)}")
