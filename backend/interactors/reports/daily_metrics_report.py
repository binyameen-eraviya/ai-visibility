import uuid
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.daily_metric import DailyMetric as DailyMetricDB
from backend.interactors.helpers.project_access import verify_project_access

async def call(
    db: AsyncSession,
    project_id: uuid.UUID,
    start_date: date,
    end_date: date,
    current_user,
    brand_id: uuid.UUID = None,
    platform_id: uuid.UUID = None,
    country_id: uuid.UUID = None,
):
    await verify_project_access(db, project_id, current_user)

    try:
        metrics = await DailyMetricDB.get_report(
            db,
            project_id=project_id,
            start_date=start_date,
            end_date=end_date,
            brand_id=brand_id,
            platform_id=platform_id,
            country_id=country_id,
        )
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
