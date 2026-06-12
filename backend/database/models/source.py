import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.enums import SourceType, UrlType
from backend.database.migrations.source import Source as SourceTable

class Source:
    async def find_by_answer(db: AsyncSession, answer_id: uuid.UUID):
        try:
            stmt = select(SourceTable).where(
                SourceTable.answer_id == answer_id
            ).order_by(SourceTable.position)
            result = await db.execute(stmt)
            sources = result.scalars().all()
            return sources
        except Exception as e:
            raise Exception(f"Error fetching sources by answer: {str(e)}")

    async def create(
        db: AsyncSession,
        answer_id: uuid.UUID,
        url: str,
        domain: str,
        source_type: SourceType = SourceType.OTHER,
        url_type: UrlType = UrlType.OTHER,
        position: int = None,
    ):
        try:
            source = SourceTable(
                id=uuid.uuid4(),
                answer_id=answer_id,
                url=url,
                domain=domain,
                source_type=source_type,
                url_type=url_type,
                position=position,
            )
            db.add(source)
            await db.commit()
            await db.refresh(source)
            return source
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error creating source: {str(e)}")
