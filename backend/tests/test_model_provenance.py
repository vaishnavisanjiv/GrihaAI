import hashlib

import pytest

from app.models.analysis import AnalysisRun
from app.models.floor_plan import FloorPlan
from app.models.project import Project
from app.services import floorplan_model, model_analysis_service


def test_checkpoint_fingerprint_detects_file_replacement(tmp_path):
    checkpoint_path = tmp_path / "floorplan_unet.pt"
    checkpoint_path.write_bytes(b"initial checkpoint")
    initial_sha256 = model_analysis_service._checkpoint_sha256(checkpoint_path)

    checkpoint_path.write_bytes(b"replacement checkpoint")

    with pytest.raises(RuntimeError, match="checkpoint changed while analysis was loading"):
        model_analysis_service._ensure_checkpoint_unchanged(checkpoint_path, initial_sha256)


def _create_analysis_records(db, test_user):
    project = Project(user_id=test_user.id, name="Model provenance")
    db.add(project)
    db.flush()
    floor_plan = FloorPlan(
        project_id=project.id,
        filename="plan.png",
        original_filename="plan.png",
        storage_path="unused.png",
        file_type=".png",
        file_size=1,
    )
    db.add(floor_plan)
    db.flush()
    analysis = AnalysisRun(floor_plan_id=floor_plan.id, status="PENDING")
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis, floor_plan


def test_analysis_persists_checkpoint_sha256_in_model_version(
    db, test_user, tmp_path, monkeypatch
):
    pytest.importorskip("torch")
    checkpoint_path = tmp_path / "floorplan_unet.pt"
    checkpoint_bytes = b"fixed test checkpoint"
    checkpoint_path.write_bytes(checkpoint_bytes)
    expected_sha256 = hashlib.sha256(checkpoint_bytes).hexdigest()
    analysis, floor_plan = _create_analysis_records(db, test_user)
    monkeypatch.setattr(
        model_analysis_service,
        "get_checkpoint_path",
        lambda: checkpoint_path,
    )
    monkeypatch.setattr(
        floorplan_model,
        "load_checkpoint",
        lambda _path, _device: (object(), {"best_epoch": 3}),
    )
    monkeypatch.setattr(
        model_analysis_service,
        "_add_model_predictions",
        lambda *_args: ([], []),
    )

    model_analysis_service.run_trained_analysis(db, analysis, floor_plan)

    db.refresh(analysis)
    assert analysis.status == "COMPLETED"
    assert analysis.cv_method == "cubicasa5k-unet-segmentation"
    assert analysis.model_version == f"buildguard-unet-v1-epoch-3-sha256:{expected_sha256}"
