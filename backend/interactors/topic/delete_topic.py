import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.topic import Topic as TopicDB
from backend.interactors.helpers.project_access import verify_project_access
from backend.utils.custom_exceptions import NotFound as DataNotFoundException

async def call(db: AsyncSession, project_id: uuid.UUID, topic_id: uuid.UUID, current_user):
    await verify_project_access(db, project_id, current_user)

    try:
        topic = await TopicDB.find_by_id(db, topic_id)
        if topic.project_id != project_id:
            raise DataNotFoundException("Topic not found")

        await TopicDB.delete(db, topic_id)
        return {"message": "Topic deleted"}
    except DataNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
