import json
from types import SimpleNamespace

import numpy as np
import torch
from PIL import Image
from sqlalchemy.orm import Session

from app.models.analysis import AnalysisRun, SpatialEdge
from app.models.floor_plan import FloorPlan
from app.services import floorplan_model
from app.services.model_analysis_service import _add_model_predictions
from app.services.spatial_service import build_spatial_graph


def _room(room_id, polygon, confidence=0.8, label="Room"):
    return SimpleNamespace(
        id=room_id,
        label=label,
        polygon_json=json.dumps(polygon),
        confidence=confidence,
    )


def _door(door_id, polygon, confidence=0.7):
    return SimpleNamespace(
        id=door_id,
        element_type="door",
        geometry_json=json.dumps({"polygon_pixels": polygon}),
        confidence=confidence,
    )


def test_spatial_graph_only_records_measured_candidates_with_uncalibrated_confidence():
    touching_room = _room(2, [[0, 0], [10, 0], [10, 10], [0, 10]], label="Kitchen")
    nearby_room = _room(3, [[11, 0], [21, 0], [21, 10], [11, 10]], label="Bedroom")
    distant_room = _room(4, [[100, 100], [110, 100], [110, 110], [100, 110]])
    door = _door(2, [[10, 4], [11, 4], [11, 6], [10, 6]])

    edges = build_spatial_graph(
        [touching_room, nearby_room, distant_room],
        [door],
        analysis_id=42,
    )

    assert {(edge.source_element_id, edge.target_element_id, edge.relationship_type) for edge in edges} == {
        (2, 3, "ADJACENT_TO_CANDIDATE"),
        (2, 2, "PROXIMATE_TO"),
        (3, 2, "PROXIMATE_TO"),
    }
    for edge in edges:
        properties = json.loads(edge.properties_json)
        assert properties["confidence"] <= 0.8
        assert properties["confidence_calibrated"] is False
        assert properties["review_required"] is True
        if edge.relationship_type == "PROXIMATE_TO":
            assert properties["source_node_type"] == "room"
            assert properties["target_node_type"] == "element"
        assert properties["evidence"]["method"] == "polygon_distance"
        assert properties["evidence"]["distance_pixels"] >= 0


def test_spatial_graph_omits_invalid_polygons_and_unverified_confidence():
    valid = _room(1, [[0, 0], [10, 0], [10, 10], [0, 10]])
    invalid = _room(2, [[0, 0], [10, 10], [0, 10], [10, 0]])
    missing_confidence = _room(
        3,
        [[10, 0], [20, 0], [20, 10], [10, 10]],
        confidence=None,
    )
    malformed = SimpleNamespace(
        id=4,
        label="Malformed",
        polygon_json="{not json",
        confidence=0.9,
    )

    assert build_spatial_graph(
        [valid, invalid, missing_confidence, malformed],
        [],
        analysis_id=7,
    ) == []


def test_model_analysis_persists_graph_candidates_with_review_metadata(
    tmp_path,
    db: Session,
    monkeypatch,
):
    image_path = tmp_path / "plan.png"
    Image.new("RGB", (512, 512), "white").save(image_path)
    analysis = AnalysisRun(floor_plan_id=1, status="PENDING")
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    floor_plan = FloorPlan(
        project_id=1,
        filename="plan.png",
        original_filename="plan.png",
        storage_path=str(image_path),
        file_type=".png",
        scale_source="uncalibrated",
    )
    labels = np.zeros((512, 512), dtype=np.uint8)
    labels[20:80, 20:80] = 2
    labels[20:80, 80:140] = 3
    labels[45:55, 75:85] = 11
    confidence = np.full((512, 512), 0.8, dtype=np.float32)
    monkeypatch.setattr(
        floorplan_model,
        "predict_image",
        lambda model, path, device: (labels, confidence),
        raising=False,
    )

    _add_model_predictions(db, analysis, floor_plan, model=None, device=torch.device("cpu"))
    db.commit()

    graph_edges = db.query(SpatialEdge).filter(SpatialEdge.analysis_id == analysis.id).all()
    assert graph_edges
    assert {edge.relationship_type for edge in graph_edges} <= {
        "ADJACENT_TO_CANDIDATE",
        "PROXIMATE_TO",
    }
    assert all(json.loads(edge.properties_json)["review_required"] for edge in graph_edges)
    assert all(
        json.loads(edge.properties_json)["confidence_calibrated"] is False
        for edge in graph_edges
    )
