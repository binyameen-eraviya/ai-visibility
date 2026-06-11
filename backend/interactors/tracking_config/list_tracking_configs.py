import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.tracking_config import TrackingConfig as TrackingConfigDB
from backend.interactors.helpers.project_access import verify_project_access

async def call(db: AsyncSession, project_id: uuid.UUID, current_user):
    await verify_project_access(db, project_id, current_user)

    try:
        configs = await TrackingConfigDB.find_by_project(db, project_id)
        return configs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
