import uuid
from datetime import date as date_type

from sqlalchemy import desc, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.migrations.gap_score import GapScore as GapScoreTable


class GapScore:
    async def upsert(
        db: AsyncSession,
        project_id: uuid.UUID,
        domain: str,
        date: date_type,
        gap_score: int,
        competitor_mentions: int,
    ):
        """Insert or update the gap score for this project + domain + date."""
        try:
            fields = {"gap_score": gap_score, "competitor_mentions": competitor_mentions}
            stmt = insert(GapScoreTable).values(
                id=uuid.uuid4(),
                project_id=project_id,
                domain=domain,
                date=date,
                **fields,
            ).on_conflict_do_update(
                constraint="uq_gap_scores_project_domain_date",
                set_=fields,
            ).returning(GapScoreTable)
            result = await db.execute(stmt)
            score = result.scalars().first()
            await db.commit()
            return score
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error upserting gap score: {str(e)}")

    async def get_report(
        db: AsyncSession,
        project_id: uuid.UUID,
        start_date: date_type,
        end_date: date_type,
        min_competitors: int = 0,
    ):
        """Gap analysis: domains ranked by gap_score over a date range."""
        try:
            stmt = select(GapScoreTable).where(
                GapScoreTable.project_id == project_id,
                GapScoreTable.date >= start_date,
                GapScoreTable.date <= end_date,
            )
            if min_competitors:
                stmt = stmt.where(GapScoreTable.competitor_mentions >= min_competitors)
            stmt = stmt.order_by(desc(GapScoreTable.gap_score))

            result = await db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            raise Exception(f"Error fetching gap scores report: {str(e)}")
