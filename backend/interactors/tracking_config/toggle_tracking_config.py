import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.tracking_config import TrackingConfig as TrackingConfigDB
from backend.interactors.helpers.project_access import verify_project_access
from backend.utils.custom_exceptions import NotFound as DataNotFoundException

async def call(db: AsyncSession, project_id: uuid.UUID, tracking_config_id: uuid.UUID, current_user):
    await verify_project_access(db, project_id, current_user)

    try:
        config = await TrackingConfigDB.find_by_id(db, tracking_config_id)
        if config.project_id != project_id:
            raise DataNotFoundException("Tracking config not found")

        config = await TrackingConfigDB.toggle_active(db, tracking_config_id)
        return config
    except DataNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tracking config not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
