import uuid
from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.enums import PromptStatus
from backend.database.migrations.prompt import Prompt as PromptTable
from backend.database.migrations.tag import Tag as TagTable
from backend.utils.custom_exceptions import (
    NotFound as DataNotFoundException,
    BadRequest as BadRequestException,
)

class Prompt:
    async def find_by_id(db: AsyncSession, prompt_id: uuid.UUID):
        try:
            stmt = select(PromptTable).where(
                PromptTable.id == prompt_id,
                PromptTable.deleted_at.is_(None),
            ).options(selectinload(PromptTable.tags), selectinload(PromptTable.topic))
            result = await db.execute(stmt)
            prompt = result.scalars().first()
            if not prompt:
                raise DataNotFoundException("Prompt not found")
            return prompt
        except DataNotFoundException:
            raise
        except Exception as e:
            raise Exception(f"Error fetching prompt by ID: {str(e)}")

    async def find_by_project(db: AsyncSession, project_id: uuid.UUID):
        try:
            stmt = select(PromptTable).where(
                PromptTable.project_id == project_id,
                PromptTable.deleted_at.is_(None),
            ).options(
                selectinload(PromptTable.tags), selectinload(PromptTable.topic)
            ).order_by(desc(PromptTable.created_at))
            result = await db.execute(stmt)
            prompts = result.scalars().all()
            return prompts
        except Exception as e:
            raise Exception(f"Error fetching prompts by project: {str(e)}")

    async def create(
        db: AsyncSession,
        project_id: uuid.UUID,
        text: str,
        topic_id: uuid.UUID = None,
        tag_ids: list = None,
    ):
        try:
            prompt = PromptTable(
                id=uuid.uuid4(),
                project_id=project_id,
                text=text,
                topic_id=topic_id,
                tags=[],
            )

            if tag_ids:
                # Only attach tags that belong to the same project.
                stmt = select(TagTable).where(
                    TagTable.id.in_(tag_ids),
                    TagTable.project_id == project_id,
                )
                result = await db.execute(stmt)
                prompt.tags = list(result.scalars().all())

            db.add(prompt)
            await db.commit()
            return await Prompt.find_by_id(db, prompt.id)
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error creating prompt: {str(e)}")

    async def update(
        db: AsyncSession,
        prompt_id: uuid.UUID,
        text: str = None,
        topic_id: uuid.UUID = None,
        status: PromptStatus = None,
    ):
        try:
            prompt = await Prompt.find_by_id(db, prompt_id)

            if text is not None:
                prompt.text = text
            if topic_id is not None:
                prompt.topic_id = topic_id
            if status is not None:
                prompt.status = status
            prompt.updated_at = datetime.now(timezone.utc)
            await db.commit()
            return await Prompt.find_by_id(db, prompt_id)
        except DataNotFoundException:
            raise
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error updating prompt: {str(e)}")

    async def soft_delete(db: AsyncSession, prompt_id: uuid.UUID):
        try:
            prompt = await Prompt.find_by_id(db, prompt_id)

            prompt.deleted_at = datetime.now(timezone.utc)
            await db.commit()
            return None
        except DataNotFoundException:
            raise
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error deleting prompt: {str(e)}")

    async def add_tag(db: AsyncSession, prompt_id: uuid.UUID, tag_id: uuid.UUID):
        try:
            prompt = await Prompt.find_by_id(db, prompt_id)

            stmt = select(TagTable).where(TagTable.id == tag_id)
            result = await db.execute(stmt)
            tag = result.scalars().first()
            if not tag:
                raise DataNotFoundException("Tag not found")
            if tag.project_id != prompt.project_id:
                raise BadRequestException("Tag belongs to a different project")

            if tag not in prompt.tags:
                prompt.tags.append(tag)
                await db.commit()
            return await Prompt.find_by_id(db, prompt_id)
        except (DataNotFoundException, BadRequestException):
            raise
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error adding tag to prompt: {str(e)}")

    async def remove_tag(db: AsyncSession, prompt_id: uuid.UUID, tag_id: uuid.UUID):
        try:
            prompt = await Prompt.find_by_id(db, prompt_id)

            tag = next((t for t in prompt.tags if t.id == tag_id), None)
            if not tag:
                raise DataNotFoundException("Tag not attached to prompt")

            prompt.tags.remove(tag)
            await db.commit()
            return await Prompt.find_by_id(db, prompt_id)
        except DataNotFoundException:
            raise
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error removing tag from prompt: {str(e)}")
