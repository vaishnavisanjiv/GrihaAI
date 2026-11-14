from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
import sys

sys.path.insert(0, str(BACKEND_ROOT))
from app.services.floorplan_model import CLASS_NAMES, IMAGE_SIZE, FloorPlanUNet, load_checkpoint


class CubiCasaSegmentationDataset(Dataset[tuple[torch.Tensor, torch.Tensor]]):
    def __init__(self, records: list[dict[str, Any]], prepared_dir: Path, augment: bool = False) -> None:
        self.records = records
        self.prepared_dir = prepared_dir
        self.augment = augment

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        record = self.records[index]
        with Image.open(self.prepared_dir / record["image"]) as image:
            image_array = np.asarray(
                image.convert("RGB").resize((IMAGE_SIZE, IMAGE_SIZE), Image.Resampling.LANCZOS),
                dtype=np.float32,
            ) / 255.0
        with Image.open(self.prepared_dir / record["mask"]) as mask:
            mask_array = np.asarray(
                mask.convert("L").resize((IMAGE_SIZE, IMAGE_SIZE), Image.Resampling.NEAREST),
                dtype=np.int64,
            )
        if self.augment and random.random() < 0.5:
            turns = random.randint(1, 3)
            image_array = np.rot90(image_array, turns, axes=(0, 1)).copy()
            mask_array = np.rot90(mask_array, turns, axes=(0, 1)).copy()
        if self.augment and random.random() < 0.5:
            image_array = np.fliplr(image_array).copy()
            mask_array = np.fliplr(mask_array).copy()
        if self.augment and random.random() < 0.5:
            image_array = np.flipud(image_array).copy()
            mask_array = np.flipud(mask_array).copy()
        if self.augment:
            contrast = random.uniform(0.9, 1.1)
            brightness = random.uniform(-0.05, 0.05)
            image_array = np.clip(image_array * contrast + brightness, 0, 1)
        image_tensor = torch.from_numpy(image_array.transpose(2, 0, 1))
        mask_tensor = torch.from_numpy(mask_array)
        return image_tensor, mask_tensor


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"Split file not found: {path}")
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not records:
        raise ValueError(f"No samples found in {path}")
    return records


def limit_records(
    records: list[dict[str, Any]], max_samples: int | None, seed: int
) -> list[dict[str, Any]]:
    if max_samples is None or max_samples >= len(records):
        return records
    if max_samples < 1:
        raise ValueError("sample limits must be positive")
    return random.Random(seed).sample(records, max_samples)


def loaders(
    prepared_dir: Path,
    split_dir: Path,
    batch_size: int,
    max_train_samples: int | None = None,
    max_val_samples: int | None = None,
    seed: int = 42,
    num_workers: int = 0,
) -> tuple[DataLoader, DataLoader]:
    train_records = read_jsonl(split_dir / "train.jsonl")
    val_records = read_jsonl(split_dir / "val.jsonl")
    train_ids = {record["id"] for record in train_records}
    val_ids = {record["id"] for record in val_records}
    if len(train_ids) != len(train_records) or len(val_ids) != len(val_records):
        raise ValueError("Train or validation split contains duplicate sample IDs")
    if train_ids & val_ids:
        raise ValueError("Train and validation files overlap; refusing data leakage")
    train_records = limit_records(train_records, max_train_samples, seed)
    val_records = limit_records(val_records, max_val_samples, seed + 1)
    is_cuda = torch.cuda.is_available()
    train_loader = DataLoader(
        CubiCasaSegmentationDataset(train_records, prepared_dir, augment=True),
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=is_cuda,
        persistent_workers=(num_workers > 0),
    )
    val_loader = DataLoader(
        CubiCasaSegmentationDataset(val_records, prepared_dir),
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=is_cuda,
        persistent_workers=(num_workers > 0),
    )
    return train_loader, val_loader


def confusion_matrix(
    predictions: torch.Tensor, targets: torch.Tensor, num_classes: int = len(CLASS_NAMES)
) -> np.ndarray:
    predicted = predictions.reshape(-1).to(torch.int64)
    expected = targets.reshape(-1).to(torch.int64)
    valid = (expected >= 0) & (expected < num_classes)
    counts = torch.bincount(
        num_classes * expected[valid] + predicted[valid], minlength=num_classes * num_classes
    )
    return counts.reshape(num_classes, num_classes).cpu().numpy()


