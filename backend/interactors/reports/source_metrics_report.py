import uuid
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.enums import SourceType, UrlType
from backend.database.models.source_metric import SourceMetric as SourceMetricDB
from backend.interactors.helpers.project_access import verify_project_access

async def call(
    db: AsyncSession,
    project_id: uuid.UUID,
    start_date: date,
    end_date: date,
    current_user,
    source_type: SourceType = None,
    url_type: UrlType = None,
):
    await verify_project_access(db, project_id, current_user)

    try:
        metrics = await SourceMetricDB.get_report(
            db,
            project_id=project_id,
            start_date=start_date,
            end_date=end_date,
            source_type=source_type,
            url_type=url_type,
        )
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
