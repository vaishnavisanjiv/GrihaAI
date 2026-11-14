import json
import math
from typing import Any

import networkx as nx
from shapely.geometry import Polygon
from shapely.strtree import STRtree

from app.models.analysis import SpatialEdge

ROOM_ADJACENCY_TOLERANCE_PIXELS = 1.5


def _polygon_from_json(value: str | None, key: str | None = None) -> Polygon | None:
    if not value:
        return None
    try:
        geometry: Any = json.loads(value)
        if key is not None:
            geometry = geometry.get(key) if isinstance(geometry, dict) else None
        if not isinstance(geometry, list):
            return None
        polygon = Polygon(geometry)
        if polygon.is_empty or not polygon.is_valid or polygon.area <= 0:
            return None
        return polygon
    except (json.JSONDecodeError, TypeError, ValueError):
        return None


def _confidence(value: Any) -> float | None:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(confidence) or not 0 <= confidence <= 1:
        return None
    return confidence


def _edge(
    analysis_id: int,
    source_id: int,
    target_id: int,
    source_node_type: str,
    target_node_type: str,
    relationship: str,
    confidence: float,
    evidence: dict[str, Any],
) -> SpatialEdge:
    return SpatialEdge(
        analysis_id=analysis_id,
        source_element_id=source_id,
        target_element_id=target_id,
        relationship_type=relationship,
        properties_json=json.dumps(
            {
                "confidence": confidence,
                "confidence_calibrated": False,
                "review_required": True,
                "source_node_type": source_node_type,
                "target_node_type": target_node_type,
                "evidence": evidence,
            }
        ),
    )


def build_spatial_graph(
    rooms: list[Any],
    elements: list[Any],
    analysis_id: int,
) -> list[SpatialEdge]:
    """Persist conservative geometry-derived candidates, never connectivity claims."""
    graph = nx.MultiGraph()
    geometries: dict[int, Polygon] = {}
    confidences: dict[int, float] = {}
    edges: list[SpatialEdge] = []

    for room in rooms:
        room_id = getattr(room, "id", None)
        polygon = _polygon_from_json(getattr(room, "polygon_json", None))
        confidence = _confidence(getattr(room, "confidence", None))
        if room_id is None or polygon is None or confidence is None:
            continue
        graph.add_node(("room", room_id), node_type="room", confidence=confidence)
        geometries[room_id] = polygon
        confidences[room_id] = confidence

    room_ids = list(geometries)
    room_polygons = [geometries[room_id] for room_id in room_ids]
    room_tree = STRtree(room_polygons) if room_polygons else None
    if room_tree is not None:
        for source_index, source_polygon in enumerate(room_polygons):
            for target_index in room_tree.query(
                source_polygon,
                predicate="dwithin",
                distance=ROOM_ADJACENCY_TOLERANCE_PIXELS,
            ):
                target_index = int(target_index)
                if target_index <= source_index:
                    continue
                source_id = room_ids[source_index]
                target_id = room_ids[target_index]
                target_polygon = room_polygons[target_index]
                distance = float(source_polygon.distance(target_polygon))
                confidence = min(confidences[source_id], confidences[target_id])
                graph.add_edge(
                    ("room", source_id),
                    ("room", target_id),
                    relationship="ADJACENT_TO_CANDIDATE",
                    confidence=confidence,
                    evidence={
                        "method": "polygon_distance",
                        "distance_pixels": distance,
                        "maximum_distance_pixels": ROOM_ADJACENCY_TOLERANCE_PIXELS,
                        "source_geometry_confidence": confidences[source_id],
                        "target_geometry_confidence": confidences[target_id],
                    },
                )

    for element in elements:
        if str(getattr(element, "element_type", "")).lower() != "door":
            continue
        door_id = getattr(element, "id", None)
        door_polygon = _polygon_from_json(
            getattr(element, "geometry_json", None),
            key="polygon_pixels",
        )
        door_confidence = _confidence(getattr(element, "confidence", None))
        if door_id is None or door_polygon is None or door_confidence is None:
            continue
        graph.add_node(("element", door_id), node_type="door", confidence=door_confidence)
        proximity_threshold = max(1.0, math.sqrt(door_polygon.area))
        if room_tree is None:
            continue
        for room_index in room_tree.query(
            door_polygon,
            predicate="dwithin",
            distance=proximity_threshold,
        ):
            room_index = int(room_index)
            room_id = room_ids[room_index]
            room_polygon = room_polygons[room_index]
            distance = float(room_polygon.distance(door_polygon))
            confidence = min(confidences[room_id], door_confidence)
            graph.add_edge(
                ("room", room_id),
                ("element", door_id),
                relationship="PROXIMATE_TO",
                confidence=confidence,
                evidence={
                    "method": "polygon_distance",
                    "distance_pixels": distance,
                    "maximum_distance_pixels": proximity_threshold,
                    "room_geometry_confidence": confidences[room_id],
                    "door_geometry_confidence": door_confidence,
                },
            )

    unique_edges: dict[tuple[int, int, str], dict[str, Any]] = {}
    for source, target, edge_data in graph.edges(data=True):
        source_type, source_id = source
        target_type, target_id = target
        if source_type == "element" and target_type == "room":
            source_id, target_id = target_id, source_id
            source_type, target_type = target_type, source_type

        # Canonical key: order IDs if same node type (room-room)
        key = (
            min(source_id, target_id) if source_type == target_type else source_id,
            max(source_id, target_id) if source_type == target_type else target_id,
            edge_data["relationship"],
        )

        if key in unique_edges:
            existing = unique_edges[key]
            existing_dist = existing["evidence"].get("distance_pixels", 9999.0)
            new_dist = edge_data["evidence"].get("distance_pixels", 9999.0)
            if new_dist < existing_dist:
                existing["evidence"]["distance_pixels"] = new_dist
            existing["confidence"] = max(existing["confidence"], edge_data["confidence"])
            existing["evidence"]["contact_count"] = existing["evidence"].get("contact_count", 1) + 1
        else:
            evidence_copy = dict(edge_data["evidence"])
            evidence_copy["contact_count"] = 1
            unique_edges[key] = {
                "source_id": source_id,
                "target_id": target_id,
                "source_type": source_type,
                "target_type": target_type,
                "relationship": edge_data["relationship"],
                "confidence": edge_data["confidence"],
                "evidence": evidence_copy,
            }

    for item in unique_edges.values():
        edges.append(
            _edge(
                analysis_id,
                item["source_id"],
                item["target_id"],
                item["source_type"],
                item["target_type"],
                item["relationship"],
                item["confidence"],
                item["evidence"],
            )
        )
    return edges
