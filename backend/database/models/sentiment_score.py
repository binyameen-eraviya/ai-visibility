import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.migrations.sentiment_score import SentimentScore as SentimentScoreTable

class SentimentScore:
    async def find_by_answer(db: AsyncSession, answer_id: uuid.UUID):
        try:
            stmt = select(SentimentScoreTable).where(SentimentScoreTable.answer_id == answer_id)
            result = await db.execute(stmt)
            scores = result.scalars().all()
            return scores
        except Exception as e:
            raise Exception(f"Error fetching sentiment scores by answer: {str(e)}")

    async def create(
        db: AsyncSession,
        answer_id: uuid.UUID,
        brand_id: uuid.UUID,
        score: int,
        reasoning: str = None,
    ):
        try:
            sentiment = SentimentScoreTable(
                id=uuid.uuid4(),
                answer_id=answer_id,
                brand_id=brand_id,
                score=score,
                reasoning=reasoning,
            )
            db.add(sentiment)
            await db.commit()
            await db.refresh(sentiment)
            return sentiment
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error creating sentiment score: {str(e)}")
