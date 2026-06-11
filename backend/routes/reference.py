from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_db
from backend.service.auth_handler import AuthHandler
from backend.utils.schema.response import PlatformResponse, CountryResponse
from backend.database.models.platform import Platform as PlatformDB
from backend.database.models.country import Country as CountryDB

router = APIRouter(prefix="/api", tags=["reference"])

@router.get("/platforms", response_model=List[PlatformResponse])
async def list_platforms(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await PlatformDB.get_list(db, active_only=False)

@router.get("/countries", response_model=List[CountryResponse])
async def list_countries(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await CountryDB.get_list(db, active_only=False)
