import uuid
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_db
from backend.service.auth_handler import AuthHandler
from backend.utils.schema.request import TopicCreate
from backend.utils.schema.response import TopicResponse
from backend.interactors.topic import create_topic as create_topic_interactor
from backend.interactors.topic import list_topics as list_topics_interactor
from backend.interactors.topic import delete_topic as delete_topic_interactor

router = APIRouter(prefix="/api/projects/{project_id}/topics", tags=["topics"])

@router.post("", response_model=TopicResponse)
async def create_topic(
    project_id: uuid.UUID,
    payload: TopicCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await create_topic_interactor.call(db, project_id, payload, current_user)

@router.get("", response_model=List[TopicResponse])
async def list_topics(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await list_topics_interactor.call(db, project_id, current_user)

@router.delete("/{topic_id}")
async def delete_topic(
    project_id: uuid.UUID,
    topic_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await delete_topic_interactor.call(db, project_id, topic_id, current_user)
