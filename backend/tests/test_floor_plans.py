import io

from PIL import Image

from app.core.config import settings


def create_png_bytes(width=200, height=120, color=(0, 255, 0)):
    image = Image.new("RGB", (width, height), color)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_upload_and_process_floor_plan(client, user_token_headers):
    create_project_response = client.post(
        "/api/projects/",
        headers=user_token_headers,
        json={
            "name": "Floor Plan Demo",
            "description": "A sample plan for testing uploads",
            "building_type": "residential",
            "jurisdiction": "Bengaluru"
        },
    )
    project_id = create_project_response.json()["id"]

    upload_response = client.post(
        "/api/floor-plans/upload",
        headers=user_token_headers,
        data={"project_id": project_id},
        files={"file": ("demo-floor-plan.png", create_png_bytes(), "image/png")},
    )

    assert upload_response.status_code == 201
    payload = upload_response.json()
    assert payload["filename"] == "demo-floor-plan.png"

    floor_plan_id = payload["id"]
    process_response = client.post(
        f"/api/floor-plans/{floor_plan_id}/process",
        headers=user_token_headers,
    )

    assert process_response.status_code == 200
    processed = process_response.json()
    assert processed["status"] == "PROCESSED"
    assert processed["project_id"] == project_id


def test_list_floor_plans_for_user(client, user_token_headers):
    create_project_response = client.post(
        "/api/projects/",
        headers=user_token_headers,
        json={
            "name": "List Floor Plans",
            "description": "Project for listing plans",
            "building_type": "residential",
            "jurisdiction": "Pune"
        },
    )
    project_id = create_project_response.json()["id"]

    client.post(
        "/api/floor-plans/upload",
        headers=user_token_headers,
        data={"project_id": project_id},
        files={"file": ("demo-floor-plan-2.png", create_png_bytes(), "image/png")},
    )

    response = client.get(
        "/api/floor-plans/",
        headers=user_token_headers,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert any(plan["project_id"] == project_id for plan in response.json())


def test_upload_rejects_invalid_pdf_signature(client, user_token_headers):
    project_response = client.post(
        "/api/projects/",
        headers=user_token_headers,
        json={"name": "PDF validation"},
    )
    response = client.post(
        "/api/floor-plans/upload",
        headers=user_token_headers,
        data={"project_id": project_response.json()["id"]},
        files={"file": ("not-a-pdf.pdf", b"not a PDF", "application/pdf")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid PDF file"


def test_upload_enforces_size_limit(client, user_token_headers, monkeypatch):
    project_response = client.post(
        "/api/projects/",
        headers=user_token_headers,
        json={"name": "Upload size limit"},
    )
    monkeypatch.setattr(settings, "MAX_FILE_SIZE_MB", 0)
    response = client.post(
        "/api/floor-plans/upload",
        headers=user_token_headers,
        data={"project_id": project_response.json()["id"]},
        files={"file": ("plan.png", create_png_bytes(), "image/png")},
    )
    assert response.status_code == 413


def test_scale_calibration_uses_known_image_distance(client, user_token_headers):
    project_response = client.post(
        "/api/projects/",
        headers=user_token_headers,
        json={"name": "Scale calibration"},
    )
    floor_plan_response = client.post(
        "/api/floor-plans/upload",
        headers=user_token_headers,
        data={"project_id": project_response.json()["id"]},
        files={"file": ("plan.png", create_png_bytes(200, 120), "image/png")},
    )
    floor_plan_id = floor_plan_response.json()["id"]

    response = client.put(
        f"/api/floor-plans/{floor_plan_id}/scale",
        headers=user_token_headers,
        json={"x1": 10, "y1": 10, "x2": 110, "y2": 10, "known_distance_mm": 2000},
    )

    assert response.status_code == 200
    assert response.json()["scale_pixels_per_mm"] == 0.05
    assert response.json()["scale_source"] == "user-calibrated"


def test_scale_calibration_rejects_points_outside_image(client, user_token_headers):
    project_response = client.post(
        "/api/projects/",
        headers=user_token_headers,
        json={"name": "Invalid scale calibration"},
    )
    floor_plan_response = client.post(
        "/api/floor-plans/upload",
        headers=user_token_headers,
        data={"project_id": project_response.json()["id"]},
        files={"file": ("plan.png", create_png_bytes(200, 120), "image/png")},
    )
    floor_plan_id = floor_plan_response.json()["id"]

    response = client.put(
        f"/api/floor-plans/{floor_plan_id}/scale",
        headers=user_token_headers,
        json={"x1": -1, "y1": 10, "x2": 110, "y2": 10, "known_distance_mm": 2000},
    )

    assert response.status_code == 400
