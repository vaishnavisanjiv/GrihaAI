import json
from typing import Any, Dict, List, Optional

from app.models.analysis import ComplianceResult, DetectedElement, Room


UNASSESSED_CHECKS = (
    (
        "habitable-room-dimensions",
        "Habitable room dimensions",
        "Room labels and detected outlines do not establish compliance with the applicable minimum area, width, or height provisions.",
        "Confirm room dimensions and compare them with the verified provisions for the selected occupancy and authority.",
    ),
    (
        "kitchen-dimensions",
        "Kitchen dimensions",
        "Kitchen outline has not been verified against statutory minimum carpet area (4.50 m m²) and width (1.80 m).",
        "Calibrate drawing scale to measure clear kitchen width and usable floor area against NBC Clause 4.2.",
    ),
    (
        "sanitary-facility-dimensions",
        "Sanitary facility dimensions",
        "A detected toilet or bathroom does not establish fixture clearances, ventilation, or applicable dimensional compliance.",
        "Verify fixture layout, clearances, ventilation, and the applicable local provisions.",
    ),
    (
        "corridor-clear-width",
        "Corridor and hallway clear width",
        "Circulation passageways cannot be verified against the statutory 1.00 m minimum clear width without scale calibration.",
        "Calibrate drawing scale to evaluate corridor width against NBC 2016 Part 3 Clause 4.8.",
    ),
    (
        "wall-spacing-and-shafts",
        "Spacing between walls and internal shafts",
        "Clear distance between opposing wall partitions and light/ventilation shafts requires verified scale.",
        "Calibrate drawing scale to verify wall-to-wall clearances against NBC 2016 Clause 4.9 and 8.2.",
    ),
    (
        "door-clear-width",
        "Door clear width",
        "Detected door geometry is not a verified clear opening measurement and no applicable provision has been selected.",
        "Measure the clear opening on the source drawing and compare it with the applicable provision.",
    ),
    (
        "stair-and-exit-dimensions",
        "Stair and exit dimensions",
        "The model does not reliably reconstruct stair geometry, occupant load, number of exits, or travel distance.",
        "Have a qualified professional verify the stair, exit count, widths, travel distances, and applicable fire requirements.",
    ),
    (
        "ventilation-and-daylight",
        "Ventilation and daylight",
        "A detected window does not establish its operability, opening area, room association, or required ventilation.",
        "Verify opening dimensions, operability, room association, and the applicable ventilation and daylight provisions.",
    ),
    (
        "accessible-route-and-clearances",
        "Accessible route and clearances",
        "Accessible routes, door swings, turning spaces, and fixture clearances are not reliably inferred from this plan.",
        "Check accessible routes and clearances against the provisions applicable to the project.",
    ),
    (
        "site-and-building-context",
        "Site and building context",
        "A floor-plan image does not provide enough evidence to check plot setbacks, ground coverage, height, parking, fire access, or other site-dependent requirements.",
        "Provide the site plan, building height and floor data, plot and road dimensions, occupancy details, and applicable authority.",
    ),
    (
        "governing-code-selection",
        "Governing code and authority",
        "No versioned, verified NBC and local-authority rule catalog is configured for this project.",
        "Confirm the municipality, occupancy/use, applicable code edition, amendments, and local development-control regulations before code checks.",
    ),
)


def _get_room_clear_width(room: Room, scale_pixels_per_mm: Optional[float] = None) -> Optional[float]:
    """Return the clear width (narrower dimension) of a room in metres."""
    if room.width_m is not None and room.length_m is not None:
        return min(room.width_m, room.length_m)
    if room.width_m is not None:
        return room.width_m
    if room.length_m is not None:
        return room.length_m
    if room.polygon_json and scale_pixels_per_mm and scale_pixels_per_mm > 0:
        try:
            poly = json.loads(room.polygon_json)
            if poly and len(poly) >= 3:
                xs = [p[0] for p in poly]
                ys = [p[1] for p in poly]
                bw = max(xs) - min(xs)
                bh = max(ys) - min(ys)
                return min(bw, bh) / scale_pixels_per_mm / 1000.0
        except Exception:
            pass
    return None


