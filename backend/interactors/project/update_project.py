import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.schema.request import ProjectUpdate
from backend.database.models.project import Project as ProjectDB
from backend.interactors.helpers.project_access import verify_project_access

async def call(db: AsyncSession, project_id: uuid.UUID, payload: ProjectUpdate, current_user):
    await verify_project_access(db, project_id, current_user)

    try:
        project = await ProjectDB.update(
            db,
            project_id,
            name=payload.name,
            website_url=payload.website_url,
        )
        return project
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
