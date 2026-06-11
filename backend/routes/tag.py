import uuid
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_db
from backend.service.auth_handler import AuthHandler
from backend.utils.schema.request import TagCreate
from backend.utils.schema.response import TagResponse
from backend.interactors.tag import create_tag as create_tag_interactor
from backend.interactors.tag import list_tags as list_tags_interactor
from backend.interactors.tag import delete_tag as delete_tag_interactor

router = APIRouter(prefix="/api/projects/{project_id}/tags", tags=["tags"])

@router.post("", response_model=TagResponse)
async def create_tag(
    project_id: uuid.UUID,
    payload: TagCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await create_tag_interactor.call(db, project_id, payload, current_user)

@router.get("", response_model=List[TagResponse])
async def list_tags(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await list_tags_interactor.call(db, project_id, current_user)

@router.delete("/{tag_id}")
async def delete_tag(
    project_id: uuid.UUID,
    tag_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await delete_tag_interactor.call(db, project_id, tag_id, current_user)
