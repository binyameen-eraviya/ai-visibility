import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.schema.request import TopicCreate
from backend.database.models.topic import Topic as TopicDB
from backend.interactors.helpers.project_access import verify_project_access

async def call(db: AsyncSession, project_id: uuid.UUID, payload: TopicCreate, current_user):
    await verify_project_access(db, project_id, current_user)

    try:
        topic = await TopicDB.create(db, project_id=project_id, name=payload.name)
        return topic
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
