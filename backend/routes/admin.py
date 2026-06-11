import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_db
from backend.service.auth_handler import AuthHandler
from backend.utils.schema.request import ScrapeAccountCreate
from backend.utils.schema.response import ScrapeAccountResponse, VerificationResponse
from backend.interactors.admin import create_scrape_account as create_scrape_account_interactor
from backend.interactors.admin import list_scrape_accounts as list_scrape_accounts_interactor
from backend.interactors.admin import verify_user as verify_user_interactor

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.post("/scrape-accounts", response_model=ScrapeAccountResponse)
async def create_scrape_account(
    payload: ScrapeAccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_super_admin),
):
    return await create_scrape_account_interactor.call(db, payload, current_user)

@router.get("/scrape-accounts", response_model=List[ScrapeAccountResponse])
async def list_scrape_accounts(
    platform_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_super_admin),
):
    return await list_scrape_accounts_interactor.call(db, current_user, platform_id=platform_id)

@router.post("/users/{user_id}/verify", response_model=VerificationResponse)
async def verify_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_super_admin),
):
    return await verify_user_interactor.call(db, user_id, current_user)
