import uuid
from datetime import date as date_type

from sqlalchemy import desc, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.enums import SourceType, UrlType
from backend.database.migrations.source_metric import SourceMetric as SourceMetricTable

class SourceMetric:
    async def upsert(
        db: AsyncSession,
        project_id: uuid.UUID,
        domain: str,
        date: date_type,
        citation_count: int,
        source_type: SourceType = SourceType.OTHER,
        url_type: UrlType = UrlType.OTHER,
        retrieved_pct: float = 0.0,
        citation_rate: float = 0.0,
    ):
        """Insert or update the citation count for this project + domain + date."""
        try:
            fields = {
                "citation_count": citation_count,
                "source_type": source_type,
                "url_type": url_type,
                "retrieved_pct": retrieved_pct,
                "citation_rate": citation_rate,
            }
            stmt = insert(SourceMetricTable).values(
                id=uuid.uuid4(),
                project_id=project_id,
                domain=domain,
                date=date,
                **fields,
            ).on_conflict_do_update(
                constraint="uq_source_metrics_project_domain_date",
                set_=fields,
            ).returning(SourceMetricTable)
            result = await db.execute(stmt)
            metric = result.scalars().first()
            await db.commit()
            return metric
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error upserting source metric: {str(e)}")

    async def get_report(
        db: AsyncSession,
        project_id: uuid.UUID,
        start_date: date_type,
        end_date: date_type,
        source_type: SourceType = None,
    ):
        """Dashboard query: cited domains for a project over a date range."""
        try:
            stmt = select(SourceMetricTable).where(
                SourceMetricTable.project_id == project_id,
                SourceMetricTable.date >= start_date,
                SourceMetricTable.date <= end_date,
            )
            if source_type is not None:
                stmt = stmt.where(SourceMetricTable.source_type == source_type)
            stmt = stmt.order_by(SourceMetricTable.date, desc(SourceMetricTable.citation_count))

            result = await db.execute(stmt)
            metrics = result.scalars().all()
            return metrics
        except Exception as e:
            raise Exception(f"Error fetching source metrics report: {str(e)}")
