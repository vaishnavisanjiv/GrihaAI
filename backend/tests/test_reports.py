import io

from PIL import Image

from app.models.analysis import AnalysisRun, ComplianceResult


def create_png_bytes(width=200, height=120, color=(0, 255, 0)):
    image = Image.new("RGB", (width, height), color)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_generate_analysis_report(client, user_token_headers, db):
    project_response = client.post(
        "/api/projects/",
        headers=user_token_headers,
        json={
            "name": "Report Demo",
            "description": "Project for report generation",
            "building_type": "residential",
            "jurisdiction": "Bengaluru",
        },
    )
    project_id = project_response.json()["id"]

    upload_response = client.post(
        "/api/floor-plans/upload",
        headers=user_token_headers,
        data={"project_id": project_id},
        files={"file": ("demo-report-plan.png", create_png_bytes(), "image/png")},
    )
    floor_plan_id = upload_response.json()["id"]

    analysis = AnalysisRun(
        floor_plan_id=floor_plan_id,
        status="COMPLETED",
        cv_method="cubicasa5k-unet-segmentation",
        model_version="test-model",
    )
    db.add(analysis)
    db.flush()
    db.add(
        ComplianceResult(
            analysis_id=analysis.id,
            rule_id="room-area-minimum",
            status="PASS",
            message="Test finding",
        )
    )
    db.commit()
    db.refresh(analysis)
    analysis_id = analysis.id

    report_response = client.get(
        f"/api/reports/{analysis_id}",
        headers=user_token_headers,
    )

    assert report_response.status_code == 200
    payload = report_response.json()
    assert payload["analysis_id"] == analysis_id
    assert payload["project_name"] == "Report Demo"
    assert payload["model_version"] == "test-model"
    assert "rules" in payload
    assert payload["assessment_type"] == "preliminary_screening"
    assert "not an nbc compliance certificate" in payload["assessment_notice"].lower()
    assert "overall_score" not in payload
    assert payload["summary"]["not_assessed_count"] == 1
    assert payload["rules"][0]["status"] == "NOT_ASSESSED"

    analysis_response = client.get(
        f"/api/analysis/{analysis_id}",
        headers=user_token_headers,
    )
    assert analysis_response.status_code == 200
    assert analysis_response.json()["compliance_results"][0]["status"] == "NOT_ASSESSED"

    compliance_response = client.get(
        f"/api/analysis/{analysis_id}/compliance",
        headers=user_token_headers,
    )
    assert compliance_response.status_code == 200
    assert compliance_response.json()[0]["status"] == "NOT_ASSESSED"

    pdf_response = client.get(
        f"/api/reports/{analysis_id}/download",
        headers=user_token_headers,
    )

    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"].startswith("application/pdf")
    assert b"Overall Score" not in pdf_response.content
