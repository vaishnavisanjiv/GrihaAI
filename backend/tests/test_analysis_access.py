import io
import json

from PIL import Image

from app.api import analysis as analysis_api
from app.models.analysis import AnalysisRun, SpatialEdge


def create_png_bytes():
    image = Image.new("RGB", (200, 120), (255, 255, 255))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_analysis_resources_are_only_visible_to_their_owner(
    client, user_token_headers, db
):
    project_response = client.post(
        "/api/projects/",
        headers=user_token_headers,
        json={"name": "Private analysis"},
    )
    project_id = project_response.json()["id"]
    upload_response = client.post(
        "/api/floor-plans/upload",
        headers=user_token_headers,
        data={"project_id": project_id},
        files={"file": ("plan.png", create_png_bytes(), "image/png")},
    )
    floor_plan_id = upload_response.json()["id"]
    analysis = AnalysisRun(
        floor_plan_id=floor_plan_id,
        status="COMPLETED",
        cv_method="cubicasa5k-unet-segmentation",
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    analysis_id = analysis.id
    db.add(
        SpatialEdge(
            analysis_id=analysis_id,
            source_element_id=1,
            target_element_id=2,
            relationship_type="ADJACENT_TO_CANDIDATE",
            properties_json='{"confidence":0.6,"confidence_calibrated":false,"review_required":true}',
        )
    )
    db.commit()

    owner_summary = client.get(
        f"/api/analysis/{analysis_id}",
        headers=user_token_headers,
    )
    assert owner_summary.status_code == 200
    assert owner_summary.json()["spatial_edges"][0]["relationship_type"] == "ADJACENT_TO_CANDIDATE"
    assert (
        json.loads(owner_summary.json()["spatial_edges"][0]["properties_json"])[
            "confidence_calibrated"
        ]
        is False
    )

    client.post(
        "/api/auth/register",
        json={
            "email": "other-user@example.com",
            "name": "Other User",
            "password": "password123",
        },
    )
    login_response = client.post(
        "/api/auth/login",
        data={"username": "other-user@example.com", "password": "password123"},
    )
    other_user_headers = {
        "Authorization": f"Bearer {login_response.json()['access_token']}"
    }

    for path in (
        f"/api/analysis/{analysis_id}",
        f"/api/analysis/{analysis_id}/elements",
        f"/api/analysis/{analysis_id}/rooms",
        f"/api/analysis/{analysis_id}/graph",
        f"/api/analysis/{analysis_id}/compliance",
        f"/api/analysis/{analysis_id}/recommendations",
        f"/api/reports/{analysis_id}",
        f"/api/reports/{analysis_id}/download",
    ):
        response = client.get(path, headers=other_user_headers)
        assert response.status_code == 404, path

    assistant_response = client.post(
        f"/api/assistant/{analysis_id}/ask",
        headers=other_user_headers,
        json={"question": "What are the main risks?"},
    )
    assert assistant_response.status_code == 404

    foreign_analysis_response = client.post(
        f"/api/analysis/{floor_plan_id}/start",
        headers=other_user_headers,
    )
    assert foreign_analysis_response.status_code == 403


def test_analysis_requires_trained_model_instead_of_returning_synthetic_data(
    client, user_token_headers, db, monkeypatch
):
    project_response = client.post(
        "/api/projects/",
        headers=user_token_headers,
        json={"name": "Model required"},
    )
    upload_response = client.post(
        "/api/floor-plans/upload",
        headers=user_token_headers,
        data={"project_id": project_response.json()["id"]},
        files={"file": ("plan.png", create_png_bytes(), "image/png")},
    )
    floor_plan_id = upload_response.json()["id"]
    monkeypatch.setattr(analysis_api, "has_trained_model", lambda: False)

    response = client.post(
        f"/api/analysis/{floor_plan_id}/start",
        headers=user_token_headers,
    )

    assert response.status_code == 503
    assert "backend/models/floorplan_unet.pt" in response.json()["detail"]
    assert db.query(AnalysisRun).count() == 0


def test_owner_can_record_spatial_candidate_review_without_verifying_relationship(
    client, user_token_headers, db
):
    project_response = client.post(
        "/api/projects/",
        headers=user_token_headers,
        json={"name": "Candidate review"},
    )
    upload_response = client.post(
        "/api/floor-plans/upload",
        headers=user_token_headers,
        data={"project_id": project_response.json()["id"]},
        files={"file": ("plan.png", create_png_bytes(), "image/png")},
    )
    analysis = AnalysisRun(
        floor_plan_id=upload_response.json()["id"],
        status="COMPLETED",
        cv_method="cubicasa5k-unet-segmentation",
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    edge = SpatialEdge(
        analysis_id=analysis.id,
        source_element_id=1,
        target_element_id=2,
        relationship_type="ADJACENT_TO_CANDIDATE",
        properties_json='{"confidence":0.6,"confidence_calibrated":false,"review_required":true}',
    )
    db.add(edge)
    db.commit()
    db.refresh(edge)

    response = client.put(
        f"/api/analysis/{analysis.id}/graph/{edge.id}/review",
        headers=user_token_headers,
        json={"review_status": "plausible"},
    )

    assert response.status_code == 200
    properties = json.loads(response.json()["properties_json"])
    assert properties["review_status"] == "plausible"
    assert properties["reviewed_by_user_id"] is not None
    assert properties["reviewed_at"]
    assert properties["review_required"] is True
    assert properties["confidence_calibrated"] is False
    assert len(response.json()["reviews"]) == 1
    assert response.json()["reviews"][0]["review_status"] == "plausible"

    updated_response = client.put(
        f"/api/analysis/{analysis.id}/graph/{edge.id}/review",
        headers=user_token_headers,
        json={"review_status": "uncertain"},
    )
    assert updated_response.status_code == 200
    assert [review["review_status"] for review in updated_response.json()["reviews"]] == [
        "plausible",
        "uncertain",
    ]


def test_spatial_candidate_review_rejects_invalid_status_and_non_candidates(
    client, user_token_headers, db
):
    project_response = client.post(
        "/api/projects/",
        headers=user_token_headers,
        json={"name": "Invalid candidate review"},
    )
    upload_response = client.post(
        "/api/floor-plans/upload",
        headers=user_token_headers,
        data={"project_id": project_response.json()["id"]},
        files={"file": ("plan.png", create_png_bytes(), "image/png")},
    )
    analysis = AnalysisRun(floor_plan_id=upload_response.json()["id"], status="COMPLETED")
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    edge = SpatialEdge(
        analysis_id=analysis.id,
        source_element_id=1,
        target_element_id=2,
        relationship_type="CONNECTS_TO",
        properties_json='{"review_required":true}',
    )
    db.add(edge)
    db.commit()
    db.refresh(edge)
    url = f"/api/analysis/{analysis.id}/graph/{edge.id}/review"

    invalid_status = client.put(
        url,
        headers=user_token_headers,
        json={"review_status": "verified"},
    )
    assert invalid_status.status_code == 422

    non_candidate = client.put(
        url,
        headers=user_token_headers,
        json={"review_status": "plausible"},
    )
    assert non_candidate.status_code == 409


def test_spatial_candidate_review_is_owner_scoped(client, user_token_headers, db):
    project_response = client.post(
        "/api/projects/",
        headers=user_token_headers,
        json={"name": "Private candidate review"},
    )
    upload_response = client.post(
        "/api/floor-plans/upload",
        headers=user_token_headers,
        data={"project_id": project_response.json()["id"]},
        files={"file": ("plan.png", create_png_bytes(), "image/png")},
    )
    analysis = AnalysisRun(floor_plan_id=upload_response.json()["id"], status="COMPLETED")
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    edge = SpatialEdge(
        analysis_id=analysis.id,
        source_element_id=1,
        target_element_id=2,
        relationship_type="ADJACENT_TO_CANDIDATE",
        properties_json='{"review_required":true}',
    )
    db.add(edge)
    db.commit()
    db.refresh(edge)

    client.post(
        "/api/auth/register",
        json={
            "email": "reviewer@example.com",
            "name": "Reviewer",
            "password": "password123",
        },
    )
    login_response = client.post(
        "/api/auth/login",
        data={"username": "reviewer@example.com", "password": "password123"},
    )
    reviewer_headers = {
        "Authorization": "Bearer " + login_response.json()["access_token"]
    }
    response = client.put(
        f"/api/analysis/{analysis.id}/graph/{edge.id}/review",
        headers=reviewer_headers,
        json={"review_status": "uncertain"},
    )

    assert response.status_code == 404
