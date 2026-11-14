"""
Tests for the asynchronous analysis flow:
  POST /{floor_plan_id}/start -> 202 Accepted, status=PENDING
  GET  /{analysis_id}/status  -> lightweight status polling
  Background task transitions status to RUNNING -> COMPLETED or FAILED
"""
import pytest
from unittest.mock import patch

from app.models.analysis import AnalysisRun
from app.models.floor_plan import FloorPlan
from app.models.project import Project
from app.services import model_analysis_service


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_project_and_floor_plan(db, user):
    project = Project(user_id=user.id, name="Async analysis project")
    db.add(project)
    db.flush()
    floor_plan = FloorPlan(
        project_id=project.id,
        filename="plan.png",
        original_filename="plan.png",
        storage_path="nonexistent.png",
        file_type=".png",
        file_size=1,
    )
    db.add(floor_plan)
    db.commit()
    db.refresh(floor_plan)
    return project, floor_plan


# ---------------------------------------------------------------------------
# start_analysis returns 503 when no model checkpoint is available
# ---------------------------------------------------------------------------

def test_start_analysis_no_model_returns_503(client, user_token_headers, db, test_user):
    _project, floor_plan = _create_project_and_floor_plan(db, test_user)
    with patch.object(model_analysis_service, "has_trained_model", return_value=False):
        response = client.post(
            f"/api/analysis/{floor_plan.id}/start",
            headers=user_token_headers,
        )
    assert response.status_code == 503


# ---------------------------------------------------------------------------
# start_analysis returns 202 Accepted (PENDING) when a model is present.
# The background task is mocked to prevent database conflict in tests.
# ---------------------------------------------------------------------------

def test_start_analysis_accepted_with_model(client, user_token_headers, db, test_user):
    _project, floor_plan = _create_project_and_floor_plan(db, test_user)
    with (
        patch.object(model_analysis_service, "has_trained_model", return_value=True),
        patch("app.api.analysis._run_analysis_in_background", return_value=None) as mock_bg,
    ):
        response = client.post(
            f"/api/analysis/{floor_plan.id}/start",
            headers=user_token_headers,
        )
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "PENDING"
    assert body["floor_plan_id"] == floor_plan.id
    assert "id" in body
    mock_bg.assert_called_once()


# ---------------------------------------------------------------------------
# GET /{analysis_id}/status returns a lightweight status view
# ---------------------------------------------------------------------------

def test_get_analysis_status_returns_pending(client, user_token_headers, db, test_user):
    _project, floor_plan = _create_project_and_floor_plan(db, test_user)
    analysis = AnalysisRun(floor_plan_id=floor_plan.id, status="PENDING")
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    response = client.get(
        f"/api/analysis/{analysis.id}/status",
        headers=user_token_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == analysis.id
    assert body["status"] == "PENDING"
    assert body["floor_plan_id"] == floor_plan.id
    assert "rooms" not in body
    assert "elements" not in body


def test_get_analysis_status_returns_running(client, user_token_headers, db, test_user):
    _project, floor_plan = _create_project_and_floor_plan(db, test_user)
    analysis = AnalysisRun(floor_plan_id=floor_plan.id, status="RUNNING")
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    response = client.get(
        f"/api/analysis/{analysis.id}/status",
        headers=user_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "RUNNING"


def test_get_analysis_status_404_for_other_user(client, db, test_user):
    from app.models.user import User
    from app.core.security import get_password_hash

    other_user = User(
        email="other@example.com",
        name="Other",
        password_hash=get_password_hash("pass"),
    )
    db.add(other_user)
    db.flush()
    project = Project(user_id=other_user.id, name="Other project")
    db.add(project)
    db.flush()
    floor_plan = FloorPlan(
        project_id=project.id,
        filename="plan.png",
        original_filename="plan.png",
        storage_path="x.png",
        file_type=".png",
        file_size=1,
    )
    db.add(floor_plan)
    db.flush()
    analysis = AnalysisRun(floor_plan_id=floor_plan.id, status="PENDING")
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    r = client.post("/api/auth/login", data={"username": "test@example.com", "password": "password123"})
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    response = client.get(f"/api/analysis/{analysis.id}/status", headers=headers)
    assert response.status_code == 404
