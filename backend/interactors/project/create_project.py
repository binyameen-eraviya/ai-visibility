from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.schema.request import ProjectCreate
from backend.database.models.project import Project as ProjectDB

async def call(db: AsyncSession, payload: ProjectCreate, current_user):
    try:
        project = await ProjectDB.create(
            db,
            organization_id=current_user.organization_id,
            name=payload.name,
            website_url=payload.website_url,
        )
        return project
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
