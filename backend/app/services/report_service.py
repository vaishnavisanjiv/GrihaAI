import os
import json
import tempfile
from collections import Counter
from typing import Dict, Any, List
from xml.sax.saxutils import escape

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
)
from sqlalchemy.orm import Session

from app.models.analysis import AnalysisRun, ComplianceResult, Room, DetectedElement, SpatialEdge
from app.models.floor_plan import FloorPlan
from app.models.project import Project
from app.services.analysis_service import mark_findings_unassessed


def generate_report(db: Session, analysis_id: int) -> Dict[str, Any]:
    analysis = db.query(AnalysisRun).filter(AnalysisRun.id == analysis_id).first()
    if not analysis:
        raise ValueError("Analysis not found")

    floor_plan = db.query(FloorPlan).filter(FloorPlan.id == analysis.floor_plan_id).first()
    project = db.query(Project).filter(Project.id == floor_plan.project_id).first() if floor_plan else None
    rules = db.query(ComplianceResult).filter(ComplianceResult.analysis_id == analysis_id).all()
    is_calibrated = bool(
        floor_plan
        and floor_plan.scale_source == "user-calibrated"
        and floor_plan.scale_pixels_per_mm
        and floor_plan.scale_pixels_per_mm > 0
    )
    mark_findings_unassessed(rules, scale_calibrated=is_calibrated)

    rooms = db.query(Room).filter(Room.analysis_id == analysis_id).all()
    elements = db.query(DetectedElement).filter(DetectedElement.analysis_id == analysis_id).all()
    spatial_edges = db.query(SpatialEdge).filter(SpatialEdge.analysis_id == analysis_id).all()

    room_categories = Counter(r.label for r in rooms if r.label)
    element_categories = Counter(e.element_type for e in elements if e.element_type)

    reviewed_edges = sum(1 for e in spatial_edges if e.reviews and len(e.reviews) > 0)

    recommendations = []
    for rule in rules:
        if rule.recommendation and rule.recommendation not in recommendations:
            recommendations.append(rule.recommendation)

    is_calibrated = bool(floor_plan and floor_plan.scale_source == "user-calibrated" and floor_plan.scale_pixels_per_mm)

    if analysis.cv_method == "cubicasa5k-unet-segmentation":
        scale_text = (
            "Metric measurements are calibrated."
            if is_calibrated
            else "Dimensions are uncalibrated (pixel area only)."
        )
        narrative = (
            f"The system identified {len(rooms)} room regions across {len(room_categories)} categories and "
            f"{len(elements)} architectural elements in the uploaded floor plan. {len(spatial_edges)} spatial "
            f"relationship candidates were generated for human review. {scale_text} Building-code compliance has "
            f"not been assessed against a verified regulatory catalog."
        )
    else:
        narrative = (
            "This is a prototype/demo result and includes synthetic example elements. It is not an analysis "
            "of the uploaded plan and must not be used for design or approval decisions."
        )

    return {
        "analysis_id": analysis_id,
        "report_title": "BuildGuard AI Preliminary Plan Review",
        "assessment_type": "preliminary_screening",
        "assessment_notice": (
            "This report contains preliminary model-generated detections and geometric observations. "
            "It is not an NBC compliance certificate, building approval or substitute for professional architectural review."
        ),
        "project_name": project.name if project else "General Project",
        "jurisdiction": project.jurisdiction if project else "Not Specified",
        "floor_plan_filename": floor_plan.original_filename if floor_plan else "floor_plan.png",
        "floor_plan_path": floor_plan.storage_path if floor_plan else None,
        "is_calibrated": is_calibrated,
        "generated_at": analysis.completed_at.isoformat() if analysis.completed_at else analysis.started_at.isoformat(),
        "status": "COMPLETED" if analysis.status == "COMPLETED" else analysis.status,
        "cv_method": analysis.cv_method,
        "model_version": analysis.model_version,
        "executive_summary": {
            "room_count": len(rooms),
            "element_count": len(elements),
            "candidate_count": len(spatial_edges),
            "reviewed_candidate_count": reviewed_edges,
            "not_assessed_count": sum(1 for rule in rules if rule.status == "NOT_ASSESSED"),
        },
        "summary": {
            "pass_count": sum(1 for rule in rules if rule.status == "PASS"),
            "warning_count": sum(1 for rule in rules if rule.status == "WARNING"),
            "fail_count": sum(1 for rule in rules if rule.status == "FAIL"),
            "not_assessed_count": sum(1 for rule in rules if rule.status == "NOT_ASSESSED"),
        },
        "room_breakdown": [{"category": cat, "count": cnt} for cat, cnt in room_categories.most_common()],
        "element_breakdown": [{"type": etype, "count": cnt} for etype, cnt in element_categories.most_common()],
        "rules": [
            {
                "rule_id": rule.rule_id,
                "status": rule.status,
                "severity": rule.severity,
                "message": rule.message,
                "explanation": rule.explanation,
                "recommendation": rule.recommendation,
            }
            for rule in rules
        ],
        "recommendations": recommendations,
        "narrative": narrative,
    }


