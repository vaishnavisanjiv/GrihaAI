from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.floor_plan import FloorPlanResponse, FloorPlanUploadResponse, ScaleCalibrationRequest
from app.services import floor_plan_service
from app.services.project_service import get_project

router = APIRouter()


@router.put("/{floor_plan_id}/scale", response_model=FloorPlanResponse)
def calibrate_floor_plan_scale(
    floor_plan_id: int,
    payload: ScaleCalibrationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    floor_plan = floor_plan_service.get_floor_plan_for_user(db, floor_plan_id, current_user.id)
    scale = None

    if payload.scale_pixels_per_mm and payload.scale_pixels_per_mm > 0:
        scale = payload.scale_pixels_per_mm
    elif (
        payload.x1 is not None
        and payload.y1 is not None
        and payload.x2 is not None
        and payload.y2 is not None
        and payload.known_distance_mm
    ):
        pixel_distance = ((payload.x2 - payload.x1) ** 2 + (payload.y2 - payload.y1) ** 2) ** 0.5
        if pixel_distance <= 0:
            raise HTTPException(status_code=400, detail="Calibration points must be different")
        if floor_plan.width and floor_plan.height and any(
            coordinate < 0 or coordinate > limit
            for coordinate, limit in (
                (payload.x1, floor_plan.width),
                (payload.x2, floor_plan.width),
                (payload.y1, floor_plan.height),
                (payload.y2, floor_plan.height),
            )
        ):
            raise HTTPException(status_code=400, detail="Calibration points must be inside the uploaded image")
        scale = pixel_distance / payload.known_distance_mm
    elif payload.preset_type:
        import json
        import statistics
        from app.models.analysis import AnalysisRun, DetectedElement
        latest_analysis = (
            db.query(AnalysisRun)
            .filter(AnalysisRun.floor_plan_id == floor_plan_id)
            .order_by(AnalysisRun.id.desc())
            .first()
        )
        target_real_m = payload.reference_real_length_m or 1.0
        door_widths_px = []
        if latest_analysis:
            doors = (
                db.query(DetectedElement)
                .filter(
                    DetectedElement.analysis_id == latest_analysis.id,
                    DetectedElement.element_type == "door",
                )
                .all()
            )
            for d in doors:
                if d.geometry_json:
                    try:
                        geom = json.loads(d.geometry_json)
                        bbox = geom.get("bbox_pixels")
                        if bbox and len(bbox) == 4:
                            _, _, bw, bh = bbox
                            door_widths_px.append(max(bw, bh))
                    except Exception:
                        pass
        if door_widths_px:
            ref_px = statistics.median(door_widths_px)
            scale = ref_px / (target_real_m * 1000.0)
        else:
            scale = 0.05
    else:
        raise HTTPException(status_code=400, detail="Provide two points with known distance or a calibration preset")

    from app.services.analysis_service import recalculate_floor_plan_scale_and_compliance
    return recalculate_floor_plan_scale_and_compliance(db, floor_plan.id, scale)


@router.get("/", response_model=List[FloorPlanResponse])
def list_floor_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return floor_plan_service.list_floor_plans_for_user(db, current_user.id)

@router.post("/upload", response_model=FloorPlanUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_floor_plan(
    project_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_project(db, project_id, current_user.id)

    floor_plan = await floor_plan_service.upload_floor_plan(db, project_id, file)
    return {
        "id": floor_plan.id,
        "message": "Floor plan uploaded successfully",
        "filename": floor_plan.original_filename,
    }

@router.post("/{floor_plan_id}/process", response_model=FloorPlanResponse)
def process_floor_plan(
    floor_plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    processed_floor_plan = floor_plan_service.process_floor_plan(db, floor_plan_id, current_user.id)
    return processed_floor_plan

@router.get("/{floor_plan_id}", response_model=FloorPlanResponse)
def get_floor_plan_info(
    floor_plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return floor_plan_service.get_floor_plan_for_user(db, floor_plan_id, current_user.id)

@router.get("/{floor_plan_id}/image")
def get_floor_plan_image(
    floor_plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    floor_plan = floor_plan_service.get_floor_plan_for_user(db, floor_plan_id, current_user.id)
    return FileResponse(floor_plan.storage_path)
