from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.services import project_service

router = APIRouter()

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project: ProjectCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    return project_service.create_project(db, project, current_user.id)

@router.get("/", response_model=List[ProjectResponse])
def list_projects(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    return project_service.get_projects(db, current_user.id, skip, limit)

@router.get("/{project_id}/summary")
def get_project_summary(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return project_service.get_project_summary(db, project_id, current_user.id)

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    return project_service.get_project(db, project_id, current_user.id)

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int, 
    project_update: ProjectUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    return project_service.update_project(db, project_id, project_update, current_user.id)

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    project_service.delete_project(db, project_id, current_user.id)
    return None
