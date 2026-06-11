import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.migrations.answer import Answer as AnswerTable
from backend.utils.custom_exceptions import NotFound as DataNotFoundException

class Answer:
    async def find_by_id(db: AsyncSession, answer_id: uuid.UUID):
        try:
            stmt = select(AnswerTable).where(AnswerTable.id == answer_id)
            result = await db.execute(stmt)
            answer = result.scalars().first()
            if not answer:
                raise DataNotFoundException("Answer not found")
            return answer
        except DataNotFoundException:
            raise
        except Exception as e:
            raise Exception(f"Error fetching answer by ID: {str(e)}")

    async def find_by_scrape_run(db: AsyncSession, scrape_run_id: uuid.UUID):
        try:
            stmt = select(AnswerTable).where(AnswerTable.scrape_run_id == scrape_run_id)
            result = await db.execute(stmt)
            answer = result.scalars().first()
            if not answer:
                raise DataNotFoundException("Answer not found")
            return answer
        except DataNotFoundException:
            raise
        except Exception as e:
            raise Exception(f"Error fetching answer by scrape run: {str(e)}")

    async def create(
        db: AsyncSession,
        scrape_run_id: uuid.UUID,
        answer_text: str,
        parsed_at: datetime = None,
    ):
        try:
            answer = AnswerTable(
                id=uuid.uuid4(),
                scrape_run_id=scrape_run_id,
                answer_text=answer_text,
                parsed_at=parsed_at,
            )
            db.add(answer)
            await db.commit()
            await db.refresh(answer)
            return answer
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error creating answer: {str(e)}")
