import uuid
from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.migrations.project import Project as ProjectTable
from backend.utils.custom_exceptions import NotFound as DataNotFoundException

class Project:
    async def find_by_id(db: AsyncSession, project_id: uuid.UUID):
        try:
            stmt = select(ProjectTable).where(
                ProjectTable.id == project_id,
                ProjectTable.deleted_at.is_(None),
            )
            result = await db.execute(stmt)
            project = result.scalars().first()
            if not project:
                raise DataNotFoundException("Project not found")
            return project
        except DataNotFoundException:
            raise
        except Exception as e:
            raise Exception(f"Error fetching project by ID: {str(e)}")

    async def find_by_organization(db: AsyncSession, organization_id: uuid.UUID):
        try:
            stmt = select(ProjectTable).where(
                ProjectTable.organization_id == organization_id,
                ProjectTable.deleted_at.is_(None),
            ).order_by(desc(ProjectTable.created_at))
            result = await db.execute(stmt)
            projects = result.scalars().all()
            return projects
        except Exception as e:
            raise Exception(f"Error fetching projects by organization: {str(e)}")

    async def create(db: AsyncSession, organization_id: uuid.UUID, name: str, website_url: str = None):
        try:
            project = ProjectTable(
                id=uuid.uuid4(),
                organization_id=organization_id,
                name=name,
                website_url=website_url,
            )
            db.add(project)
            await db.commit()
            await db.refresh(project)
            return project
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error creating project: {str(e)}")

    async def update(db: AsyncSession, project_id: uuid.UUID, name: str = None, website_url: str = None):
        try:
            project = await Project.find_by_id(db, project_id)

            if name is not None:
                project.name = name
            if website_url is not None:
                project.website_url = website_url
            project.updated_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(project)
            return project
        except DataNotFoundException:
            raise
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error updating project: {str(e)}")

    async def soft_delete(db: AsyncSession, project_id: uuid.UUID):
        try:
            project = await Project.find_by_id(db, project_id)

            project.deleted_at = datetime.now(timezone.utc)
            await db.commit()
            return None
        except DataNotFoundException:
            raise
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error deleting project: {str(e)}")
