import uuid
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_db
from backend.utils.enums import SourceType, UrlType
from backend.service.auth_handler import AuthHandler
from backend.utils.schema.response import (
    DailyMetricResponse,
    SourceMetricResponse,
    GapAnalysisResponse,
    BrandInsightResponse,
)
from backend.interactors.reports import daily_metrics_report as daily_metrics_interactor
from backend.interactors.reports import source_metrics_report as source_metrics_interactor
from backend.interactors.reports import gap_analysis_report as gap_analysis_interactor
from backend.interactors.reports import brand_insights_report as brand_insights_interactor

router = APIRouter(prefix="/api/projects/{project_id}/reports", tags=["reports"])

@router.get("/daily-metrics", response_model=List[DailyMetricResponse])
async def get_daily_metrics(
    project_id: uuid.UUID,
    start_date: date = Query(...),
    end_date: date = Query(...),
    brand_id: Optional[uuid.UUID] = Query(None),
    platform_id: Optional[uuid.UUID] = Query(None),
    country_id: Optional[uuid.UUID] = Query(None),
    group_by: Optional[str] = Query(None, description="date | platform | brand"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await daily_metrics_interactor.call(
        db, project_id, start_date, end_date, current_user,
        brand_id=brand_id, platform_id=platform_id, country_id=country_id,
        group_by=group_by,
    )

@router.get("/source-metrics", response_model=List[SourceMetricResponse])
async def get_source_metrics(
    project_id: uuid.UUID,
    start_date: date = Query(...),
    end_date: date = Query(...),
    source_type: Optional[SourceType] = Query(None, description="domain type filter"),
    url_type: Optional[UrlType] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await source_metrics_interactor.call(
        db, project_id, start_date, end_date, current_user,
        source_type=source_type, url_type=url_type,
    )

@router.get("/gap-analysis", response_model=List[GapAnalysisResponse])
async def get_gap_analysis(
    project_id: uuid.UUID,
    start_date: date = Query(...),
    end_date: date = Query(...),
    min_competitors: int = Query(0, ge=0, description="min competitor mentions (Peec's 'Min N Competitor')"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await gap_analysis_interactor.call(
        db, project_id, start_date, end_date, current_user,
        min_competitors=min_competitors,
    )

@router.get("/brand-insights", response_model=List[BrandInsightResponse])
async def get_brand_insights(
    project_id: uuid.UUID,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await brand_insights_interactor.call(
        db, project_id, start_date, end_date, current_user,
    )
