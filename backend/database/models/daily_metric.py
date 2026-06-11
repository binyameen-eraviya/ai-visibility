import uuid
from datetime import date as date_type

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.migrations.daily_metric import DailyMetric as DailyMetricTable

class DailyMetric:
    async def upsert(
        db: AsyncSession,
        project_id: uuid.UUID,
        brand_id: uuid.UUID,
        platform_id: uuid.UUID,
        country_id: uuid.UUID,
        date: date_type,
        visibility_pct: float,
        share_of_voice: float,
        total_runs: int,
        mention_count: int,
        avg_position: float = None,
        avg_sentiment: float = None,
    ):
        """Insert or update the metric row for this scope + date."""
        try:
            metrics = {
                "visibility_pct": visibility_pct,
                "avg_position": avg_position,
                "avg_sentiment": avg_sentiment,
                "share_of_voice": share_of_voice,
                "total_runs": total_runs,
                "mention_count": mention_count,
            }
            stmt = insert(DailyMetricTable).values(
                id=uuid.uuid4(),
                project_id=project_id,
                brand_id=brand_id,
                platform_id=platform_id,
                country_id=country_id,
                date=date,
                **metrics,
            ).on_conflict_do_update(
                constraint="uq_daily_metrics_scope_date",
                set_=metrics,
            ).returning(DailyMetricTable)
            result = await db.execute(stmt)
            metric = result.scalars().first()
            await db.commit()
            return metric
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error upserting daily metric: {str(e)}")

    async def get_report(
        db: AsyncSession,
        project_id: uuid.UUID,
        start_date: date_type,
        end_date: date_type,
        brand_id: uuid.UUID = None,
        platform_id: uuid.UUID = None,
        country_id: uuid.UUID = None,
    ):
        """Dashboard query: metrics for a project over a date range."""
        try:
            stmt = select(DailyMetricTable).where(
                DailyMetricTable.project_id == project_id,
                DailyMetricTable.date >= start_date,
                DailyMetricTable.date <= end_date,
            )
            if brand_id is not None:
                stmt = stmt.where(DailyMetricTable.brand_id == brand_id)
            if platform_id is not None:
                stmt = stmt.where(DailyMetricTable.platform_id == platform_id)
            if country_id is not None:
                stmt = stmt.where(DailyMetricTable.country_id == country_id)
            stmt = stmt.order_by(DailyMetricTable.date)

            result = await db.execute(stmt)
            metrics = result.scalars().all()
            return metrics
        except Exception as e:
            raise Exception(f"Error fetching daily metrics report: {str(e)}")
