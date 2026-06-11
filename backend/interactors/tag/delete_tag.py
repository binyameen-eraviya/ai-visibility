import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.tag import Tag as TagDB
from backend.interactors.helpers.project_access import verify_project_access
from backend.utils.custom_exceptions import NotFound as DataNotFoundException

async def call(db: AsyncSession, project_id: uuid.UUID, tag_id: uuid.UUID, current_user):
    await verify_project_access(db, project_id, current_user)

    try:
        tag = await TagDB.find_by_id(db, tag_id)
        if tag.project_id != project_id:
            raise DataNotFoundException("Tag not found")

        await TagDB.delete(db, tag_id)
        return {"message": "Tag deleted"}
    except DataNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
