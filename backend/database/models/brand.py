import uuid
from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.migrations.brand import Brand as BrandTable
from backend.utils.custom_exceptions import NotFound as DataNotFoundException

class Brand:
    async def find_by_id(db: AsyncSession, brand_id: uuid.UUID):
        try:
            stmt = select(BrandTable).where(
                BrandTable.id == brand_id,
                BrandTable.deleted_at.is_(None),
            )
            result = await db.execute(stmt)
            brand = result.scalars().first()
            if not brand:
                raise DataNotFoundException("Brand not found")
            return brand
        except DataNotFoundException:
            raise
        except Exception as e:
            raise Exception(f"Error fetching brand by ID: {str(e)}")

    async def find_by_project(db: AsyncSession, project_id: uuid.UUID):
        try:
            stmt = select(BrandTable).where(
                BrandTable.project_id == project_id,
                BrandTable.deleted_at.is_(None),
            ).order_by(desc(BrandTable.is_primary), desc(BrandTable.created_at))
            result = await db.execute(stmt)
            brands = result.scalars().all()
            return brands
        except Exception as e:
            raise Exception(f"Error fetching brands by project: {str(e)}")

    async def create(
        db: AsyncSession,
        project_id: uuid.UUID,
        name: str,
        aliases: list = None,
        is_primary: bool = False,
    ):
        try:
            brand = BrandTable(
                id=uuid.uuid4(),
                project_id=project_id,
                name=name,
                aliases=aliases or [],
                is_primary=is_primary,
            )
            db.add(brand)
            await db.commit()
            await db.refresh(brand)
            return brand
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error creating brand: {str(e)}")

    async def update(
        db: AsyncSession,
        brand_id: uuid.UUID,
        name: str = None,
        aliases: list = None,
        is_primary: bool = None,
    ):
        try:
            brand = await Brand.find_by_id(db, brand_id)

            if name is not None:
                brand.name = name
            if aliases is not None:
                brand.aliases = aliases
            if is_primary is not None:
                brand.is_primary = is_primary
            brand.updated_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(brand)
            return brand
        except DataNotFoundException:
            raise
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error updating brand: {str(e)}")

    async def soft_delete(db: AsyncSession, brand_id: uuid.UUID):
        try:
            brand = await Brand.find_by_id(db, brand_id)

            brand.deleted_at = datetime.now(timezone.utc)
            await db.commit()
            return None
        except DataNotFoundException:
            raise
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error deleting brand: {str(e)}")
