import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.schema.request import PromptUpdate
from backend.database.models.prompt import Prompt as PromptDB
from backend.database.models.topic import Topic as TopicDB
from backend.interactors.helpers.project_access import verify_project_access
from backend.utils.custom_exceptions import NotFound as DataNotFoundException

async def call(db: AsyncSession, project_id: uuid.UUID, prompt_id: uuid.UUID, payload: PromptUpdate, current_user):
    await verify_project_access(db, project_id, current_user)

    try:
        prompt = await PromptDB.find_by_id(db, prompt_id)
        if prompt.project_id != project_id:
            raise DataNotFoundException("Prompt not found")

        if payload.topic_id:
            topic = await TopicDB.find_by_id(db, payload.topic_id)
            if topic.project_id != project_id:
                raise DataNotFoundException("Topic not found")

        prompt = await PromptDB.update(
            db,
            prompt_id,
            text=payload.text,
            topic_id=payload.topic_id,
            status=payload.status,
        )
        return prompt
    except DataNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