def generate_pdf_report(db: Session, analysis_id: int) -> str:
    payload = generate_report(db, analysis_id)
    temp_dir = tempfile.gettempdir()
    output_path = os.path.join(temp_dir, f"buildguard-report-{analysis_id}.pdf")

    # Document setup
    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#0f172a")  # Slate 900
    cyan_color = colors.HexColor("#0284c7")     # Sky 600
    border_color = colors.HexColor("#cbd5e1")   # Slate 300
    bg_light = colors.HexColor("#f8fafc")       # Slate 50
    alert_bg = colors.HexColor("#fffbeb")       # Amber 50
    alert_border = colors.HexColor("#fde68a")   # Amber 200
    alert_text = colors.HexColor("#92400e")     # Amber 800

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=20,
        leading=24,
        textColor=primary_color,
        alignment=0,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=cyan_color,
        fontName="Helvetica-Bold",
    )
    h2_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=13,
        leading=17,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=6,
        fontName="Helvetica-Bold",
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
    )
    disclaimer_style = ParagraphStyle(
        "DisclaimerText",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=12,
        textColor=alert_text,
    )
    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1e293b"),
    )
    table_head_style = ParagraphStyle(
        "TableHead",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        fontName="Helvetica-Bold",
    )

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    story = []

    # 1. Header & Title
    story.append(Paragraph("BUILDGUARD AI ARCHITECTURAL REVIEW", subtitle_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Plan Analysis & Geometry Screening Report", title_style))
    story.append(Spacer(1, 8))

    # Meta Table
    exec_data = payload.get("executive_summary", {})
    meta_rows = [
        [
            Paragraph("<b>Project:</b> " + escape(str(payload.get("project_name", "—"))), body_style),
            Paragraph("<b>File:</b> " + escape(str(payload.get("floor_plan_filename", "—"))), body_style),
        ],
        [
            Paragraph("<b>Jurisdiction:</b> " + escape(str(payload.get("jurisdiction", "—"))), body_style),
            Paragraph("<b>Date:</b> " + escape(str(payload.get("generated_at", "—"))[:19]), body_style),
        ],
        [
            Paragraph("<b>Status:</b> " + escape(str(payload.get("status", "COMPLETED"))), body_style),
            Paragraph("<b>Analysis ID:</b> #" + str(payload.get("analysis_id", "—")), body_style),
        ],
    ]
    meta_table = Table(meta_rows, colWidths=[260, 260])
    meta_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg_light),
            ("BOX", (0, 0), (-1, -1), 1, border_color),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # Prominent Disclaimer Box
    disclaimer_p = Paragraph(f"<b>LEGAL & COMPLIANCE NOTICE:</b> {escape(payload.get('assessment_notice', ''))}", disclaimer_style)
    disclaimer_table = Table([[disclaimer_p]], colWidths=[520])
    disclaimer_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), alert_bg),
            ("BOX", (0, 0), (-1, -1), 1, alert_border),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    story.append(disclaimer_table)
    story.append(Spacer(1, 12))

    # 2. Executive Summary Metrics Table
    story.append(Paragraph("1. Executive Summary", h2_style))
    summary_cells = [
        [
            Paragraph(f"<b>Detected Rooms</b><br/><font size='14'><b>{exec_data.get('room_count', 0)}</b></font><br/>Identified regions", body_style),
            Paragraph(f"<b>Detected Elements</b><br/><font size='14'><b>{exec_data.get('element_count', 0)}</b></font><br/>Walls, doors, windows", body_style),
            Paragraph(f"<b>Spatial Candidates</b><br/><font size='14'><b>{exec_data.get('candidate_count', 0)}</b></font><br/>{exec_data.get('reviewed_candidate_count', 0)} reviewed", body_style),
            Paragraph(f"<b>Code Checks</b><br/><font size='14'><b>{exec_data.get('not_assessed_count', 8)}</b></font><br/>Not assessed", body_style),
        ]
    ]
    exec_table = Table(summary_cells, colWidths=[130, 130, 130, 130])
    exec_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg_light),
            ("GRID", (0, 0), (-1, -1), 1, border_color),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    story.append(exec_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph(payload.get("narrative", ""), body_style))
    story.append(Spacer(1, 10))

    # 3. Source Floor Plan Image (if available)
    plan_path = payload.get("floor_plan_path")
    if plan_path and os.path.exists(plan_path):
        try:
            with PILImage.open(plan_path) as im:
                orig_w, orig_h = im.size
            display_w = 420
            display_h = (orig_h / orig_w) * display_w
            if display_h > 240:
                display_h = 240
                display_w = (orig_w / orig_h) * display_h
            story.append(Paragraph("2. Uploaded Floor Plan", h2_style))
            img_flowable = Image(plan_path, width=display_w, height=display_h)
            img_table = Table([[img_flowable]], colWidths=[520])
            img_table.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(img_table)
            story.append(Spacer(1, 8))
        except Exception:
            pass

    # 4. Room & Architectural Elements Breakdown
    story.append(Paragraph("3. Room & Element Detection Summary", h2_style))
    room_items = payload.get("room_breakdown", [])
    element_items = payload.get("element_breakdown", [])

    breakdown_rows = [[
        Paragraph("Room Category", table_head_style),
        Paragraph("Count", table_head_style),
        Paragraph("Element Type", table_head_style),
        Paragraph("Count", table_head_style),
    ]]
    max_len = max(len(room_items), len(element_items), 1)
    for i in range(max_len):
        r_cat = room_items[i]["category"] if i < len(room_items) else "—"
        r_cnt = str(room_items[i]["count"]) if i < len(room_items) else ""
        e_type = element_items[i]["type"].capitalize() if i < len(element_items) else "—"
        e_cnt = str(element_items[i]["count"]) if i < len(element_items) else ""
        breakdown_rows.append([
            Paragraph(escape(r_cat), table_cell_style),
            Paragraph(r_cnt, table_cell_style),
            Paragraph(escape(e_type), table_cell_style),
            Paragraph(e_cnt, table_cell_style),
        ])

    breakdown_table = Table(breakdown_rows, colWidths=[160, 100, 160, 100])
    breakdown_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), primary_color),
            ("GRID", (0, 0), (-1, -1), 0.5, border_color),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, bg_light]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(breakdown_table)
    story.append(Spacer(1, 8))

    # Note regarding scale calibration
    story.append(
        Paragraph(
            "<i>Note on measurements: Pixel area indicates region footprint on the 2D image. "
            "Real-world dimensions ($m$ / $m^2$) require a verified image-to-physical scale calibration.</i>",
            body_style,
        )
    )
    story.append(Spacer(1, 12))

    # 5. Preliminary Compliance Screening (8 categories)
    story.append(Paragraph("4. Preliminary Compliance Screening (8 Categories)", h2_style))
    story.append(
        Paragraph(
            "Current findings are retained for screening context. The system does not have a verified, "
            "versioned NBC and local-authority rule catalog for these checks. Therefore, no compliance conclusion is provided.",
            body_style,
        )
    )
    story.append(Spacer(1, 6))

    rule_rows = [[
        Paragraph("Assessment Category", table_head_style),
        Paragraph("Status", table_head_style),
        Paragraph("Screening Observation / Rationale", table_head_style),
    ]]
    for rule in payload.get("rules", []):
        rule_rows.append([
            Paragraph(f"<b>{escape(rule['rule_id'].replace('-', ' ').title())}</b>", table_cell_style),
            Paragraph(f"<font color='#d97706'><b>{rule['status']}</b></font>", table_cell_style),
            Paragraph(escape(rule.get("message") or rule.get("explanation") or "Preliminary check."), table_cell_style),
        ])

    rule_table = Table(rule_rows, colWidths=[150, 90, 280])
    rule_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), primary_color),
            ("GRID", (0, 0), (-1, -1), 0.5, border_color),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, bg_light]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(rule_table)
    story.append(Spacer(1, 12))

    # 6. Recommendations & Next Steps
    story.append(Paragraph("5. Recommended Next Steps", h2_style))
    rec_items = payload.get("recommendations", [])
    if not rec_items:
        rec_items = [
            "Visually cross-reference the detected room polygons against the original drawing.",
            "Calibrate drawing scale with a known on-site dimension for metric calculations.",
            "Verify clear door opening widths and stair dimensions on the original drawings.",
            "Review potential room adjacency candidates in the spatial review workflow.",
            "Have a licensed architect or building official evaluate municipal bylaws and NBC provisions.",
        ]
    for item in rec_items[:6]:
        story.append(Paragraph(f"• {escape(item)}", body_style))
    story.append(Spacer(1, 12))

    # 7. Technical Details & Model Provenance
    story.append(Paragraph("6. Technical Provenance & Integrity", h2_style))
    provenance_rows = [
        [
            Paragraph("<b>Model Architecture:</b>", body_style),
            Paragraph("buildguard-unet-v1 (13-class semantic segmentation)", body_style),
        ],
        [
            Paragraph("<b>CV Pipeline:</b>", body_style),
            Paragraph(escape(str(payload.get("cv_method", "cubicasa5k-unet-segmentation"))), body_style),
        ],
        [
            Paragraph("<b>Checkpoint Provenance:</b>", body_style),
            Paragraph(f"<font size='7'>{escape(str(payload.get('model_version', 'Not recorded')))}</font>", body_style),
        ],
    ]
    prov_table = Table(provenance_rows, colWidths=[140, 380])
    prov_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg_light),
            ("BOX", (0, 0), (-1, -1), 0.5, border_color),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ])
    )
    story.append(prov_table)

    doc.build(story)
    return output_path
