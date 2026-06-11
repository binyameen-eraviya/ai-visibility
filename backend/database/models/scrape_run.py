import uuid
from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.enums import ScrapeStatus
from backend.database.migrations.scrape_run import ScrapeRun as ScrapeRunTable
from backend.database.migrations.tracking_config import TrackingConfig as TrackingConfigTable
from backend.utils.custom_exceptions import NotFound as DataNotFoundException

class ScrapeRun:
    async def find_by_id(db: AsyncSession, scrape_run_id: uuid.UUID):
        try:
            stmt = select(ScrapeRunTable).where(ScrapeRunTable.id == scrape_run_id)
            result = await db.execute(stmt)
            run = result.scalars().first()
            if not run:
                raise DataNotFoundException("Scrape run not found")
            return run
        except DataNotFoundException:
            raise
        except Exception as e:
            raise Exception(f"Error fetching scrape run by ID: {str(e)}")

    async def find_by_id_and_project(db: AsyncSession, scrape_run_id: uuid.UUID, project_id: uuid.UUID):
        """Fetch a run only if it belongs to the given project (via its config)."""
        try:
            stmt = (
                select(ScrapeRunTable)
                .join(TrackingConfigTable, ScrapeRunTable.tracking_config_id == TrackingConfigTable.id)
                .where(
                    ScrapeRunTable.id == scrape_run_id,
                    TrackingConfigTable.project_id == project_id,
                )
            )
            result = await db.execute(stmt)
            run = result.scalars().first()
            if not run:
                raise DataNotFoundException("Scrape run not found")
            return run
        except DataNotFoundException:
            raise
        except Exception as e:
            raise Exception(f"Error fetching scrape run by ID and project: {str(e)}")

    async def find_by_project(db: AsyncSession, project_id: uuid.UUID, limit: int = 50, offset: int = 0):
        """Recent runs for a project, newest first, paginated."""
        try:
            stmt = (
                select(ScrapeRunTable)
                .join(TrackingConfigTable, ScrapeRunTable.tracking_config_id == TrackingConfigTable.id)
                .where(TrackingConfigTable.project_id == project_id)
                .order_by(desc(ScrapeRunTable.created_at))
                .limit(limit)
                .offset(offset)
            )
            result = await db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            raise Exception(f"Error fetching scrape runs by project: {str(e)}")

    async def find_by_tracking_config(db: AsyncSession, tracking_config_id: uuid.UUID):
        try:
            stmt = select(ScrapeRunTable).where(
                ScrapeRunTable.tracking_config_id == tracking_config_id
            ).order_by(desc(ScrapeRunTable.created_at))
            result = await db.execute(stmt)
            runs = result.scalars().all()
            return runs
        except Exception as e:
            raise Exception(f"Error fetching scrape runs by tracking config: {str(e)}")

    async def create(
        db: AsyncSession,
        tracking_config_id: uuid.UUID,
        status: ScrapeStatus = ScrapeStatus.PENDING,
        raw_storage_path: str = None,
        screenshot_path: str = None,
        error: str = None,
        account_id: uuid.UUID = None,
        duration_ms: int = None,
        scraped_at: datetime = None,
    ):
        try:
            run = ScrapeRunTable(
                id=uuid.uuid4(),
                tracking_config_id=tracking_config_id,
                status=status,
                raw_storage_path=raw_storage_path,
                screenshot_path=screenshot_path,
                error=error,
                account_id=account_id,
                duration_ms=duration_ms,
                scraped_at=scraped_at,
            )
            db.add(run)
            await db.commit()
            await db.refresh(run)
            return run
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error creating scrape run: {str(e)}")

    async def update(
        db: AsyncSession,
        scrape_run_id: uuid.UUID,
        status: ScrapeStatus = None,
        raw_storage_path: str = None,
        screenshot_path: str = None,
        error: str = None,
        account_id: uuid.UUID = None,
        duration_ms: int = None,
        scraped_at: datetime = None,
    ):
        """Patch the mutable fields of a run; only non-None values are applied."""
        try:
            run = await ScrapeRun.find_by_id(db, scrape_run_id)

            if status is not None:
                run.status = status
            if raw_storage_path is not None:
                run.raw_storage_path = raw_storage_path
            if screenshot_path is not None:
                run.screenshot_path = screenshot_path
            if error is not None:
                run.error = error
            if account_id is not None:
                run.account_id = account_id
            if duration_ms is not None:
                run.duration_ms = duration_ms
            if scraped_at is not None:
                run.scraped_at = scraped_at

            await db.commit()
            await db.refresh(run)
            return run
        except DataNotFoundException:
            raise
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error updating scrape run: {str(e)}")
