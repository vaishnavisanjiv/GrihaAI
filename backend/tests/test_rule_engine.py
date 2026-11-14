from app.models.analysis import DetectedElement, Room
from app.services.rule_engine import evaluate_rules


def test_rule_engine_marks_checks_unassessed_without_verified_code_catalog():
    rooms = [
        Room(label="Living Room", area_sqm=25.0),
        Room(label="Bedroom 1", area_sqm=14.0),
        Room(label="Bathroom", area_sqm=5.5),
    ]
    elements = [
        DetectedElement(element_type="door", geometry_json='{"width_m": 1.1}'),
        DetectedElement(element_type="stair", geometry_json='{"width_m": 1.6}'),
        DetectedElement(element_type="window", geometry_json='{"width_m": 1.2}'),
    ]

    results = evaluate_rules({"rooms": rooms, "elements": elements}, analysis_id=42)
    rule_ids = {result.rule_id for result in results}

    assert "habitable-room-dimensions" in rule_ids
    assert "sanitary-facility-dimensions" in rule_ids
    assert "stair-and-exit-dimensions" in rule_ids
    assert "accessible-route-and-clearances" in rule_ids
    assert results
    assert all(result.status == "NOT_ASSESSED" for result in results)


def test_room_area_is_not_assessed_when_scale_or_code_is_unverified():
    results = evaluate_rules(
        {"rooms": [Room(label="Living Room", area_pixels=10000)], "elements": []},
        analysis_id=43,
    )
    room_check = next(result for result in results if result.rule_id == "habitable-room-dimensions")
    assert room_check.status == "NOT_ASSESSED"
    assert "not assessed" in room_check.message


def test_corridor_width_passes_when_at_least_1m():
    rooms = [
        Room(id=1, label="Entry / Hallway", width_m=1.20, length_m=3.50, area_sqm=4.20),
        Room(id=2, label="Living / Dining", width_m=3.50, length_m=4.50, area_sqm=15.75),
    ]
    elements = [
        DetectedElement(id=1, element_type="door", geometry_json='{"width_m": 0.95}'),
    ]
    results = evaluate_rules(
        {"rooms": rooms, "elements": elements},
        analysis_id=44,
        scale_calibrated=True,
        scale_pixels_per_mm=0.05,
    )
    corridor_check = next(r for r in results if r.rule_id == "corridor-clear-width")
    assert corridor_check.status == "PASS"
    assert "complies" in corridor_check.message.lower() or "1.20" in corridor_check.message


def test_corridor_width_fails_when_below_1m():
    rooms = [
        Room(id=1, label="Entry / Hallway", width_m=0.82, length_m=2.40, area_sqm=1.97),
        Room(id=2, label="Living / Dining", width_m=3.20, length_m=4.00, area_sqm=12.80),
    ]
    elements = [
        DetectedElement(id=1, element_type="door", geometry_json='{"width_m": 0.85}'),
    ]
    results = evaluate_rules(
        {"rooms": rooms, "elements": elements},
        analysis_id=45,
        scale_calibrated=True,
        scale_pixels_per_mm=0.05,
    )
    corridor_check = next(r for r in results if r.rule_id == "corridor-clear-width")
    assert corridor_check.status == "FAIL"
    assert "0.82" in corridor_check.message or "non-compliant" in corridor_check.message.lower()


def test_habitable_kitchen_and_sanitary_compliance():
    rooms = [
        Room(id=1, label="Living / Dining", width_m=3.60, length_m=5.00, area_sqm=18.00),
        Room(id=2, label="Kitchen", width_m=2.10, length_m=2.80, area_sqm=5.88),
        Room(id=3, label="Bathroom", width_m=1.50, length_m=2.20, area_sqm=3.30),
    ]
    elements = [
        DetectedElement(id=1, element_type="door", geometry_json='{"width_m": 0.90}'),
        DetectedElement(id=2, element_type="window", geometry_json='{"width_m": 1.80}'),
    ]
    results = evaluate_rules(
        {"rooms": rooms, "elements": elements},
        analysis_id=46,
        scale_calibrated=True,
        scale_pixels_per_mm=0.05,
    )
    habitable_check = next(r for r in results if r.rule_id == "habitable-room-dimensions")
    kitchen_check = next(r for r in results if r.rule_id == "kitchen-dimensions")
    sanitary_check = next(r for r in results if r.rule_id == "sanitary-facility-dimensions")

    assert habitable_check.status == "PASS"
    assert kitchen_check.status == "PASS"
    assert sanitary_check.status == "PASS"