def scores_from_confusion(matrix: np.ndarray) -> dict[str, Any]:
    if matrix.shape != (len(CLASS_NAMES), len(CLASS_NAMES)):
        raise ValueError(f"Confusion matrix must have shape {(len(CLASS_NAMES), len(CLASS_NAMES))}")
    if np.any(matrix < 0):
        raise ValueError("Confusion matrix counts cannot be negative")

    true_positive = np.diag(matrix).astype(np.float64)
    predicted_count = matrix.sum(axis=0).astype(np.float64)
    target_count = matrix.sum(axis=1).astype(np.float64)
    union = predicted_count + target_count - true_positive
    valid_iou = union > 0
    valid_precision = predicted_count > 0
    valid_recall = target_count > 0
    precision = np.divide(
        true_positive, predicted_count, out=np.zeros_like(true_positive), where=valid_precision
    )
    recall = np.divide(
        true_positive, target_count, out=np.zeros_like(true_positive), where=valid_recall
    )
    dice_denominator = predicted_count + target_count
    dice = np.divide(
        2 * true_positive,
        dice_denominator,
        out=np.zeros_like(true_positive),
        where=dice_denominator > 0,
    )
    f1 = dice.copy()
    class_iou = {
        CLASS_NAMES[index]: float(true_positive[index] / union[index]) if valid_iou[index] else None
        for index in range(len(CLASS_NAMES))
    }
    class_metrics = {
        CLASS_NAMES[index]: {
            "precision": float(precision[index]) if valid_precision[index] else None,
            "recall": float(recall[index]) if valid_recall[index] else None,
            "f1": float(f1[index]) if valid_iou[index] else None,
            "dice": float(dice[index]) if valid_iou[index] else None,
        }
        for index in range(len(CLASS_NAMES))
    }
    total = int(matrix.sum())
    result = {
        "mean_iou": float(np.mean(true_positive[valid_iou] / union[valid_iou])) if np.any(valid_iou) else 0.0,
        "pixel_accuracy": float(true_positive.sum() / total) if total else 0.0,
        "macro_precision": float(np.mean(precision[valid_precision])) if np.any(valid_precision) else 0.0,
        "macro_recall": float(np.mean(recall[valid_recall])) if np.any(valid_recall) else 0.0,
        "macro_f1": float(np.mean(f1[valid_iou])) if np.any(valid_iou) else 0.0,
        "macro_dice": float(np.mean(dice[valid_iou])) if np.any(valid_iou) else 0.0,
        "class_iou": class_iou,
        "class_metrics": class_metrics,
        "evaluated_classes": int(valid_iou.sum()),
        "pixels": total,
    }
    return result


def evaluate_model(
    model: FloorPlanUNet, records: list[dict[str, Any]], prepared_dir: Path,
    device: torch.device, batch_size: int, include_confusion_matrix: bool = False,
    include_sample_metrics: bool = False,
) -> dict[str, Any]:
    loader = DataLoader(
        CubiCasaSegmentationDataset(records, prepared_dir),
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=device.type == "cuda",
    )
    matrix = np.zeros((len(CLASS_NAMES), len(CLASS_NAMES)), dtype=np.int64)
    sample_metrics: list[dict[str, Any]] = []
    model.eval()
    with torch.inference_mode():
        for images, masks in loader:
            logits = model(images.to(device))
            predicted = logits.argmax(dim=1).cpu()
            matrix += confusion_matrix(predicted, masks)
            if include_sample_metrics:
                for index, record in enumerate(loader.dataset.records[
                    len(sample_metrics):len(sample_metrics) + len(images)
                ]):
                    sample_matrix = confusion_matrix(predicted[index], masks[index])
                    sample_score = scores_from_confusion(sample_matrix)
                    sample_metrics.append(
                        {
                            "id": record["id"],
                            "mean_iou": sample_score["mean_iou"],
                            "pixel_accuracy": sample_score["pixel_accuracy"],
                        }
                    )
    metrics = scores_from_confusion(matrix)
    if include_confusion_matrix:
        metrics["confusion_matrix"] = matrix.tolist()
    if include_sample_metrics:
        metrics["sample_metrics"] = sample_metrics
    return metrics


def load_model(path: Path, device: torch.device) -> tuple[FloorPlanUNet, dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"Trained model checkpoint not found: {path}")
    return load_checkpoint(path, device)


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
