from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.analysis import AnalysisRun, ComplianceResult, DetectedElement, Room
from app.models.floor_plan import FloorPlan
from app.services.preprocessing_service import prepare_plan_for_analysis
from app.services.rule_engine import evaluate_rules
from app.services.spatial_service import build_spatial_graph

if TYPE_CHECKING:
    import torch
    from app.services.floorplan_model import FloorPlanUNet


def get_checkpoint_path() -> Path:
    model_dir = Path(settings.CV_MODEL_PATH)
    if not model_dir.is_absolute():
        model_dir = Path.cwd() / model_dir
    return model_dir / "floorplan_unet.pt"


def has_trained_model() -> bool:
    return get_checkpoint_path().is_file()


def _checkpoint_sha256(checkpoint_path: Path) -> str:
    digest = hashlib.sha256()
    with checkpoint_path.open("rb") as checkpoint_file:
        for chunk in iter(lambda: checkpoint_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ensure_checkpoint_unchanged(checkpoint_path: Path, original_sha256: str) -> None:
    if _checkpoint_sha256(checkpoint_path) != original_sha256:
        raise RuntimeError("Model checkpoint changed while analysis was loading it")


def _polygon_from_component(component: np.ndarray) -> list[list[int]]:
    contour = component
    epsilon = max(1.0, cv2.arcLength(contour, True) * 0.01)
    simplified = cv2.approxPolyDP(contour, epsilon, True)
    return [[int(point[0][0]), int(point[0][1])] for point in simplified]


def _add_model_predictions(
    db: Session,
    analysis: AnalysisRun,
    floor_plan: FloorPlan,
    model: FloorPlanUNet,
    device: torch.device,
) -> tuple[list[Room], list[DetectedElement]]:
    from app.services.floorplan_model import ELEMENT_LABELS, ROOM_LABELS, predict_image

    image_path = Path(floor_plan.storage_path)
    if floor_plan.file_type == ".pdf":
        image_path = Path(
            prepare_plan_for_analysis(
                floor_plan.storage_path,
                str(image_path.parent / "previews"),
            )
        )
        if image_path.suffix.lower() == ".pdf":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not convert this PDF. Install Poppler and add it to PATH, then retry.",
            )

    labels, confidence = predict_image(model, image_path, device)
    height, width = labels.shape
    # Refined architectural thresholds:
    # Rooms require at least ~200 px² (filters out tiny 80 px/120 px noise specks)
    min_room_area = max(200, int(height * width * 0.0008))
    # Elements like doors and windows can be smaller
    min_element_area = max(36, int(height * width * 0.0001))
    rooms: list[Room] = []
    elements: list[DetectedElement] = []

    # Morphological kernels to bridge door cutouts and thin partition lines within the same room class
    room_morph_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    element_morph_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

    for class_id, label in ROOM_LABELS.items():
        raw_mask = (labels == class_id).astype("uint8")
        # Apply morphological closing to heal micro-gaps and unify fragmented pieces of the same space
        closed_mask = cv2.morphologyEx(raw_mask, cv2.MORPH_CLOSE, room_morph_kernel)

        component_count, component_labels, stats, centroids = cv2.connectedComponentsWithStats(
            closed_mask, connectivity=8
        )
        for component_id in range(1, component_count):
            x, y, component_width, component_height, area = stats[component_id]
            if area < min_room_area:
                continue
            component_mask = (component_labels == component_id).astype("uint8")
            contours, _ = cv2.findContours(
                component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            if not contours:
                continue
            contour = max(contours, key=cv2.contourArea)
            average_confidence = float(confidence[component_labels == component_id].mean())
            metric_area = (
                float(area / (floor_plan.scale_pixels_per_mm**2) / 1_000_000)
                if floor_plan.scale_source == "user-calibrated" and floor_plan.scale_pixels_per_mm
                else None
            )
            metric_width = (
                float(max(component_width, component_height) / floor_plan.scale_pixels_per_mm / 1000)
                if floor_plan.scale_source == "user-calibrated" and floor_plan.scale_pixels_per_mm
                else None
            )
            metric_length = (
                float(min(component_width, component_height) / floor_plan.scale_pixels_per_mm / 1000)
                if floor_plan.scale_source == "user-calibrated" and floor_plan.scale_pixels_per_mm
                else None
            )
            rooms.append(
                Room(
                    analysis_id=analysis.id,
                    label=label,
                    polygon_json=json.dumps(_polygon_from_component(contour)),
                    area_pixels=float(area),
                    area_sqm=metric_area,
                    width_m=metric_width,
                    length_m=metric_length,
                    centroid_x=float(centroids[component_id][0]),
                    centroid_y=float(centroids[component_id][1]),
                    confidence=average_confidence,
                )
            )

    for class_id, element_type in ELEMENT_LABELS.items():
        raw_mask = (labels == class_id).astype("uint8")
        closed_mask = cv2.morphologyEx(raw_mask, cv2.MORPH_CLOSE, element_morph_kernel)
        component_count, component_labels, stats, _ = cv2.connectedComponentsWithStats(
            closed_mask, connectivity=8
        )
        for component_id in range(1, component_count):
            x, y, component_width, component_height, area = stats[component_id]
            if area < min_element_area:
                continue
            component_mask = (component_labels == component_id).astype("uint8")
            contours, _ = cv2.findContours(
                component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            if not contours:
                continue
            contour = max(contours, key=cv2.contourArea)
            average_confidence = float(confidence[component_labels == component_id].mean())
            metric_width = (
                float(max(component_width, component_height) / floor_plan.scale_pixels_per_mm / 1000)
                if floor_plan.scale_source == "user-calibrated" and floor_plan.scale_pixels_per_mm
                else None
            )
            elements.append(
                DetectedElement(
                    analysis_id=analysis.id,
                    element_type=element_type,
                    label=element_type.title(),
                    confidence=average_confidence,
                    geometry_json=json.dumps(
                        {
                            "polygon_pixels": _polygon_from_component(contour),
                            "bbox_pixels": [int(x), int(y), int(component_width), int(component_height)],
                            "area_pixels": int(area),
                            "width_m": metric_width,
                        }
                    ),
                    properties_json=json.dumps(
                        {
                            "measurement_unit": "meters" if metric_width is not None else "pixels",
                                            "scale_calibrated": floor_plan.scale_source == "user-calibrated",
                        }
                    ),
                )
            )

    db.add_all(rooms)
    db.add_all(elements)
    db.flush()
    db.add_all(build_spatial_graph(rooms, elements, analysis.id))
    findings = evaluate_rules({"rooms": rooms, "elements": elements}, analysis_id=analysis.id)
    db.add_all(findings)
    return rooms, elements


def run_trained_analysis(db: Session, analysis: AnalysisRun, floor_plan: FloorPlan) -> None:
    try:
        import torch
    except ImportError as exc:
        analysis.status = "FAILED"
        analysis.error_message = "PyTorch is not installed; install backend/requirements-ml.txt"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="A trained checkpoint exists, but PyTorch is not installed. Install backend/requirements-ml.txt.",
        ) from exc

    # Mark analysis as actively running so status polls reflect progress.
    analysis.status = "RUNNING"
    db.commit()

    checkpoint_path = get_checkpoint_path()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    try:
        from app.services.floorplan_model import load_checkpoint

        checkpoint_sha256 = _checkpoint_sha256(checkpoint_path)
        model, checkpoint = load_checkpoint(checkpoint_path, device)
        _ensure_checkpoint_unchanged(checkpoint_path, checkpoint_sha256)
        _add_model_predictions(db, analysis, floor_plan, model, device)
        analysis.cv_method = "cubicasa5k-unet-segmentation"
        analysis.model_version = (
            f"buildguard-unet-v1-epoch-{checkpoint.get('best_epoch', 'unknown')}"
            f"-sha256:{checkpoint_sha256}"
        )
        analysis.status = "COMPLETED"
        analysis.completed_at = datetime.now(timezone.utc)
        db.commit()
    except HTTPException as exc:
        db.rollback()
        analysis.status = "FAILED"
        analysis.error_message = str(exc.detail)[:1000]
        db.commit()
        raise
    except (cv2.error, OSError, RuntimeError, ValueError, KeyError) as exc:
        db.rollback()
        analysis.status = "FAILED"
        analysis.error_message = str(exc)[:1000]
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Floor-plan model analysis failed: {exc}",
        ) from exc
