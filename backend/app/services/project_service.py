from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Dict, Any
from app.models.project import Project
from app.models.floor_plan import FloorPlan
from app.models.analysis import AnalysisRun, ComplianceResult
from app.schemas.project import ProjectCreate, ProjectUpdate

def create_project(db: Session, project: ProjectCreate, user_id: int) -> Project:
    db_project = Project(**project.model_dump(), user_id=user_id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def get_projects(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Project]:
    return db.query(Project).filter(Project.user_id == user_id).offset(skip).limit(limit).all()

def get_project(db: Session, project_id: int, user_id: int) -> Project:
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def get_project_summary(db: Session, project_id: int, user_id: int) -> Dict[str, Any]:
    project = get_project(db, project_id, user_id)
    plans = db.query(FloorPlan).filter(FloorPlan.project_id == project_id).all()
    plan_ids = [plan.id for plan in plans]
    analyses = db.query(AnalysisRun).filter(AnalysisRun.floor_plan_id.in_(plan_ids)).all() if plan_ids else []
    compliance_results = []
    if analyses:
        analysis_ids = [analysis.id for analysis in analyses]
        compliance_results = db.query(ComplianceResult).filter(ComplianceResult.analysis_id.in_(analysis_ids)).all()

    return {
        "project_id": project.id,
        "project_name": project.name,
        "plan_count": len(plans),
        "analysis_count": len(analyses),
        "not_assessed_count": len(compliance_results),
    }


def update_project(db: Session, project_id: int, project_update: ProjectUpdate, user_id: int) -> Project:
    project = get_project(db, project_id, user_id)
    update_data = project_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project

def delete_project(db: Session, project_id: int, user_id: int) -> bool:
    project = get_project(db, project_id, user_id)
    db.delete(project)
    db.commit()
    return True
