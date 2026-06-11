import uuid

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.migrations.topic import Topic as TopicTable
from backend.utils.custom_exceptions import NotFound as DataNotFoundException

class Topic:
    async def find_by_id(db: AsyncSession, topic_id: uuid.UUID):
        try:
            stmt = select(TopicTable).where(TopicTable.id == topic_id)
            result = await db.execute(stmt)
            topic = result.scalars().first()
            if not topic:
                raise DataNotFoundException("Topic not found")
            return topic
        except DataNotFoundException:
            raise
        except Exception as e:
            raise Exception(f"Error fetching topic by ID: {str(e)}")

    async def find_by_project(db: AsyncSession, project_id: uuid.UUID):
        try:
            stmt = select(TopicTable).where(
                TopicTable.project_id == project_id
            ).order_by(desc(TopicTable.created_at))
            result = await db.execute(stmt)
            topics = result.scalars().all()
            return topics
        except Exception as e:
            raise Exception(f"Error fetching topics by project: {str(e)}")

    async def create(db: AsyncSession, project_id: uuid.UUID, name: str):
        try:
            topic = TopicTable(id=uuid.uuid4(), project_id=project_id, name=name)
            db.add(topic)
            await db.commit()
            await db.refresh(topic)
            return topic
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error creating topic: {str(e)}")

    async def delete(db: AsyncSession, topic_id: uuid.UUID):
        try:
            topic = await Topic.find_by_id(db, topic_id)

            await db.delete(topic)
            await db.commit()
            return None
        except DataNotFoundException:
            raise
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error deleting topic: {str(e)}")
