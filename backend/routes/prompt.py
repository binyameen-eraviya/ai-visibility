import uuid
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_db
from backend.service.auth_handler import AuthHandler
from backend.utils.schema.request import PromptCreate, PromptUpdate
from backend.utils.schema.response import PromptResponse
from backend.interactors.prompt import create_prompt as create_prompt_interactor
from backend.interactors.prompt import list_prompts as list_prompts_interactor
from backend.interactors.prompt import update_prompt as update_prompt_interactor
from backend.interactors.prompt import delete_prompt as delete_prompt_interactor
from backend.interactors.prompt import add_prompt_tag as add_prompt_tag_interactor
from backend.interactors.prompt import remove_prompt_tag as remove_prompt_tag_interactor

router = APIRouter(prefix="/api/projects/{project_id}/prompts", tags=["prompts"])

@router.post("", response_model=PromptResponse)
async def create_prompt(
    project_id: uuid.UUID,
    payload: PromptCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await create_prompt_interactor.call(db, project_id, payload, current_user)

@router.get("", response_model=List[PromptResponse])
async def list_prompts(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await list_prompts_interactor.call(db, project_id, current_user)

@router.put("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(
    project_id: uuid.UUID,
    prompt_id: uuid.UUID,
    payload: PromptUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await update_prompt_interactor.call(db, project_id, prompt_id, payload, current_user)

@router.delete("/{prompt_id}")
async def delete_prompt(
    project_id: uuid.UUID,
    prompt_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await delete_prompt_interactor.call(db, project_id, prompt_id, current_user)

@router.post("/{prompt_id}/tags/{tag_id}", response_model=PromptResponse)
async def add_prompt_tag(
    project_id: uuid.UUID,
    prompt_id: uuid.UUID,
    tag_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await add_prompt_tag_interactor.call(db, project_id, prompt_id, tag_id, current_user)

@router.delete("/{prompt_id}/tags/{tag_id}", response_model=PromptResponse)
async def remove_prompt_tag(
    project_id: uuid.UUID,
    prompt_id: uuid.UUID,
    tag_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await remove_prompt_tag_interactor.call(db, project_id, prompt_id, tag_id, current_user)
