import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.tag import Tag as TagDB
from backend.interactors.helpers.project_access import verify_project_access

async def call(db: AsyncSession, project_id: uuid.UUID, current_user):
    await verify_project_access(db, project_id, current_user)

    try:
        tags = await TagDB.find_by_project(db, project_id)
        return tags
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
