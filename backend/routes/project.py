import uuid
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_db
from backend.service.auth_handler import AuthHandler
from backend.utils.schema.request import ProjectCreate, ProjectUpdate
from backend.utils.schema.response import ProjectResponse
from backend.interactors.project import create_project as create_project_interactor
from backend.interactors.project import list_projects as list_projects_interactor
from backend.interactors.project import get_project as get_project_interactor
from backend.interactors.project import update_project as update_project_interactor
from backend.interactors.project import delete_project as delete_project_interactor

router = APIRouter(prefix="/api/projects", tags=["projects"])

@router.post("", response_model=ProjectResponse)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await create_project_interactor.call(db, payload, current_user)

@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await list_projects_interactor.call(db, current_user)

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await get_project_interactor.call(db, project_id, current_user)

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await update_project_interactor.call(db, project_id, payload, current_user)

@router.delete("/{project_id}")
async def delete_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthHandler.get_current_user),
):
    return await delete_project_interactor.call(db, project_id, current_user)
