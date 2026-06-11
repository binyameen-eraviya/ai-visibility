import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.migrations.platform import Platform as PlatformTable
from backend.utils.custom_exceptions import NotFound as DataNotFoundException

class Platform:
    async def find_by_id(db: AsyncSession, platform_id: uuid.UUID):
        try:
            stmt = select(PlatformTable).where(PlatformTable.id == platform_id)
            result = await db.execute(stmt)
            platform = result.scalars().first()
            if not platform:
                raise DataNotFoundException("Platform not found")
            return platform
        except DataNotFoundException:
            raise
        except Exception as e:
            raise Exception(f"Error fetching platform by ID: {str(e)}")

    async def get_list(db: AsyncSession, active_only: bool = False):
        try:
            stmt = select(PlatformTable).order_by(PlatformTable.name)
            if active_only:
                stmt = stmt.where(PlatformTable.is_active.is_(True))
            result = await db.execute(stmt)
            platforms = result.scalars().all()
            return platforms
        except Exception as e:
            raise Exception(f"Error fetching platform list: {str(e)}")
