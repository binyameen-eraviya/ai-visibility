import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.prompt import Prompt as PromptDB
from backend.interactors.helpers.project_access import verify_project_access
from backend.utils.custom_exceptions import NotFound as DataNotFoundException

async def call(db: AsyncSession, project_id: uuid.UUID, prompt_id: uuid.UUID, current_user):
    await verify_project_access(db, project_id, current_user)

    try:
        prompt = await PromptDB.find_by_id(db, prompt_id)
        if prompt.project_id != project_id:
            raise DataNotFoundException("Prompt not found")

        await PromptDB.soft_delete(db, prompt_id)
        return {"message": "Prompt deleted"}
    except DataNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
