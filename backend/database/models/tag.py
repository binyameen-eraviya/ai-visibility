import uuid

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.migrations.tag import Tag as TagTable
from backend.utils.custom_exceptions import NotFound as DataNotFoundException

class Tag:
    async def find_by_id(db: AsyncSession, tag_id: uuid.UUID):
        try:
            stmt = select(TagTable).where(TagTable.id == tag_id)
            result = await db.execute(stmt)
            tag = result.scalars().first()
            if not tag:
                raise DataNotFoundException("Tag not found")
            return tag
        except DataNotFoundException:
            raise
        except Exception as e:
            raise Exception(f"Error fetching tag by ID: {str(e)}")

    async def find_by_project(db: AsyncSession, project_id: uuid.UUID):
        try:
            stmt = select(TagTable).where(
                TagTable.project_id == project_id
            ).order_by(desc(TagTable.created_at))
            result = await db.execute(stmt)
            tags = result.scalars().all()
            return tags
        except Exception as e:
            raise Exception(f"Error fetching tags by project: {str(e)}")

    async def create(db: AsyncSession, project_id: uuid.UUID, name: str):
        try:
            tag = TagTable(id=uuid.uuid4(), project_id=project_id, name=name)
            db.add(tag)
            await db.commit()
            await db.refresh(tag)
            return tag
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error creating tag: {str(e)}")

    async def delete(db: AsyncSession, tag_id: uuid.UUID):
        try:
            tag = await Tag.find_by_id(db, tag_id)

            await db.delete(tag)
            await db.commit()
            return None
        except DataNotFoundException:
            raise
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error deleting tag: {str(e)}")
