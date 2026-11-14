from typing import Dict, Any, List
from collections import Counter
from sqlalchemy.orm import Session

from app.models.analysis import AnalysisRun, ComplianceResult, Room, DetectedElement, SpatialEdge
from app.models.floor_plan import FloorPlan


def build_assistant_response(db: Session, question: str, analysis_id: int | None = None) -> Dict[str, Any]:
    normalized = (question or "").strip().lower()

    if not normalized:
        return {
            "answer": "Please ask a question about the floor plan, corridor width, space between walls, room dimensions, or NBC 2016 compliance.",
            "context": [],
            "evidence": [],
            "suggested_actions": [
                "Is the corridor width compliant with NBC norms?",
                "Is the space between walls correct?",
                "What are the main observations in this floor plan?",
                "How many rooms were detected?",
                "Which architectural elements were identified?",
                "What should I verify next?",
            ],
        }

    # Fetch analysis record and child objects
    analysis = db.query(AnalysisRun).filter(AnalysisRun.id == analysis_id).first() if analysis_id else None
    floor_plan = db.query(FloorPlan).filter(FloorPlan.id == analysis.floor_plan_id).first() if analysis else None
    rooms: List[Room] = db.query(Room).filter(Room.analysis_id == analysis_id).all() if analysis_id else []
    elements: List[DetectedElement] = db.query(DetectedElement).filter(DetectedElement.analysis_id == analysis_id).all() if analysis_id else []
    edges: List[SpatialEdge] = db.query(SpatialEdge).filter(SpatialEdge.analysis_id == analysis_id).all() if analysis_id else []
    compliance: List[ComplianceResult] = db.query(ComplianceResult).filter(ComplianceResult.analysis_id == analysis_id).all() if analysis_id else []

    room_count = len(rooms)
    element_count = len(elements)
    edge_count = len(edges)
    room_categories = Counter(r.label for r in rooms if r.label)
    element_categories = Counter(e.element_type for e in elements if e.element_type)

    is_calibrated = bool(floor_plan and floor_plan.scale_source == "user-calibrated" and floor_plan.scale_pixels_per_mm)

    # 1. Corridor Width / Hallway Width / Circulation Passage
    if any(k in normalized for k in ["corridor", "hallway", "passageway", "passage"]):
        corridor_finding = next((c for c in compliance if c.rule_id == "corridor-clear-width"), None)
        hallway_rooms = [r for r in rooms if r.label in ("Entry / Hallway", "Hallway", "Corridor", "Entry")]

        if is_calibrated and corridor_finding:
            widths_str = ", ".join(f"{r.width_m}m" for r in hallway_rooms if r.width_m) or "measured"
            answer = (
                f"Corridor Assessment: {corridor_finding.status}.\n\n"
                f"{corridor_finding.message}\n\n"
                f"Under the National Building Code of India (NBC 2016 Part 3, Clause 4.8 / 12.8), "
                f"residential internal corridors and passageways must maintain a minimum clear width of 1.00 m. "
                f"Identified corridor zones: {len(hallway_rooms)} (widths: {widths_str}). "
                f"{corridor_finding.recommendation}"
            )
        elif is_calibrated:
            answer = (
                "Under NBC 2016 Part 3 Clause 4.8, residential corridors must maintain at least 1.00 m clear width. "
                "Ensure that circulation passages between habitable spaces provide 1.00 m unobstructed width."
            )
        else:
            answer = (
                "According to NBC 2016 Part 3 Clause 4.8, the minimum clear width for residential corridors and hallways is 1.00 m (1000 mm). "
                "Currently, drawing scale is uncalibrated. Use the 'Calibrate Scale' button to set drawing scale (e.g. set door = 1.0 m) "
                "so the system can verify exact corridor width in metres."
            )
        return {
            "answer": answer,
            "context": [f"Corridor status: {corridor_finding.status if corridor_finding else 'Uncalibrated'}"],
            "evidence": [f"{len(hallway_rooms)} corridor zones detected"],
            "suggested_actions": [
                "Locate corridor on the spatial overlay board",
                "Is the space between walls correct?",
                "Verify habitable room dimensions",
            ],
        }

    # 2. Space Between Two Walls / Wall Spacing & Clearances
    if any(k in normalized for k in ["space between", "between two walls", "wall space", "wall clear", "wall spacing", "clearance between walls"]):
        wall_finding = next((c for c in compliance if c.rule_id == "wall-spacing-and-shafts"), None)
        wall_count = element_categories.get("wall", 0)

        if is_calibrated and wall_finding:
            answer = (
                f"Wall Spacing Assessment: {wall_finding.status}.\n\n"
                f"{wall_finding.message}\n\n"
                f"NBC 2016 Part 3 specifies clear clearances between opposing walls:\n"
                f"- Minimum clearance in circulation passages: 1.00 m (Clause 4.8)\n"
                f"- Minimum clearance in habitable rooms: 2.40 m (Clause 4.1)\n"
                f"- Minimum clearance in kitchens: 1.80 m (Clause 4.2)\n"
                f"- Minimum clearance in bathrooms: 1.20 m (Clause 4.4)\n"
                f"- Minimum clearance for internal light/ventilation shafts: 1.20 m (Clause 4.9 & 8.2).\n\n"
                f"{wall_finding.explanation}"
            )
        elif is_calibrated:
            answer = (
                f"Analyzed {wall_count} wall elements. NBC 2016 mandates clear wall spans of at least 1.00 m for circulation passages "
                "and 1.20 m for utility and light/ventilation shafts."
            )
        else:
            answer = (
                "NBC 2016 establishes specific minimum clearances between opposing walls:\n"
                "- Circulation corridors: minimum 1.00 m\n"
                "- Habitable rooms: minimum 2.40 m\n"
                "- Kitchens: minimum 1.80 m\n"
                "- Bathrooms: minimum 1.20 m\n"
                "- Light/ventilation shafts: minimum 1.20 m\n\n"
                "Please calibrate drawing scale (via 'Calibrate Scale' button) to measure exact wall-to-wall clearances in metres."
            )
        return {
            "answer": answer,
            "context": [f"{wall_count} wall elements analyzed"],
            "evidence": [],
            "suggested_actions": [
                "Is the corridor width compliant with NBC norms?",
                "Review partition walls on the overlay board",
                "Check door clear widths",
            ],
        }

    # 3. Main Observations / Overview
    if any(k in normalized for k in ["main observation", "observations", "what did the system detect", "overview", "summary", "summarize"]):
        categories_str = ", ".join(f"{cnt} {lbl}" for lbl, cnt in room_categories.most_common(5)) or "no room categories"
        elements_str = ", ".join(f"{cnt} {etype}s" for etype, cnt in element_categories.items()) or "no elements"
        scale_msg = (
            f"Drawing scale is calibrated ({floor_plan.scale_pixels_per_mm * 1000:.1f} px/m). Geometry has been evaluated against NBC 2016 norms."
            if is_calibrated
            else "Physical dimensions are uncalibrated (reported in raw pixels). Use 'Calibrate Scale' to assess NBC 2016 compliance."
        )
        answer = (
            f"The analysis identified {room_count} room regions ({categories_str}) and {element_count} architectural elements ({elements_str}) "
            f"in the uploaded floor plan. {edge_count} potential geometric spatial relationships were generated for review. {scale_msg}"
        )
        return {
            "answer": answer,
            "context": [f"{room_count} rooms", f"{element_count} elements", f"{edge_count} spatial candidates"],
            "evidence": [],
            "suggested_actions": [
                "Is the corridor width compliant with NBC norms?",
                "Is the space between walls correct?",
                "Which architectural elements were identified?",
                "What should I verify next?",
            ],
        }

    # 4. How many rooms were detected?
    if any(k in normalized for k in ["how many room", "room count", "number of room", "rooms detected", "rooms were detected"]):
        breakdown = ", ".join(f"{cnt} {lbl}" for lbl, cnt in room_categories.items()) if room_categories else "none"
        answer = (
            f"The system detected a total of {room_count} room regions. "
            f"Breakdown by category: {breakdown}. "
            f"{'Metric areas are calibrated in square metres.' if is_calibrated else 'Areas are reported in pixels because scale is not yet calibrated.'}"
        )
        return {
            "answer": answer,
            "context": [f"{lbl}: {cnt}" for lbl, cnt in room_categories.items()],
            "evidence": [],
            "suggested_actions": [
                "Is the corridor width compliant with NBC norms?",
                "Which architectural elements were identified?",
                "Review room boundaries on the spatial board",
            ],
        }

    # 5. Which architectural elements were identified?
    if any(k in normalized for k in ["architectural element", "elements were identified", "what elements", "element count", "which elements"]):
        breakdown = ", ".join(f"{cnt} {etype}s" for etype, cnt in element_categories.items()) if element_categories else "none"
        answer = (
            f"The model identified {element_count} architectural elements: {breakdown}. "
            "These elements were detected by the semantic segmentation model. "
            "Doors, windows, and walls are cross-checked against NBC 2016 clearance and ventilation standards."
        )
        return {
            "answer": answer,
            "context": [f"{etype}: {cnt}" for etype, cnt in element_categories.items()],
            "evidence": [],
            "suggested_actions": [
                "Locate doors and windows on the plan viewer",
                "Is the corridor width compliant?",
                "Verify aperture clearances",
            ],
        }

    # 6. Building Code / NBC 2016 Compliance Status
    if any(k in normalized for k in ["nbc", "code check", "compliance", "rule", "standard", "regulation"]):
        if is_calibrated:
            pass_c = sum(1 for c in compliance if c.status == "PASS")
            fail_c = sum(1 for c in compliance if c.status == "FAIL")
            warn_c = sum(1 for c in compliance if c.status == "WARNING")
            answer = (
                f"NBC 2016 Assessment Summary: {pass_c} Passed, {fail_c} Action Items / Violations, {warn_c} Warnings.\n\n"
                "Key evaluated provisions:\n"
                "- Corridor clear width: NBC Clause 4.8 (≥ 1.00 m)\n"
                "- Habitable rooms: NBC Clause 4.1 (width ≥ 2.40 m, area ≥ 9.50 m²)\n"
                "- Kitchen: NBC Clause 4.2 (width ≥ 1.80 m, area ≥ 4.50 m²)\n"
                "- Bathroom / WC: NBC Clause 4.4 (width ≥ 1.20 m, area ≥ 1.80 m²)\n"
                "- Doors: NBC Clause 4.7 (main ≥ 1.00 m, rooms ≥ 0.90 m, bath ≥ 0.75 m)\n"
                "- Natural ventilation: NBC Clause 4.10 (window aperture ≥ 10%)\n\n"
                "Review detailed findings in the Compliance Screening table below."
            )
        else:
            answer = (
                "Compliance is currently in uncalibrated screening mode. "
                "To evaluate your plan against the National Building Code of India (NBC 2016), "
                "click 'Calibrate Scale' on the header or compliance panel (e.g. set entrance door = 1.0 m). "
                "The engine will instantly compute corridor widths and room dimensions in metres and report PASS/FAIL results."
            )
        return {
            "answer": answer,
            "context": [c.rule_id for c in compliance],
            "evidence": [],
            "suggested_actions": [
                "Is the corridor width compliant with NBC norms?",
                "Is the space between walls correct?",
                "Review the compliance matrix table",
            ],
        }

    # 7. Recommendations / What should I verify next?
    if any(k in normalized for k in ["verify next", "what next", "next step", "what should i do", "recommendation"]):
        answer = (
            "Recommended next steps for this floor plan:\n"
            "1. Calibrate drawing scale if not yet calibrated to view real dimensions in metres.\n"
            "2. Review corridor clear width (Clause 4.8) to ensure at least 1.00 m unobstructed transit.\n"
            "3. Verify space between opposing partition walls in circulation and shaft areas (min 1.00 m - 1.20 m).\n"
            "4. Check habitable room carpet areas against NBC 9.50 m² minimums.\n"
            "5. Review spatial relationships using the human-in-the-loop audit buttons.\n"
            "6. Download the comprehensive PDF Analysis Report for statutory review."
        )
        return {
            "answer": answer,
            "context": ["Scale calibration", "Corridor check", "Wall clearances", "Spatial review", "PDF report"],
            "evidence": [],
            "suggested_actions": [
                "Calibrate drawing scale",
                "Export PDF Analysis Report",
                "Review spatial relationship candidates",
            ],
        }

    # Fallback response
    return {
        "answer": (
            f"The floor plan contains {room_count} detected rooms and {element_count} architectural elements. "
            f"{'Drawing scale is calibrated with active NBC 2016 rule checking.' if is_calibrated else 'Calibrate drawing scale to evaluate corridor widths, room areas, and wall spacing against NBC 2016 norms.'}"
        ),
        "context": [f"{room_count} rooms", f"{element_count} elements"],
        "evidence": [],
        "suggested_actions": [
            "Is the corridor width compliant with NBC norms?",
            "Is the space between walls correct?",
            "What are the main observations in this floor plan?",
        ],
    }
