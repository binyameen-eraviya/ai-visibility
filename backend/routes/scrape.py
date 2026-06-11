import uuid
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_db
from backend.service.auth_handler import AuthHandler
from backend.utils.schema.request import ScrapeRunRequest
from backend.utils.schema.response import ScrapeRunResponse, ScrapeRunDetailResponse
from backend.interactors.scrape import run_now as run_now_interactor
from backend.interactors.scrape import list_runs as list_runs_interactor
from backend.interactors.scrape import get_run as get_run_interactor

router = APIRouter(prefix="/api/projects/{project_id}", tags=["scrape"])

@router.post("/prompts/{prompt_id}/run", response_model=ScrapeRunResponse)
async def run_prompt_now(
    project_id: uuid.UUID,
    prompt_id: uuid.UUID,
    payload: ScrapeRunRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await run_now_interactor.call(db, project_id, prompt_id, payload, current_user)

@router.get("/runs", response_model=List[ScrapeRunResponse])
async def list_runs(
    project_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await list_runs_interactor.call(db, project_id, current_user, limit=limit, offset=offset)

@router.get("/runs/{run_id}", response_model=ScrapeRunDetailResponse)
async def get_run(
    project_id: uuid.UUID,
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await get_run_interactor.call(db, project_id, run_id, current_user)
