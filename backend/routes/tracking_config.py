import uuid
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_db
from backend.service.auth_handler import AuthHandler
from backend.utils.schema.request import TrackingConfigCreate, TrackingConfigBulkCreate
from backend.utils.schema.response import TrackingConfigResponse
from backend.interactors.tracking_config import create_tracking_config as create_interactor
from backend.interactors.tracking_config import bulk_create_tracking_configs as bulk_create_interactor
from backend.interactors.tracking_config import list_tracking_configs as list_interactor
from backend.interactors.tracking_config import toggle_tracking_config as toggle_interactor

router = APIRouter(prefix="/api/projects/{project_id}/tracking-configs", tags=["tracking-configs"])

@router.post("", response_model=TrackingConfigResponse)
async def create_tracking_config(
    project_id: uuid.UUID,
    payload: TrackingConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await create_interactor.call(db, project_id, payload, current_user)

@router.post("/bulk", response_model=List[TrackingConfigResponse])
async def bulk_create_tracking_configs(
    project_id: uuid.UUID,
    payload: TrackingConfigBulkCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await bulk_create_interactor.call(db, project_id, payload, current_user)

@router.get("", response_model=List[TrackingConfigResponse])
async def list_tracking_configs(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await list_interactor.call(db, project_id, current_user)

@router.patch("/{tracking_config_id}/toggle", response_model=TrackingConfigResponse)
async def toggle_tracking_config(
    project_id: uuid.UUID,
    tracking_config_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await toggle_interactor.call(db, project_id, tracking_config_id, current_user)
