import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.schema.request import TrackingConfigBulkCreate
from backend.database.models.prompt import Prompt as PromptDB
from backend.database.models.tracking_config import TrackingConfig as TrackingConfigDB
from backend.interactors.helpers.project_access import verify_project_access

async def call(db: AsyncSession, project_id: uuid.UUID, payload: TrackingConfigBulkCreate, current_user):
    await verify_project_access(db, project_id, current_user)

    try:
        # Every prompt referenced must belong to this project.
        project_prompts = await PromptDB.find_by_project(db, project_id)
        project_prompt_ids = {p.id for p in project_prompts}
        for c in payload.configs:
            if c.prompt_id not in project_prompt_ids:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Prompt {c.prompt_id} not found",
                )

        configs = await TrackingConfigDB.bulk_create(
            db,
            project_id=project_id,
            configs=[c.model_dump() for c in payload.configs],
        )
        return configs
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
