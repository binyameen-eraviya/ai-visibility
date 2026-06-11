import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.migrations.mention import Mention as MentionTable

class Mention:
    async def find_by_answer(db: AsyncSession, answer_id: uuid.UUID):
        try:
            stmt = select(MentionTable).where(MentionTable.answer_id == answer_id)
            result = await db.execute(stmt)
            mentions = result.scalars().all()
            return mentions
        except Exception as e:
            raise Exception(f"Error fetching mentions by answer: {str(e)}")

    async def create(
        db: AsyncSession,
        answer_id: uuid.UUID,
        brand_id: uuid.UUID,
        mentioned: bool,
        position: int = None,
        context_snippet: str = None,
    ):
        try:
            mention = MentionTable(
                id=uuid.uuid4(),
                answer_id=answer_id,
                brand_id=brand_id,
                mentioned=mentioned,
                position=position,
                context_snippet=context_snippet,
            )
            db.add(mention)
            await db.commit()
            await db.refresh(mention)
            return mention
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error creating mention: {str(e)}")
