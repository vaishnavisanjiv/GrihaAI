import json
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.analysis import (
    ComplianceResult,
    DetectedElement,
    Room,
    SpatialEdge,
    SpatialEdgeReview,
)
from app.schemas.analysis import (
    AnalysisResponse,
    AnalysisStatusResponse,
    AnalysisSummaryResponse,
    ComplianceResultResponse,
    DetectedElementResponse,
    RoomResponse,
    SpatialEdgeResponse,
    SpatialEdgeReviewRequest,
)
from app.services import analysis_service
from app.services.floor_plan_service import get_floor_plan_for_user
from app.services import model_analysis_service
from app.services.model_analysis_service import has_trained_model

router = APIRouter()


def _run_analysis_in_background(analysis_id: int, floor_plan_id: int) -> None:
    """
    Background worker: opens its own DB session so it is independent of the
    request session, runs the full model analysis, then closes the session.
    Called by FastAPI BackgroundTasks after the HTTP response has been sent.
    """
    db = SessionLocal()
    try:
        from app.models.analysis import AnalysisRun
        from app.models.floor_plan import FloorPlan

        analysis = db.query(AnalysisRun).filter(AnalysisRun.id == analysis_id).first()
        floor_plan = db.query(FloorPlan).filter(FloorPlan.id == floor_plan_id).first()
        if analysis is None or floor_plan is None:
            return
        try:
            model_analysis_service.run_trained_analysis(db, analysis, floor_plan)
        except HTTPException:
            # run_trained_analysis already updated analysis.status to FAILED
            pass
        except Exception as exc:  # noqa: BLE001 — catch-all for background safety
            db.rollback()
            analysis.status = "FAILED"
            analysis.error_message = str(exc)[:1000]
            db.commit()
    finally:
        db.close()


@router.post(
    "/{floor_plan_id}/start",
    response_model=AnalysisResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start a floor-plan analysis (async)",
    description=(
        "Enqueues an analysis and returns 202 Accepted immediately. "
        "Poll GET /{analysis_id}/status until status is COMPLETED or FAILED, "
        "then fetch the full summary from GET /{analysis_id}."
    ),
)
def start_analysis(
    floor_plan_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_floor_plan_for_user(db, floor_plan_id, current_user.id)
    if not (has_trained_model() and model_analysis_service.has_trained_model()):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "No trained floor-plan model is installed. Train a CubiCasa5K model "
                "and place backend/models/floorplan_unet.pt before starting analysis."
            ),
        )

    analysis = analysis_service.start_analysis(db, floor_plan_id, current_user.id)
    background_tasks.add_task(
        _run_analysis_in_background, analysis.id, floor_plan_id
    )
    return analysis


@router.get(
    "/{analysis_id}/status",
    response_model=AnalysisStatusResponse,
    summary="Poll analysis status",
    description=(
        "Returns the current status of an analysis without loading its full results. "
        "Intended for polling after POST /{floor_plan_id}/start returns 202. "
        "Status values: PENDING → RUNNING → COMPLETED | FAILED."
    ),
)
def get_analysis_status(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    analysis = analysis_service.get_analysis_for_user(db, analysis_id, current_user.id)
    return analysis


@router.get("/{analysis_id}", response_model=AnalysisSummaryResponse)
def get_analysis_summary(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return analysis_service.get_analysis_summary(db, analysis_id, current_user.id)

@router.get("/{analysis_id}/elements", response_model=List[DetectedElementResponse])
def get_elements(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    analysis_service.get_analysis_for_user(db, analysis_id, current_user.id)
    return db.query(DetectedElement).filter(DetectedElement.analysis_id == analysis_id).all()

@router.get("/{analysis_id}/rooms", response_model=List[RoomResponse])
def get_rooms(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    analysis_service.get_analysis_for_user(db, analysis_id, current_user.id)
    return db.query(Room).filter(Room.analysis_id == analysis_id).all()

@router.get("/{analysis_id}/graph", response_model=List[SpatialEdgeResponse])
def get_graph(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    analysis_service.get_analysis_for_user(db, analysis_id, current_user.id)
    return db.query(SpatialEdge).filter(SpatialEdge.analysis_id == analysis_id).all()

@router.put("/{analysis_id}/graph/{edge_id}/review", response_model=SpatialEdgeResponse)
def review_spatial_edge(
    analysis_id: int,
    edge_id: int,
    request: SpatialEdgeReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    analysis_service.get_analysis_for_user(db, analysis_id, current_user.id)
    edge = (
        db.query(SpatialEdge)
        .filter(SpatialEdge.id == edge_id, SpatialEdge.analysis_id == analysis_id)
        .first()
    )
    if edge is None:
        raise HTTPException(status_code=404, detail="Spatial candidate not found")
    if edge.relationship_type not in {"ADJACENT_TO_CANDIDATE", "PROXIMATE_TO"}:
        raise HTTPException(status_code=409, detail="Only spatial relationship candidates can be reviewed")

    try:
        properties = json.loads(edge.properties_json or "{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=409,
            detail="Spatial candidate metadata is invalid and cannot be reviewed",
        ) from exc
    if not isinstance(properties, dict) or properties.get("review_required") is not True:
        raise HTTPException(status_code=409, detail="Spatial candidate is not marked for review")

    review = SpatialEdgeReview(
        spatial_edge_id=edge.id,
        reviewer_user_id=current_user.id,
        review_status=request.review_status,
    )
    db.add(review)
    properties.update(
        {
            "review_status": request.review_status,
            "reviewed_by_user_id": current_user.id,
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    edge.properties_json = json.dumps(properties)
    db.commit()
    db.refresh(edge)
    db.refresh(review)
    return edge

@router.get("/{analysis_id}/compliance", response_model=List[ComplianceResultResponse])
def get_compliance(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    analysis = analysis_service.get_analysis_for_user(db, analysis_id, current_user.id)
    floor_plan = db.query(FloorPlan).filter(FloorPlan.id == analysis.floor_plan_id).first()
    is_calibrated = bool(
        floor_plan
        and floor_plan.scale_source == "user-calibrated"
        and floor_plan.scale_pixels_per_mm
        and floor_plan.scale_pixels_per_mm > 0
    )
    results = db.query(ComplianceResult).filter(ComplianceResult.analysis_id == analysis_id).all()
    return analysis_service.mark_findings_unassessed(results, scale_calibrated=is_calibrated)

@router.get("/{analysis_id}/recommendations")
def get_recommendations(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    analysis = analysis_service.get_analysis_for_user(db, analysis_id, current_user.id)
    floor_plan = db.query(FloorPlan).filter(FloorPlan.id == analysis.floor_plan_id).first()
    is_calibrated = bool(
        floor_plan
        and floor_plan.scale_source == "user-calibrated"
        and floor_plan.scale_pixels_per_mm
        and floor_plan.scale_pixels_per_mm > 0
    )
    results = db.query(ComplianceResult).filter(ComplianceResult.analysis_id == analysis_id).all()
    analysis_service.mark_findings_unassessed(results, scale_calibrated=is_calibrated)
    recommendations = list(dict.fromkeys(
        item.recommendation for item in results if item.recommendation
    ))
    return {"recommendations": recommendations}
