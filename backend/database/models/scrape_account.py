import uuid

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.enums import ScrapeAccountStatus
from backend.database.migrations.scrape_account import ScrapeAccount as ScrapeAccountTable
from backend.utils.custom_exceptions import NotFound as DataNotFoundException

class ScrapeAccount:
    async def find_by_id(db: AsyncSession, account_id: uuid.UUID):
        try:
            stmt = select(ScrapeAccountTable).where(ScrapeAccountTable.id == account_id)
            result = await db.execute(stmt)
            account = result.scalars().first()
            if not account:
                raise DataNotFoundException("Scrape account not found")
            return account
        except DataNotFoundException:
            raise
        except Exception as e:
            raise Exception(f"Error fetching scrape account by ID: {str(e)}")

    async def get_list(db: AsyncSession, platform_id: uuid.UUID = None):
        try:
            stmt = select(ScrapeAccountTable).order_by(desc(ScrapeAccountTable.created_at))
            if platform_id:
                stmt = stmt.where(ScrapeAccountTable.platform_id == platform_id)
            result = await db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            raise Exception(f"Error fetching scrape account list: {str(e)}")

    async def create(
        db: AsyncSession,
        platform_id: uuid.UUID,
        email: str,
        cookies: dict = None,
        daily_quota_limit: int = 10,
    ):
        try:
            account = ScrapeAccountTable(
                id=uuid.uuid4(),
                platform_id=platform_id,
                email=email,
                cookies=cookies or {},
                daily_quota_used=0,
                daily_quota_limit=daily_quota_limit,
                status=ScrapeAccountStatus.ACTIVE,
                attrs={},
            )
            db.add(account)
            await db.commit()
            await db.refresh(account)
            return account
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error creating scrape account: {str(e)}")
