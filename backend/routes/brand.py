import uuid
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_db
from backend.service.auth_handler import AuthHandler
from backend.utils.schema.request import BrandCreate, BrandUpdate
from backend.utils.schema.response import BrandResponse
from backend.interactors.brand import create_brand as create_brand_interactor
from backend.interactors.brand import list_brands as list_brands_interactor
from backend.interactors.brand import update_brand as update_brand_interactor
from backend.interactors.brand import delete_brand as delete_brand_interactor

router = APIRouter(prefix="/api/projects/{project_id}/brands", tags=["brands"])

@router.post("", response_model=BrandResponse)
async def create_brand(
    project_id: uuid.UUID,
    payload: BrandCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await create_brand_interactor.call(db, project_id, payload, current_user)

@router.get("", response_model=List[BrandResponse])
async def list_brands(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await list_brands_interactor.call(db, project_id, current_user)

@router.put("/{brand_id}", response_model=BrandResponse)
async def update_brand(
    project_id: uuid.UUID,
    brand_id: uuid.UUID,
    payload: BrandUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await update_brand_interactor.call(db, project_id, brand_id, payload, current_user)

@router.delete("/{brand_id}")
async def delete_brand(
    project_id: uuid.UUID,
    brand_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await delete_brand_interactor.call(db, project_id, brand_id, current_user)
