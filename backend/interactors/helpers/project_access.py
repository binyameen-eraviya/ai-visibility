import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.project import Project as ProjectDB
from backend.utils.custom_exceptions import NotFound as DataNotFoundException


async def verify_project_access(db: AsyncSession, project_id: uuid.UUID, current_user):
    """Fetch a project and ensure it belongs to the user's organization.

    Returns the project, or raises 404 (a foreign org's project is
    indistinguishable from a missing one -- no information leak).
    """
    try:
        project = await ProjectDB.find_by_id(db, project_id)
    except DataNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if project.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return project
