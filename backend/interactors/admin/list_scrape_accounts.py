import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.scrape_account import ScrapeAccount as ScrapeAccountDB


async def call(db: AsyncSession, current_user, platform_id: uuid.UUID = None):
    try:
        return await ScrapeAccountDB.get_list(db, platform_id=platform_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
