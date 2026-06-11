import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.schema.request import TrackingConfigCreate
from backend.database.models.prompt import Prompt as PromptDB
from backend.database.models.tracking_config import TrackingConfig as TrackingConfigDB
from backend.interactors.helpers.project_access import verify_project_access
from backend.utils.custom_exceptions import (
    NotFound as DataNotFoundException,
    BadRequest as BadRequestException,
)

async def call(db: AsyncSession, project_id: uuid.UUID, payload: TrackingConfigCreate, current_user):
    await verify_project_access(db, project_id, current_user)

    try:
        # The prompt must belong to this project.
        prompt = await PromptDB.find_by_id(db, payload.prompt_id)
        if prompt.project_id != project_id:
            raise DataNotFoundException("Prompt not found")

        config = await TrackingConfigDB.create(
            db,
            project_id=project_id,
            prompt_id=payload.prompt_id,
            platform_id=payload.platform_id,
            country_id=payload.country_id,
            frequency=payload.frequency,
        )
        return config
    except DataNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except BadRequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
