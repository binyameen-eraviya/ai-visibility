import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from backend.interactors.helpers.project_access import verify_project_access

async def call(db: AsyncSession, project_id: uuid.UUID, current_user):
    project = await verify_project_access(db, project_id, current_user)
    return project
