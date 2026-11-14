import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageDraw

from floorplan_training import (
    PROJECT_ROOT,
    CubiCasaSegmentationDataset,
    evaluate_model,
    load_model,
    read_jsonl,
)
from app.services.floorplan_model import CLASS_NAMES, IMAGE_SIZE


PALETTE = np.asarray(
    [
        (20, 20, 20),
        (110, 110, 110),
        (240, 170, 40),
        (75, 155, 220),
        (90, 190, 110),
        (180, 100, 180),
        (235, 210, 90),
        (80, 190, 190),
        (160, 120, 80),
        (140, 170, 90),
        (190, 190, 190),
        (220, 80, 80),
        (70, 120, 230),
    ],
    dtype=np.uint8,
)


def _checkpoint_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as checkpoint:
        for chunk in iter(lambda: checkpoint.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_overlay(
    image: Image.Image,
    target: np.ndarray,
    prediction: np.ndarray,
    output_path: Path,
) -> None:
    source = image.resize((IMAGE_SIZE, IMAGE_SIZE), Image.Resampling.LANCZOS).convert("RGB")
    target_color = Image.fromarray(PALETTE[target], mode="RGB")
    prediction_color = Image.fromarray(PALETTE[prediction], mode="RGB")
    target_overlay = Image.blend(source, target_color, 0.5)
    prediction_overlay = Image.blend(source, prediction_color, 0.5)

    header_height = 30
    canvas = Image.new("RGB", (IMAGE_SIZE * 3, IMAGE_SIZE + header_height), "white")
    draw = ImageDraw.Draw(canvas)
    for index, title in enumerate(("Original", "Ground truth overlay", "Prediction overlay")):
        left = index * IMAGE_SIZE
        draw.text((left + 8, 8), title, fill="black")
    canvas.paste(source, (0, header_height))
    canvas.paste(target_overlay, (IMAGE_SIZE, header_height))
    canvas.paste(prediction_overlay, (IMAGE_SIZE * 2, header_height))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)


def _write_failure_case_overlays(
    model: torch.nn.Module,
    records: list[dict],
    prepared_dir: Path,
    device: torch.device,
    failure_cases: list[dict],
    output_dir: Path,
) -> list[dict]:
    records_by_id = {record["id"]: record for record in records}
    dataset = CubiCasaSegmentationDataset(records, prepared_dir)
    dataset_index = {record["id"]: index for index, record in enumerate(records)}
    enriched: list[dict] = []
    model.eval()
    with torch.inference_mode():
        for rank, score in enumerate(failure_cases, start=1):
            record = records_by_id[score["id"]]
            image_tensor, target_tensor = dataset[dataset_index[score["id"]]]
            logits = model(image_tensor.unsqueeze(0).to(device))
            prediction = logits.argmax(dim=1)[0].cpu().numpy().astype(np.uint8)
            with Image.open(prepared_dir / record["image"]) as original:
                safe_id = re.sub(r"[^A-Za-z0-9_.-]+", "_", score["id"])
                overlay_path = output_dir / f"failure_case_{rank:02d}_{safe_id}.png"
                _write_overlay(
                    original,
                    target_tensor.numpy().astype(np.uint8),
                    prediction,
                    overlay_path,
                )
            enriched.append(
                {
                    **score,
                    "overlay": str(overlay_path),
                }
            )
    return enriched


def evaluate(
    prepared_dir: Path,
    split_dir: Path,
    checkpoint_path: Path,
    output_path: Path,
    batch_size: int = 4,
    overlay_count: int = 8,
) -> dict:
    if batch_size < 1 or overlay_count < 0:
        raise ValueError("batch_size must be positive and overlay_count cannot be negative")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    test_records = read_jsonl(split_dir / "test.jsonl")
    model, checkpoint = load_model(checkpoint_path, device)
    metrics = evaluate_model(
        model,
        test_records,
        prepared_dir,
        device,
        batch_size,
        include_confusion_matrix=True,
        include_sample_metrics=overlay_count > 0,
    )
    sample_metrics = metrics.pop("sample_metrics", [])
    result = {
        "dataset": "CubiCasa5K",
        "split": "test",
        "sample_count": len(test_records),
        "checkpoint": str(checkpoint_path),
        "checkpoint_sha256": _checkpoint_sha256(checkpoint_path),
        "checkpoint_best_epoch": checkpoint.get("best_epoch"),
        "architecture": checkpoint.get("architecture"),
        "class_names": list(CLASS_NAMES),
        "device": str(device),
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        **metrics,
    }
    if overlay_count:
        selected_failures = sorted(sample_metrics, key=lambda item: item["mean_iou"])[:overlay_count]
        result["failure_cases"] = _write_failure_case_overlays(
            model,
            test_records,
            prepared_dir,
            device,
            selected_failures,
            output_path.parent / "qualitative",
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(f"{output_path.suffix}.tmp")
    temporary_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    temporary_path.replace(output_path)
    print(json.dumps(result, indent=2))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a trained model on the held-out CubiCasa5K test split.")
    parser.add_argument("--prepared-dir", type=Path, default=PROJECT_ROOT / "data/processed/cubicasa")
    parser.add_argument("--split-dir", type=Path, default=PROJECT_ROOT / "data/processed/cubicasa/splits")
    parser.add_argument("--checkpoint", type=Path, default=PROJECT_ROOT / "backend/models/floorplan_unet.pt")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "data/processed/cubicasa/test_metrics.json")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument(
        "--overlay-count",
        type=int,
        default=8,
        help="Write overlays for the lowest per-plan test mIoU cases; use 0 to disable.",
    )
    args = parser.parse_args()
    evaluate(
        args.prepared_dir,
        args.split_dir,
        args.checkpoint,
        args.output,
        args.batch_size,
        args.overlay_count,
    )


if __name__ == "__main__":
    main()
