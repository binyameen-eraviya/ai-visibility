import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.brand import Brand as BrandDB
from backend.interactors.helpers.project_access import verify_project_access
from backend.utils.custom_exceptions import NotFound as DataNotFoundException

async def call(db: AsyncSession, project_id: uuid.UUID, brand_id: uuid.UUID, current_user):
    await verify_project_access(db, project_id, current_user)

    try:
        brand = await BrandDB.find_by_id(db, brand_id)
        if brand.project_id != project_id:
            raise DataNotFoundException("Brand not found")

        await BrandDB.soft_delete(db, brand_id)
        return {"message": "Brand deleted"}
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
