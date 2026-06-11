from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.schema.request import ScrapeAccountCreate
from backend.database.models.platform import Platform as PlatformDB
from backend.database.models.scrape_account import ScrapeAccount as ScrapeAccountDB
from backend.utils.custom_exceptions import NotFound as DataNotFoundException


async def call(db: AsyncSession, payload: ScrapeAccountCreate, current_user):
    try:
        # Fail clearly if the platform UUID is bogus.
        await PlatformDB.find_by_id(db, payload.platform_id)

        account = await ScrapeAccountDB.create(
            db,
            platform_id=payload.platform_id,
            email=payload.email,
            cookies=payload.cookies,
            daily_quota_limit=payload.daily_quota_limit,
        )
        return account
    except DataNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Platform not found",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
