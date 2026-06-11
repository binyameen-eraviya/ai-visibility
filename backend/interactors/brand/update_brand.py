import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.schema.request import BrandUpdate
from backend.database.models.brand import Brand as BrandDB
from backend.interactors.helpers.project_access import verify_project_access
from backend.utils.custom_exceptions import NotFound as DataNotFoundException

async def call(db: AsyncSession, project_id: uuid.UUID, brand_id: uuid.UUID, payload: BrandUpdate, current_user):
    await verify_project_access(db, project_id, current_user)

    try:
        brand = await BrandDB.find_by_id(db, brand_id)
        if brand.project_id != project_id:
            raise DataNotFoundException("Brand not found")

        brand = await BrandDB.update(
            db,
            brand_id,
            name=payload.name,
            aliases=payload.aliases,
            is_primary=payload.is_primary,
        )
        return brand
    except DataNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
