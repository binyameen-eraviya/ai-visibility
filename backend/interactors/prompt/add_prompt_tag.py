import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.prompt import Prompt as PromptDB
from backend.interactors.helpers.project_access import verify_project_access
from backend.utils.custom_exceptions import (
    NotFound as DataNotFoundException,
    BadRequest as BadRequestException,
)

async def call(db: AsyncSession, project_id: uuid.UUID, prompt_id: uuid.UUID, tag_id: uuid.UUID, current_user):
    await verify_project_access(db, project_id, current_user)

    try:
        prompt = await PromptDB.find_by_id(db, prompt_id)
        if prompt.project_id != project_id:
            raise DataNotFoundException("Prompt not found")

        prompt = await PromptDB.add_tag(db, prompt_id, tag_id)
        return prompt
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
