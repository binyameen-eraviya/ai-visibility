import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.schema.request import BrandCreate
from backend.database.models.brand import Brand as BrandDB
from backend.interactors.helpers.project_access import verify_project_access

async def call(db: AsyncSession, project_id: uuid.UUID, payload: BrandCreate, current_user):
    await verify_project_access(db, project_id, current_user)

    try:
        brand = await BrandDB.create(
            db,
            project_id=project_id,
            name=payload.name,
            aliases=payload.aliases,
            is_primary=payload.is_primary,
        )
        return brand
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
