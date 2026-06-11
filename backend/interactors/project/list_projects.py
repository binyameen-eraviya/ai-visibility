from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.project import Project as ProjectDB

async def call(db: AsyncSession, current_user):
    try:
        projects = await ProjectDB.find_by_organization(db, current_user.organization_id)
        return projects
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
