import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.project import Project as ProjectDB
from backend.interactors.helpers.project_access import verify_project_access

async def call(db: AsyncSession, project_id: uuid.UUID, current_user):
    await verify_project_access(db, project_id, current_user)

    try:
        await ProjectDB.soft_delete(db, project_id)
        return {"message": "Project deleted"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
