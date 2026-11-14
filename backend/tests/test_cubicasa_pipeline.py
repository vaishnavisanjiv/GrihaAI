import sys
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from prepare_cubicasa import prepare_data, rasterize_annotation
from split_dataset import split_data
from validate_dataset import validate_data
import download_dataset
from floorplan_training import limit_records
from floorplan_training import scores_from_confusion
from dataset_statistics import build_dataset_statistics
import train_floorplan_model
from evaluate_floorplan_model import _write_overlay


def test_limit_records_uses_a_repeatable_random_subset():
    records = [{"id": str(index)} for index in range(10)]

    first = limit_records(records, 4, seed=19)
    second = limit_records(records, 4, seed=19)

    assert len(first) == 4
    assert first == second
    assert len({record["id"] for record in first}) == 4
    assert limit_records(records, None, seed=19) == records


def test_cubicasa_svg_polygons_are_rasterized_to_semantic_labels(tmp_path):
    svg_path = tmp_path / "model.svg"
    mask_path = tmp_path / "mask.png"
    svg_path.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">
        <g id="Wall"><polygon points="5,5 95,5 95,95 5,95"/></g>
        <g class="Space Bedroom"><polygon points="20,20 80,20 80,80 20,80"/></g>
        <g id="Door"><polygon points="45,5 55,5 55,15 45,15"/></g>
        <g id="Window"><polygon points="20,5 35,5 35,10 20,10"/></g>
        </svg>""",
        encoding="utf-8",
    )

    counts = rasterize_annotation(svg_path, mask_path, (100, 100))
    with Image.open(mask_path) as mask:
        labels = np.asarray(mask)

    assert counts["room_groups"] == 1
    assert labels[256, 256] == 4
    assert labels[40, 40] == 1
    assert labels[30, 256] == 11
    assert labels[35, 128] == 12
    assert labels[0, 0] == 0


def test_prepare_split_and_validate_dataset(tmp_path):
    raw_dir = tmp_path / "raw"
    for index in range(10):
        sample_dir = raw_dir / f"sample-{index}"
        sample_dir.mkdir(parents=True)
        Image.new("RGB", (100, 100), "white").save(sample_dir / "F1_scaled.png")
        (sample_dir / "model.svg").write_text(
            """<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">
            <g id="Wall"><polygon points="5,5 95,5 95,95 5,95"/></g>
            <g class="Space Kitchen"><polygon points="20,20 80,20 80,80 20,80"/></g>
            </svg>""",
            encoding="utf-8",
        )
    prepared = tmp_path / "prepared"
    assert prepare_data(raw_dir, prepared) == 10
    manifest = [json.loads(line) for line in (prepared / "manifest.jsonl").read_text().splitlines()]
    assert manifest[0]["source_dimensions"] == {"width": 100, "height": 100}
    preparation_report = json.loads((prepared / "preparation_report.json").read_text())
    assert preparation_report["annotation_count"] == 10
    assert preparation_report["prepared_count"] == 10
    assert preparation_report["skipped_count"] == 0
    split_dir = prepared / "splits"
    counts = split_data(prepared / "manifest.jsonl", split_dir, seed=19)
    assert counts == {"train": 7, "val": 1, "test": 2}
    assert validate_data(prepared, split_dir)
    statistics = build_dataset_statistics(prepared, split_dir)
    assert statistics["sample_count"] == 10
    assert statistics["annotation_exclusions"]["count"] == 0
    assert statistics["source_image_dimensions"]["counts"] == {"100x100": 10}
    assert statistics["all_samples"]["prepared_mask_dimensions"] == {"512x512": 10}
    assert statistics["all_samples"]["class_distribution"]["railing"]["pixel_count"] == 0
    assert sum(
        item["pixel_fraction"]
        for item in statistics["all_samples"]["class_distribution"].values()
    ) == pytest.approx(1.0)


def test_preparation_report_records_skipped_annotations(tmp_path):
    raw_dir = tmp_path / "raw"
    missing_image = raw_dir / "missing-image"
    missing_image.mkdir(parents=True)
    (missing_image / "model.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
        '<g class="Space Bedroom"><polygon points="1,1 9,1 9,9 1,9"/></g></svg>',
        encoding="utf-8",
    )
    no_room = raw_dir / "no-room"
    no_room.mkdir(parents=True)
    Image.new("RGB", (20, 10), "white").save(no_room / "F1.png")
    (no_room / "model.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="10">'
        '<g id="Wall"><polygon points="1,1 19,1 19,9 1,9"/></g></svg>',
        encoding="utf-8",
    )
    prepared = tmp_path / "prepared"

    try:
        prepare_data(raw_dir, prepared)
    except ValueError as exc:
        assert "No usable" in str(exc)
    else:
        raise AssertionError("dataset with no usable room labels should fail")

    report = json.loads((prepared / "preparation_report.json").read_text())
    assert report["annotation_count"] == 2
    assert report["prepared_count"] == 0
    assert report["skipped_count"] == 2
    assert {entry["source"] for entry in report["skipped"]} == {"missing-image", "no-room"}
    assert all(entry["reason"] for entry in report["skipped"])


def test_segmentation_metrics_include_class_precision_recall_f1_dice_and_confusion():
    from prepare_cubicasa import CLASS_NAMES

    matrix = np.zeros((len(CLASS_NAMES), len(CLASS_NAMES)), dtype=np.int64)
    matrix[0, 0] = 10
    matrix[0, 1] = 2
    matrix[1, 1] = 3
    matrix[1, 0] = 5

    scores = scores_from_confusion(matrix)

    assert scores["pixel_accuracy"] == pytest.approx(0.65)
    assert scores["class_metrics"]["background"]["precision"] == pytest.approx(10 / 15)
    assert scores["class_metrics"]["background"]["recall"] == pytest.approx(10 / 12)
    assert scores["class_metrics"]["background"]["f1"] == pytest.approx(20 / 27)
    assert scores["class_metrics"]["wall"]["dice"] == pytest.approx(6 / 13)


def test_segmentation_metrics_handle_empty_confusion_and_reject_invalid_shape():
    from prepare_cubicasa import CLASS_NAMES

    scores = scores_from_confusion(np.zeros((len(CLASS_NAMES), len(CLASS_NAMES)), dtype=np.int64))
    assert scores["mean_iou"] == 0.0
    assert scores["pixel_accuracy"] == 0.0
    assert scores["evaluated_classes"] == 0

    try:
        scores_from_confusion(np.zeros((2, 2), dtype=np.int64))
    except ValueError as exc:
        assert "shape" in str(exc)
    else:
        raise AssertionError("invalid confusion matrix shape should be rejected")


def test_unlabeled_railing_class_is_not_exposed_as_a_detection():
    from app.services.floorplan_model import ROOM_LABELS, UNSUPPORTED_CLASS_IDS

    assert 7 in UNSUPPORTED_CLASS_IDS
    assert 7 not in ROOM_LABELS


def test_training_uses_only_train_and_validation_splits(tmp_path, monkeypatch):
    import torch
    from torch import nn

    class TinySegmentationModel(nn.Module):
        def __init__(self, num_classes):
            super().__init__()
            self.classifier = nn.Conv2d(3, num_classes, kernel_size=1)

        def forward(self, image):
            return self.classifier(image)

    prepared = tmp_path / "prepared"
    split_dir = tmp_path / "splits"
    prepared.mkdir()
    split_dir.mkdir()
    records = []
    for split_name, sample_id in (("train", "train-1"), ("val", "val-1")):
        image_path = prepared / f"{sample_id}.png"
        mask_path = prepared / f"{sample_id}-mask.png"
        Image.new("RGB", (512, 512), (120, 120, 120)).save(image_path)
        mask_array = np.zeros((512, 512), dtype=np.uint8)
        mask_array[128:384, 128:384] = 2
        Image.fromarray(mask_array).save(mask_path)
        records.append(
            {
                "split": split_name,
                "record": {
                    "id": sample_id,
                    "image": image_path.name,
                    "mask": mask_path.name,
                },
            }
        )
    for split_name in ("train", "val"):
        split_records = [item["record"] for item in records if item["split"] == split_name]
        (split_dir / f"{split_name}.jsonl").write_text(
            "\n".join(json.dumps(record) for record in split_records) + "\n",
            encoding="utf-8",
        )
    monkeypatch.setattr(train_floorplan_model, "FloorPlanUNet", TinySegmentationModel)
    checkpoint_path = tmp_path / "model.pt"

    result = train_floorplan_model.train(
        prepared,
        split_dir,
        checkpoint_path,
        epochs=1,
        batch_size=1,
        early_stopping_patience=1,
    )

    assert result["epochs_completed"] == 1
    assert result["train_samples"] == 1
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    assert checkpoint["training_config"]["optimizer"] == "AdamW"
    assert checkpoint["training_config"]["mixed_precision"] is False


def test_qualitative_overlay_contains_original_ground_truth_and_prediction_panels(tmp_path):
    image = Image.new("RGB", (64, 48), (200, 200, 200))
    target = np.zeros((512, 512), dtype=np.uint8)
    prediction = np.full((512, 512), 1, dtype=np.uint8)
    output_path = tmp_path / "overlay.png"

    _write_overlay(image, target, prediction, output_path)

    with Image.open(output_path) as overlay:
        assert overlay.size == (1536, 542)


def test_cubicasa_annotation_without_spaces_is_rejected(tmp_path):
    svg_path = tmp_path / "no-rooms.svg"
    svg_path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
        '<g id="Wall"><polygon points="1,1 9,1 9,9 1,9"/></g></svg>',
        encoding="utf-8",
    )
    try:
        rasterize_annotation(svg_path, tmp_path / "mask.png", (10, 10))
    except ValueError as exc:
        assert "No supported Space polygons" in str(exc)
    else:
        raise AssertionError("annotation without room polygons should not be accepted")


def test_downloader_reuses_a_complete_existing_archive(tmp_path, monkeypatch):
    archive_path = tmp_path / "cubicasa5k.zip"
    archive_path.write_bytes(b"verified archive")
    checksum = hashlib.md5(archive_path.read_bytes()).hexdigest()
    monkeypatch.setattr(download_dataset, "EXPECTED_MD5", checksum)

    assert download_dataset.download_dataset(tmp_path) == archive_path
    assert archive_path.read_bytes() == b"verified archive"


def test_archive_checksum_failure_does_not_delete_existing_file(tmp_path, monkeypatch):
    archive_path = tmp_path / "cubicasa5k.zip"
    archive_path.write_bytes(b"incomplete download")
    monkeypatch.setattr(download_dataset, "EXPECTED_MD5", "0" * 32)

    try:
        download_dataset.verify_archive(archive_path)
    except ValueError as exc:
        assert "left untouched" in str(exc)
    else:
        raise AssertionError("invalid archive should not pass checksum validation")

    assert archive_path.read_bytes() == b"incomplete download"
