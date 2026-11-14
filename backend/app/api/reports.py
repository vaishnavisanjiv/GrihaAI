import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.report_service import generate_pdf_report, generate_report as build_report
from app.services.analysis_service import get_analysis_for_user

router = APIRouter()

@router.get("/{analysis_id}")
def generate_report(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_analysis_for_user(db, analysis_id, current_user.id)
    try:
        return build_report(db, analysis_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@router.get("/{analysis_id}/download")
def download_report_pdf(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_analysis_for_user(db, analysis_id, current_user.id)
    try:
        output_path = generate_pdf_report(db, analysis_id)
        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename=f"buildguard-report-{analysis_id}.pdf",
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