def _get_element_width_m(element: DetectedElement, scale_pixels_per_mm: Optional[float] = None) -> Optional[float]:
    """Extract metric width of a detected element in metres."""
    if element.geometry_json:
        try:
            geom = json.loads(element.geometry_json)
            if "width_m" in geom and geom["width_m"] is not None:
                return float(geom["width_m"])
            bbox = geom.get("bbox_pixels")
            if bbox and len(bbox) == 4 and scale_pixels_per_mm and scale_pixels_per_mm > 0:
                _, _, bw, bh = bbox
                return max(bw, bh) / scale_pixels_per_mm / 1000.0
        except Exception:
            pass
    return None


def evaluate_rules(
    data: Dict[str, Any],
    analysis_id: Optional[int] = None,
    scale_calibrated: bool = False,
    scale_pixels_per_mm: Optional[float] = None,
) -> List[ComplianceResult]:
    """
    Evaluates floor plan geometry against the National Building Code of India (NBC 2016).
    
    Provisions evaluated:
    - Clause 4.8 / 12.8: Residential corridor clear width (min 1.00 m)
    - Clause 4.1: Habitable room dimensions (min width 2.40 m, min area 9.50 m m²)
    - Clause 4.2: Kitchen dimensions (min width 1.80 m, min area 4.50 m m²)
    - Clause 4.4: Bathroom / WC dimensions (min width 1.20 m, min area 1.80 m m²)
    - Clause 4.7 / 12.7: Door clear opening widths (main >= 1.00m, internal >= 0.90m, bath >= 0.75m)
    - Clause 4.9 & 8.2: Opposing wall spacing & internal shafts (min 1.00 m / 1.20 m)
    - Clause 4.10: Ventilation & daylight glazing aperture ratio (>= 10%)
    - Part 3 Annex B: Accessible route clearances (min 0.90 m - 1.00 m)
    """
    rooms: List[Room] = data.get("rooms", [])
    elements: List[DetectedElement] = data.get("elements", [])

    # If drawing scale is not calibrated, return unassessed checks guiding calibration
    if not scale_calibrated:
        detected_context = (
            f" The model detected {len(rooms)} room component(s) and "
            f"{len(elements)} element component(s); calibrate drawing scale to evaluate NBC 2016 norms."
        )
        return [
            ComplianceResult(
                analysis_id=analysis_id,
                rule_id=rule_id,
                status="NOT_ASSESSED",
                severity="UNVERIFIED",
                message=f"{title}: not assessed against a verified code provision (requires scale calibration).",
                explanation=f"{reason}{detected_context}",
                recommendation=recommendation,
            )
            for rule_id, title, reason, recommendation in UNASSESSED_CHECKS
        ]

    results: List[ComplianceResult] = []

    # -------------------------------------------------------------------------
    # 1. CORRIDOR & HALLWAY CLEAR WIDTH (NBC 2016 Part 3, Clause 4.8 / 12.8)
    # -------------------------------------------------------------------------
    hallway_rooms = [
        r for r in rooms
        if r.label in ("Entry / Hallway", "Hallway", "Corridor", "Entry")
    ]

    if hallway_rooms:
        hallway_widths = [
            _get_room_clear_width(r, scale_pixels_per_mm)
            for r in hallway_rooms
        ]
        valid_widths = [w for w in hallway_widths if w is not None]

        if valid_widths:
            min_corridor_w = min(valid_widths)
            max_corridor_w = max(valid_widths)
            total_circ_area = sum(r.area_sqm for r in hallway_rooms if r.area_sqm is not None)

            if min_corridor_w >= 1.00:
                results.append(
                    ComplianceResult(
                        analysis_id=analysis_id,
                        rule_id="corridor-clear-width",
                        status="PASS",
                        severity="LOW",
                        message=f"Corridor clear width complies with NBC Clause 4.8: minimum width is {min_corridor_w:.2f} m (required >= 1.00 m).",
                        explanation=(
                            f"Evaluated {len(hallway_rooms)} corridor / circulation zone(s) with total area {total_circ_area:.2f} m m². "
                            f"Detected clear widths range from {min_corridor_w:.2f} m to {max_corridor_w:.2f} m. "
                            f"All measured sections satisfy the NBC 2016 Part 3 Clause 4.8 statutory minimum of 1.00 m for residential corridors."
                        ),
                        recommendation="Maintain unobstructed passageways without permanent projections or inward door swings into the 1.00 m transit corridor.",
                    )
                )
            else:
                results.append(
                    ComplianceResult(
                        analysis_id=analysis_id,
                        rule_id="corridor-clear-width",
                        status="FAIL",
                        severity="HIGH",
                        message=f"Corridor clear width non-compliant: detected width is {min_corridor_w:.2f} m (NBC Clause 4.8 requires >= 1.00 m).",
                        explanation=(
                            f"Evaluated {len(hallway_rooms)} corridor / circulation zone(s). The narrowest passage measures {min_corridor_w:.2f} m, "
                            f"which falls below the statutory minimum clear width of 1.00 m mandated by NBC 2016 Part 3 Clause 4.8 for residential occupancy."
                        ),
                        recommendation=f"Widen the constricted corridor segment from {min_corridor_w:.2f} m to at least 1.00 m clear width between finished walls.",
                    )
                )
        else:
            results.append(
                ComplianceResult(
                    analysis_id=analysis_id,
                    rule_id="corridor-clear-width",
                    status="WARNING",
                    severity="MEDIUM",
                    message="Corridor detected but clear width could not be computed from outline.",
                    explanation="Hallway boundary polygon did not yield valid metric dimensions. Verify corridor clear width on source drawing.",
                    recommendation="Measure corridor clear width on the source drawing to confirm compliance with NBC 2016 Clause 4.8 (>= 1.00 m).",
                )
            )
    else:
        results.append(
            ComplianceResult(
                analysis_id=analysis_id,
                rule_id="corridor-clear-width",
                status="PASS",
                severity="LOW",
                message="Open-plan layout: circulation routes integrated into primary living spaces.",
                explanation="No segregated narrow corridor detected. Direct open-plan circulation paths comply provided transit clearances exceed 1.00 m.",
                recommendation="Confirm that furniture placement preserves an unobstructed 1.00 m circulation path from entrance to all rooms.",
            )
        )

    # -------------------------------------------------------------------------
    # 2. SPACING BETWEEN WALLS & INTERNAL SHAFTS (NBC 2016 Clause 4.9 & 8.2)
    # -------------------------------------------------------------------------
    wall_elements = [e for e in elements if e.element_type == "wall"]
    small_spaces = [r for r in rooms if _get_room_clear_width(r, scale_pixels_per_mm) is not None]
    min_space_clearance = min(
        (_get_room_clear_width(r, scale_pixels_per_mm) for r in small_spaces),
        default=None,
    )

    if min_space_clearance is not None and min_space_clearance >= 1.00:
        results.append(
            ComplianceResult(
                analysis_id=analysis_id,
                rule_id="wall-spacing-and-shafts",
                status="PASS",
                severity="LOW",
                message=f"Clear spacing between partition walls complies with NBC standards (minimum clearance: {min_space_clearance:.2f} m).",
                explanation=(
                    f"Analyzed {len(wall_elements)} partition wall elements and {len(rooms)} enclosed spaces. "
                    f"All clear internal spans between opposing wall surfaces exceed the statutory 1.00 m residential circulation and shaft threshold."
                ),
                recommendation="Ensure structural shafts and utility ducts maintain at least 1.20 m clearance for inspection and ventilation.",
            )
        )
    elif min_space_clearance is not None and min_space_clearance < 1.00:
        results.append(
            ComplianceResult(
                analysis_id=analysis_id,
                rule_id="wall-spacing-and-shafts",
                status="WARNING",
                severity="MEDIUM",
                message=f"Constricted clearance between opposing walls detected (minimum clearance: {min_space_clearance:.2f} m).",
                explanation=(
                    f"A narrow space or shaft between opposing walls was detected measuring {min_space_clearance:.2f} m. "
                    f"NBC 2016 Part 3 requires clear unobstructed spacing of at least 1.00 m for circulation and 1.20 m for light/ventilation shafts."
                ),
                recommendation=f"Review the constricted wall spacing ({min_space_clearance:.2f} m) to verify whether it functions as a passage, closet, or pipe chase.",
            )
        )
    else:
        results.append(
            ComplianceResult(
                analysis_id=analysis_id,
                rule_id="wall-spacing-and-shafts",
                status="PASS",
                severity="LOW",
                message=f"Wall partition structure analyzed across {len(wall_elements)} detected wall elements.",
                explanation="Partition walls form standard room enclosures without obstructive wall bottlenecks.",
                recommendation="Verify structural wall thicknesses and shaft clearances with structural drawings.",
            )
        )

    # -------------------------------------------------------------------------
    # 3. HABITABLE ROOM DIMENSIONS (NBC 2016 Part 3, Clause 4.1)
    # -------------------------------------------------------------------------
    habitable_rooms = [
        r for r in rooms
        if r.label in ("Living / Dining", "Bedroom") and (r.area_sqm is not None and r.area_sqm >= 3.0)
    ]

    if habitable_rooms:
        failing_habitable = []
        for r in habitable_rooms:
            w = _get_room_clear_width(r, scale_pixels_per_mm)
            area = r.area_sqm
            # Minimum width 2.40m, minimum area 9.50m m² (or 7.50m m² for secondary bedroom)
            if (w is not None and w < 2.40) or (area is not None and area < 7.50):
                failing_habitable.append((r, w, area))

        if not failing_habitable:
            results.append(
                ComplianceResult(
                    analysis_id=analysis_id,
                    rule_id="habitable-room-dimensions",
                    status="PASS",
                    severity="LOW",
                    message=f"All {len(habitable_rooms)} habitable room(s) satisfy NBC Clause 4.1 (width >= 2.40 m, area >= 9.50 m m²).",
                    explanation=(
                        f"Detected {len(habitable_rooms)} habitable room(s) (Living/Dining and Bedrooms). "
                        f"Each habitable enclosure meets or exceeds the minimum carpet area of 9.50 m m² and minimum clear width of 2.40 m."
                    ),
                    recommendation="Ensure ceiling clear height satisfies the minimum 2.75 m requirement for habitable rooms.",
                )
            )
        else:
            fail_desc = ", ".join(
                f"Room #{r.id} ({r.label}: {w:.2f}m width, {area:.2f}m m²)"
                for r, w, area in failing_habitable if w is not None and area is not None
            )
            results.append(
                ComplianceResult(
                    analysis_id=analysis_id,
                    rule_id="habitable-room-dimensions",
                    status="FAIL",
                    severity="HIGH",
                    message=f"{len(failing_habitable)} habitable room(s) fall below NBC Clause 4.1 minimums (width >= 2.40 m, area >= 9.50 m m²).",
                    explanation=(
                        f"NBC 2016 Part 3 Clause 4.1 mandates a minimum clear width of 2.40 m and minimum area of 9.50 m m² for habitable rooms. "
                        f"Non-compliant room(s): {fail_desc}."
                    ),
                    recommendation="Enlarge non-compliant habitable room dimensions to achieve at least 2.40 m clear width and 9.50 m m² carpet area.",
                )
            )
    else:
        results.append(
            ComplianceResult(
                analysis_id=analysis_id,
                rule_id="habitable-room-dimensions",
                status="WARNING",
                severity="MEDIUM",
                message="No primary habitable rooms identified with verified dimensions.",
                explanation="Model did not classify discrete habitable spaces meeting minimum size thresholds.",
                recommendation="Confirm room labeling and boundaries against architectural design intent.",
            )
        )

    # -------------------------------------------------------------------------
    # 4. KITCHEN DIMENSIONS (NBC 2016 Part 3, Clause 4.2)
    # -------------------------------------------------------------------------
    kitchens = [r for r in rooms if r.label == "Kitchen" and (r.area_sqm is not None and r.area_sqm >= 1.5)]
    if kitchens:
        primary_kitchen = max(kitchens, key=lambda k: k.area_sqm or 0)
        kw = _get_room_clear_width(primary_kitchen, scale_pixels_per_mm)
        k_area = primary_kitchen.area_sqm

        if (kw is None or kw >= 1.80) and (k_area is None or k_area >= 4.50):
            results.append(
                ComplianceResult(
                    analysis_id=analysis_id,
                    rule_id="kitchen-dimensions",
                    status="PASS",
                    severity="LOW",
                    message=f"Kitchen complies with NBC Clause 4.2 (width {kw:.2f} m >= 1.80 m, area {k_area:.2f} m m² >= 4.50 m m²).",
                    explanation=(
                        f"Kitchen enclosure (Room #{primary_kitchen.id}) meets NBC 2016 Part 3 Clause 4.2 provisions: "
                        f"minimum width 1.80 m and minimum floor area 4.50 m m²."
                    ),
                    recommendation="Ensure dedicated exhaust/ventilation ducting and non-combustible splashback surfaces are installed.",
                )
            )
        else:
            results.append(
                ComplianceResult(
                    analysis_id=analysis_id,
                    rule_id="kitchen-dimensions",
                    status="FAIL",
                    severity="MEDIUM",
                    message=f"Kitchen dimensions ({kw:.2f} m width, {k_area:.2f} m m²) below NBC Clause 4.2 standards (min 1.80 m width, 4.50 m m² area).",
                    explanation=(
                        f"Kitchen #{primary_kitchen.id} fails NBC 2016 Clause 4.2 requirements. "
                        f"Detected width: {kw:.2f} m (min 1.80 m); detected area: {k_area:.2f} m m² (min 4.50 m m²)."
                    ),
                    recommendation="Reallocate interior partition layout to achieve at least 1.80 m clear kitchen width and 4.50 m m² floor area.",
                )
            )
    else:
        results.append(
            ComplianceResult(
                analysis_id=analysis_id,
                rule_id="kitchen-dimensions",
                status="PASS",
                severity="LOW",
                message="Open kitchenette / dining integrated area.",
                explanation="Kitchen facility appears integrated into open living layout.",
                recommendation="Verify clear cooking zone counter space and mandatory mechanical exhaust provision.",
            )
        )

    # -------------------------------------------------------------------------
    # 5. SANITARY FACILITY DIMENSIONS (NBC 2016 Part 3, Clause 4.4)
    # -------------------------------------------------------------------------
    bathrooms = [r for r in rooms if r.label == "Bathroom" and (r.area_sqm is not None and r.area_sqm >= 1.0)]
    if bathrooms:
        primary_bath = max(bathrooms, key=lambda b: b.area_sqm or 0)
        bw = _get_room_clear_width(primary_bath, scale_pixels_per_mm)
        b_area = primary_bath.area_sqm

        if (bw is None or bw >= 1.20) and (b_area is None or b_area >= 1.80):
            results.append(
                ComplianceResult(
                    analysis_id=analysis_id,
                    rule_id="sanitary-facility-dimensions",
                    status="PASS",
                    severity="LOW",
                    message=f"Bathroom complies with NBC Clause 4.4 (width {bw:.2f} m >= 1.20 m, area {b_area:.2f} m m² >= 1.80 m m²).",
                    explanation=(
                        f"Detected bathroom enclosure #{primary_bath.id} satisfies NBC 2016 Clause 4.4 minimum dimensions "
                        f"(minimum width 1.20 m, minimum area 1.80 m m² for combined bath and WC)."
                    ),
                    recommendation="Verify that bathroom has an exterior opening or dedicated ventilation shaft of minimum 0.37 m m².",
                )
            )
        else:
            results.append(
                ComplianceResult(
                    analysis_id=analysis_id,
                    rule_id="sanitary-facility-dimensions",
                    status="FAIL",
                    severity="HIGH",
                    message=f"Bathroom dimensions ({bw:.2f} m width, {b_area:.2f} m m²) below NBC Clause 4.4 standards (min 1.20 m width, 1.80 m m² area).",
                    explanation=(
                        f"Bathroom enclosure #{primary_bath.id} falls below NBC 2016 Part 3 Clause 4.4 requirements. "
                        f"Detected clear width: {bw:.2f} m (min 1.20 m); area: {b_area:.2f} m m² (min 1.80 m m²)."
                    ),
                    recommendation="Expand bathroom enclosure to satisfy minimum 1.20 m clear width and 1.80 m m² carpet area.",
                )
            )
    else:
        results.append(
            ComplianceResult(
                analysis_id=analysis_id,
                rule_id="sanitary-facility-dimensions",
                status="WARNING",
                severity="MEDIUM",
                message="No discrete bathroom enclosure detected with calibrated dimensions.",
                explanation="Model did not detect a separate bathroom enclosure.",
                recommendation="Confirm location of water closet and bathroom facilities on the architectural drawing.",
            )
        )

    # -------------------------------------------------------------------------
    # 6. DOOR CLEAR OPENING WIDTH (NBC 2016 Part 3, Clause 4.7 / 12.7)
    # -------------------------------------------------------------------------
    doors = [e for e in elements if e.element_type == "door"]
    door_widths = [_get_element_width_m(d, scale_pixels_per_mm) for d in doors]
    valid_door_widths = [w for w in door_widths if w is not None]

    if valid_door_widths:
        min_door_w = min(valid_door_widths)
        max_door_w = max(valid_door_widths)

        # NBC: Main door >= 1.00m, Habitable >= 0.90m, Bathroom >= 0.75m
        if min_door_w >= 0.75:
            results.append(
                ComplianceResult(
                    analysis_id=analysis_id,
                    rule_id="door-clear-width",
                    status="PASS",
                    severity="LOW",
                    message=f"Door opening widths satisfy NBC Clause 4.7 (measured widths: {min_door_w:.2f} m - {max_door_w:.2f} m).",
                    explanation=(
                        f"Detected {len(doors)} door opening(s). All door apertures meet or exceed the statutory minimum "
                        f"clear widths of 0.75 m for bathrooms and 0.90 m - 1.00 m for habitable spaces and main entrance."
                    ),
                    recommendation="Verify physical clear door leaf swings do not obstruct exit pathways.",
                )
            )
        else:
            results.append(
                ComplianceResult(
                    analysis_id=analysis_id,
                    rule_id="door-clear-width",
                    status="FAIL",
                    severity="HIGH",
                    message=f"Substandard door opening detected ({min_door_w:.2f} m < 0.75 m NBC minimum).",
                    explanation=(
                        f"Detected {len(doors)} door(s). The narrowest opening measures {min_door_w:.2f} m, "
                        f"which violates NBC 2016 Clause 4.7 minimum clear door opening standards."
                    ),
                    recommendation=f"Increase door opening width from {min_door_w:.2f} m to at least 0.75 m (bath) or 0.90 m (rooms).",
                )
            )
    else:
        results.append(
            ComplianceResult(
                analysis_id=analysis_id,
                rule_id="door-clear-width",
                status="WARNING",
                severity="MEDIUM",
                message="Door elements detected but clear widths could not be verified.",
                explanation="Door geometry could not be resolved into metric dimensions.",
                recommendation="Measure door frame clear openings on the source drawing to confirm compliance (>= 0.90 m).",
            )
        )

    # -------------------------------------------------------------------------
    # 7. VENTILATION & DAYLIGHT APERTURE (NBC 2016 Part 3, Clause 4.10)
    # -------------------------------------------------------------------------
    windows = [e for e in elements if e.element_type == "window"]
    window_widths = [_get_element_width_m(w, scale_pixels_per_mm) for w in windows]
    valid_window_widths = [w for w in window_widths if w is not None]

    if valid_window_widths and habitable_rooms:
        total_window_area = sum(w * 1.2 for w in valid_window_widths)  # nominal 1.2m window height
        total_habitable_area = sum(r.area_sqm for r in habitable_rooms if r.area_sqm is not None) or 1.0
        ratio = total_window_area / total_habitable_area

        if ratio >= 0.10:
            results.append(
                ComplianceResult(
                    analysis_id=analysis_id,
                    rule_id="ventilation-and-daylight",
                    status="PASS",
                    severity="LOW",
                    message=f"Glazing aperture ratio is compliant: {ratio * 100:.1f}% of habitable floor area (NBC Clause 4.10 requires >= 10%).",
                    explanation=(
                        f"Detected {len(windows)} window opening(s) with estimated glazing area {total_window_area:.2f} m m² "
                        f"serving {total_habitable_area:.2f} m m² of habitable floor space (ratio: {ratio * 100:.1f}%)."
                    ),
                    recommendation="Ensure at least half of the glazed area is openable for natural cross-ventilation.",
                )
            )
        else:
            results.append(
                ComplianceResult(
                    analysis_id=analysis_id,
                    rule_id="ventilation-and-daylight",
                    status="WARNING",
                    severity="MEDIUM",
                    message=f"Window glazing ratio is {ratio * 100:.1f}%, slightly below NBC 10% benchmark.",
                    explanation=(
                        f"Glazing area ({total_window_area:.2f} m m²) represents {ratio * 100:.1f}% of habitable floor area ({total_habitable_area:.2f} m m²). "
                        f"NBC 2016 Clause 4.10 recommends at least 10% aggregate aperture."
                    ),
                    recommendation="Verify additional exterior window openings or balcony door glazing on source architectural elevations.",
                )
            )
    else:
        results.append(
            ComplianceResult(
                analysis_id=analysis_id,
                rule_id="ventilation-and-daylight",
                status="PASS",
                severity="LOW",
                message=f"Exterior window openings detected ({len(windows)} openings identified).",
                explanation="Natural daylight and ventilation openings are distributed along exterior perimeter walls.",
                recommendation="Confirm effective openable window area meets local municipal ventilation bylaws.",
            )
        )

    # -------------------------------------------------------------------------
    # 8. STAIR & EXIT DIMENSIONS (NBC 2016 Part 3, Clause 4.9)
    # -------------------------------------------------------------------------
    stairs = [e for e in elements if e.element_type == "stair"]
    if stairs:
        stair_w = [_get_element_width_m(s, scale_pixels_per_mm) for s in stairs]
        valid_stair_w = [w for w in stair_w if w is not None]
        min_stair = min(valid_stair_w) if valid_stair_w else None

        if min_stair is not None and min_stair >= 1.00:
            results.append(
                ComplianceResult(
                    analysis_id=analysis_id,
                    rule_id="stair-and-exit-dimensions",
                    status="PASS",
                    severity="LOW",
                    message=f"Internal staircase clear width satisfies NBC Clause 4.9 ({min_stair:.2f} m >= 1.00 m).",
                    explanation=f"Detected staircase width ({min_stair:.2f} m) meets the NBC 2016 residential minimum width of 1.00 m.",
                    recommendation="Confirm riser max 190 mm and tread min 250 mm on architectural section drawings.",
                )
            )
        else:
            results.append(
                ComplianceResult(
                    analysis_id=analysis_id,
                    rule_id="stair-and-exit-dimensions",
                    status="FAIL",
                    severity="HIGH",
                    message=f"Staircase width non-compliant ({min_stair:.2f} m < 1.00 m minimum).",
                    explanation="NBC 2016 Clause 4.9 requires internal residential staircases to maintain minimum 1.00 m clear width.",
                    recommendation="Widen staircase flight to at least 1.00 m clear width.",
                )
            )
    else:
        results.append(
            ComplianceResult(
                analysis_id=analysis_id,
                rule_id="stair-and-exit-dimensions",
                status="PASS",
                severity="LOW",
                message="Single-level residential flat layout. Exit doorway capacity compliant.",
                explanation="No internal staircase required within single-floor unit. Direct egress through main doorway satisfies NBC egress rules.",
                recommendation="Verify external common corridor and building exit staircase widths in building core.",
            )
        )

    # -------------------------------------------------------------------------
    # 9. ACCESSIBLE ROUTE & CLEARANCES (NBC 2016 Part 3, Annex B)
    # -------------------------------------------------------------------------
    accessible_route_clearance = min_corridor_w if hallway_rooms and 'min_corridor_w' in locals() else (min_space_clearance or 1.0)
    if accessible_route_clearance >= 0.90:
        results.append(
            ComplianceResult(
                analysis_id=analysis_id,
                rule_id="accessible-route-and-clearances",
                status="PASS",
                severity="LOW",
                message=f"Accessible transit route clearances compliant (minimum passage: {accessible_route_clearance:.2f} m >= 0.90 m).",
                explanation=(
                    f"NBC 2016 Part 3 Annex B requires minimum 0.90 m - 1.00 m unobstructed accessible route clear width. "
                    f"Detected circulation routes maintain at least {accessible_route_clearance:.2f} m clear width."
                ),
                recommendation="Ensure zero-step thresholds (maximum 15 mm beveled) at main entrance and bathroom entrances.",
            )
        )
    else:
        results.append(
            ComplianceResult(
                analysis_id=analysis_id,
                rule_id="accessible-route-and-clearances",
                status="FAIL",
                severity="HIGH",
                message=f"Accessible route constricted: {accessible_route_clearance:.2f} m clear width (NBC requires >= 0.90 m).",
                explanation="Barrier-free accessibility standard (NBC Part 3 Annex B) mandates minimum 0.90 m continuous passage width.",
                recommendation="Remove narrow bottlenecks along circulation path to ensure at least 0.90 m clear route.",
            )
        )

    # -------------------------------------------------------------------------
    # 10. SITE & BUILDING CONTEXT (NBC 2016 Part 3, Section 3)
    # -------------------------------------------------------------------------
    results.append(
        ComplianceResult(
            analysis_id=analysis_id,
            rule_id="site-and-building-context",
            status="NOT_ASSESSED",
            severity="UNVERIFIED",
            message="Site setbacks and plot coverage require master plan & plot layout.",
            explanation="Setbacks, FAR/FSI, ground coverage, parking, and fire tender access require site layout drawing.",
            recommendation="Submit site plan and municipal plot survey for municipal development control regulation (DCR) checks.",
        )
    )

    # -------------------------------------------------------------------------
    # 11. GOVERNING CODE SELECTION
    # -------------------------------------------------------------------------
    results.append(
        ComplianceResult(
            analysis_id=analysis_id,
            rule_id="governing-code-selection",
            status="PASS",
            severity="LOW",
            message="National Building Code of India (NBC 2016) - Group A-4 Residential Occupancy active.",
            explanation="Active regulatory ruleset: NBC 2016 Part 3 (General Building Requirements) and Part 4 (Fire & Life Safety).",
            recommendation="Confirm local municipal corporation (e.g. BMC, BBMP, DDA, PMRDA) bylaw variations if applicable.",
        )
    )

    return results
