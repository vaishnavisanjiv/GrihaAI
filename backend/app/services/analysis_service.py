import json
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.analysis import AnalysisRun, DetectedElement, Room, SpatialEdge, ComplianceResult
from app.models.floor_plan import FloorPlan
from app.models.project import Project


def mark_findings_unassessed(
    results: list[ComplianceResult],
    scale_calibrated: bool = False,
) -> list[ComplianceResult]:
    """
    If scale is calibrated and checks were evaluated, preserve the evaluated results.
    If scale is uncalibrated, ensure uncalibrated checks indicate calibration requirement.
    """
    if scale_calibrated:
        return results

    for result in results:
        if result.status not in ("PASS", "FAIL", "WARNING"):
            result.status = "NOT_ASSESSED"
            result.severity = "UNVERIFIED"
            result.message = (
                "Prototype finding retained for context; not assessed against a verified code provision."
            )
            result.explanation = (
                "Drawing scale is not yet calibrated. Set scale (e.g. enter known door width or reference dimension) "
                "to calculate corridor width and room clearances against NBC 2016 norms."
            )
            result.recommendation = (
                "Calibrate drawing scale on the dashboard to enable automated NBC 2016 compliance checks."
            )
    return results


def recalculate_floor_plan_scale_and_compliance(
    db: Session,
    floor_plan_id: int,
    scale_pixels_per_mm: float,
) -> FloorPlan:
    """
    Recalculates metric dimensions (width_m, length_m, area_sqm) for all detected rooms and elements,
    and runs NBC 2016 rule evaluation.
    """
    from app.services.rule_engine import evaluate_rules

    floor_plan = db.query(FloorPlan).filter(FloorPlan.id == floor_plan_id).first()
    if not floor_plan:
        raise HTTPException(status_code=404, detail="Floor plan not found")

    floor_plan.scale_pixels_per_mm = scale_pixels_per_mm
    floor_plan.scale_source = "user-calibrated"

    analyses = db.query(AnalysisRun).filter(AnalysisRun.floor_plan_id == floor_plan_id).all()
    for analysis in analyses:
        rooms = db.query(Room).filter(Room.analysis_id == analysis.id).all()
        elements = db.query(DetectedElement).filter(DetectedElement.analysis_id == analysis.id).all()

        for room in rooms:
            if room.polygon_json:
                try:
                    poly = json.loads(room.polygon_json)
                    if poly and len(poly) >= 3:
                        xs = [p[0] for p in poly]
                        ys = [p[1] for p in poly]
                        bw = max(xs) - min(xs)
                        bh = max(ys) - min(ys)
                        room.width_m = round(float(min(bw, bh) / scale_pixels_per_mm / 1000.0), 2)
                        room.length_m = round(float(max(bw, bh) / scale_pixels_per_mm / 1000.0), 2)
                except Exception:
                    pass
            if room.area_pixels:
                room.area_sqm = round(float(room.area_pixels / (scale_pixels_per_mm ** 2) / 1_000_000.0), 2)

        for element in elements:
            if element.geometry_json:
                try:
                    geom = json.loads(element.geometry_json)
                    bbox = geom.get("bbox_pixels")
                    if bbox and len(bbox) == 4:
                        _, _, bw, bh = bbox
                        geom["width_m"] = round(float(max(bw, bh) / scale_pixels_per_mm / 1000.0), 2)
                        element.geometry_json = json.dumps(geom)
                    props = json.loads(element.properties_json or "{}")
                    props["measurement_unit"] = "meters"
                    props["scale_calibrated"] = True
                    element.properties_json = json.dumps(props)
                except Exception:
                    pass

        # Clear existing compliance results and re-evaluate with calibrated scale
        db.query(ComplianceResult).filter(ComplianceResult.analysis_id == analysis.id).delete()
        new_findings = evaluate_rules(
            {"rooms": rooms, "elements": elements},
            analysis_id=analysis.id,
            scale_calibrated=True,
            scale_pixels_per_mm=scale_pixels_per_mm,
        )
        db.add_all(new_findings)

    db.commit()
    db.refresh(floor_plan)
    return floor_plan


def get_analysis_for_user(db: Session, analysis_id: int, user_id: int) -> AnalysisRun:
    analysis = (
        db.query(AnalysisRun)
        .join(FloorPlan, AnalysisRun.floor_plan_id == FloorPlan.id)
        .join(Project, FloorPlan.project_id == Project.id)
        .filter(AnalysisRun.id == analysis_id, Project.user_id == user_id)
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


def start_analysis(db: Session, floor_plan_id: int, user_id: int) -> AnalysisRun:
    floor_plan = (
        db.query(FloorPlan)
        .join(Project, FloorPlan.project_id == Project.id)
        .filter(FloorPlan.id == floor_plan_id, Project.user_id == user_id)
        .first()
    )
    if not floor_plan:
        raise HTTPException(status_code=404, detail="Floor plan not found")

    analysis = AnalysisRun(
        floor_plan_id=floor_plan_id,
        status="PENDING",
        cv_method="cubicasa5k-unet-segmentation",
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def get_analysis_summary(db: Session, analysis_id: int, user_id: int):
    analysis = get_analysis_for_user(db, analysis_id, user_id)
    floor_plan = db.query(FloorPlan).filter(FloorPlan.id == analysis.floor_plan_id).first()

    is_calibrated = bool(
        floor_plan
        and floor_plan.scale_source == "user-calibrated"
        and floor_plan.scale_pixels_per_mm
        and floor_plan.scale_pixels_per_mm > 0
    )

    rooms = db.query(Room).filter(Room.analysis_id == analysis_id).all()
    elements = db.query(DetectedElement).filter(DetectedElement.analysis_id == analysis_id).all()
    spatial_edges = db.query(SpatialEdge).filter(SpatialEdge.analysis_id == analysis_id).all()
    compliance = db.query(ComplianceResult).filter(ComplianceResult.analysis_id == analysis_id).all()

    return {
        "analysis": analysis,
        "rooms": rooms,
        "elements": elements,
        "spatial_edges": spatial_edges,
        "compliance_results": mark_findings_unassessed(compliance, scale_calibrated=is_calibrated),
        "scale_calibrated": is_calibrated,
        "scale_pixels_per_mm": floor_plan.scale_pixels_per_mm if floor_plan else None,
        "scale_source": floor_plan.scale_source if floor_plan else None,
        "image_width": floor_plan.width if floor_plan else None,
        "image_height": floor_plan.height if floor_plan else None,
        "floor_plan_filename": floor_plan.original_filename if floor_plan else None,
        "floor_plan_id": floor_plan.id if floor_plan else None,
    }
