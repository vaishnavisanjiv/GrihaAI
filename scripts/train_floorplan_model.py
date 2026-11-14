import argparse
import json
import math
import os
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch import nn

from floorplan_training import (
    PROJECT_ROOT,
    evaluate_model,
    limit_records,
    loaders,
    read_jsonl,
    set_seed,
)
from app.services.floorplan_model import CLASS_NAMES, IMAGE_SIZE, FloorPlanUNet


def write_progress(progress_path: Path, progress: dict[str, object]) -> None:
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = progress_path.with_suffix(f"{progress_path.suffix}.tmp")
    temporary_path.write_text(json.dumps(progress, indent=2), encoding="utf-8")
    os.replace(temporary_path, progress_path)


def write_json(path: Path, value: object) -> None:
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    temporary_path.write_text(json.dumps(value, indent=2), encoding="utf-8")
    os.replace(temporary_path, path)


def class_weights(records: list[dict], prepared_dir: Path, device: torch.device) -> torch.Tensor:
    counts = torch.zeros(len(CLASS_NAMES), dtype=torch.float64)
    for record in records:
        with Image.open(prepared_dir / record["mask"]) as image:
            labels = torch.from_numpy(np.asarray(image.convert("L"), dtype=np.int64))
        counts += torch.bincount(labels.reshape(-1), minlength=len(CLASS_NAMES))
    frequencies = counts / counts.sum().clamp_min(1)
    weights = torch.where(frequencies > 0, frequencies.clamp_min(1e-6).rsqrt(), 0)
    weights = weights / weights[weights > 0].mean().clamp_min(1e-6)
    return weights.clamp(max=5).float().to(device)


def train(
    prepared_dir: Path,
    split_dir: Path,
    checkpoint_path: Path,
    epochs: int = 30,
    batch_size: int = 8,
    learning_rate: float = 1e-3,
    seed: int = 42,
    max_train_samples: int | None = None,
    max_val_samples: int | None = None,
    early_stopping_patience: int = 6,
    min_delta: float = 1e-4,
    gradient_clip_norm: float = 1.0,
    num_workers: int | None = None,
    resume: bool = False,
) -> dict:
    if epochs < 1 or batch_size < 1 or learning_rate <= 0 or early_stopping_patience < 1:
        raise ValueError("epochs, batch_size, learning_rate, and patience must be positive")
    if min_delta < 0 or gradient_clip_norm <= 0:
        raise ValueError("min_delta must be non-negative and gradient_clip_norm must be positive")

    set_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("=" * 60)
    print("Training Device:", device)
    if device.type == "cuda":
        print("GPU Name:", torch.cuda.get_device_name(0))
        print("Total VRAM:", f"{torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB")
        torch.backends.cudnn.benchmark = True
    print("=" * 60)

    use_amp = device.type == "cuda"
    if num_workers is None:
        num_workers = 2 if device.type == "cuda" else 0

    train_loader, val_loader = loaders(
        prepared_dir,
        split_dir,
        batch_size,
        max_train_samples=max_train_samples,
        max_val_samples=max_val_samples,
        seed=seed,
        num_workers=num_workers,
    )
    train_records = limit_records(read_jsonl(split_dir / "train.jsonl"), max_train_samples, seed)

    model = FloorPlanUNet(num_classes=len(CLASS_NAMES)).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="max", factor=0.5, patience=2, min_lr=1e-6
    )
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)
    criterion = nn.CrossEntropyLoss(weight=class_weights(train_records, prepared_dir, device))

    best_val_iou = -math.inf
    best_epoch = 0
    epochs_without_improvement = 0
    start_epoch = 1
    history: list[dict] = []

    checkpoint_dir = checkpoint_path.parent
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    latest_checkpoint_path = checkpoint_dir / "latest_checkpoint.pt"
    history_path = checkpoint_path.with_suffix(".history.json")
    progress_path = checkpoint_path.with_suffix(".progress.json")

    # Resume support
    if resume and latest_checkpoint_path.is_file():
        print(f"Loading resume checkpoint from {latest_checkpoint_path}...")
        checkpoint_data = torch.load(latest_checkpoint_path, map_location=device, weights_only=False)
        model.load_state_dict(checkpoint_data["state_dict"])
        if "optimizer_state_dict" in checkpoint_data:
            optimizer.load_state_dict(checkpoint_data["optimizer_state_dict"])
        if "scheduler_state_dict" in checkpoint_data:
            scheduler.load_state_dict(checkpoint_data["scheduler_state_dict"])
        if "scaler_state_dict" in checkpoint_data and use_amp:
            scaler.load_state_dict(checkpoint_data["scaler_state_dict"])
        start_epoch = checkpoint_data.get("epoch", 0) + 1
        best_val_iou = checkpoint_data.get("best_val_iou", -math.inf)
        best_epoch = checkpoint_data.get("best_epoch", 0)
        epochs_without_improvement = checkpoint_data.get("epochs_without_improvement", 0)
        history = checkpoint_data.get("history", [])
        print(f"Resumed successfully at epoch {start_epoch}. Current best val mIoU: {best_val_iou:.4f} (epoch {best_epoch})")

    total_batches = len(train_loader)
    bar_width = 30
    write_progress(
        progress_path,
        {
            "status": "running",
            "epoch": start_epoch - 1,
            "total_epochs": epochs,
            "batch": 0,
            "total_batches": total_batches,
            "percent": round((start_epoch - 1) * 100 / epochs, 2),
            "device": str(device),
        },
    )

    for epoch in range(start_epoch, epochs + 1):
        model.train()
        total_loss = 0.0
        for batch_number, (images, masks) in enumerate(train_loader, start=1):
            images = images.to(device)
            masks = masks.to(device)
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(
                device_type=device.type,
                dtype=torch.float16 if use_amp else torch.bfloat16,
                enabled=use_amp,
            ):
                loss = criterion(model(images), masks)
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), gradient_clip_norm)
            scaler.step(optimizer)
            scaler.update()
            total_loss += loss.item() * images.size(0)

            percent = batch_number * 100 / total_batches
            filled = int(bar_width * batch_number / total_batches)
            progress = (
                f"\rEpoch {epoch}/{epochs} "
                f"[{'#' * filled}{'-' * (bar_width - filled)}] "
                f"{batch_number}/{total_batches} ({percent:5.1f}%) "
                f"loss={loss.item():.4f}"
            )
            print(progress, end="", flush=True)

            if batch_number % 25 == 0 or batch_number == total_batches:
                write_progress(
                    progress_path,
                    {
                        "status": "running",
                        "epoch": epoch,
                        "total_epochs": epochs,
                        "batch": batch_number,
                        "total_batches": total_batches,
                        "percent": round(percent, 2),
                        "batch_loss": float(loss.item()),
                        "samples_seen": min(batch_number * batch_size, len(train_loader.dataset)),
                        "train_samples": len(train_loader.dataset),
                        "device": str(device),
                    },
                )

        print(flush=True)
        # Validation
        validation = evaluate_model(model, val_loader.dataset.records, prepared_dir, device, batch_size)
        scheduler.step(validation["mean_iou"])
        epoch_loss = total_loss / len(train_loader.dataset)
        current_learning_rate = float(optimizer.param_groups[0]["lr"])
        history.append({
            "epoch": epoch,
            "train_loss": epoch_loss,
            "validation_mean_iou": validation["mean_iou"],
            "learning_rate": current_learning_rate,
        })
        print(
            f"--> Epoch {epoch}/{epochs}: train_loss={epoch_loss:.4f} "
            f"val_mIoU={validation['mean_iou']:.4f} "
            f"pixel_acc={validation['pixel_accuracy']:.4f} "
            f"lr={current_learning_rate:.2e}"
        )
        write_json(history_path, history)

        # 1. Save latest checkpoint for resume safety (every epoch)
        torch.save(
            {
                "epoch": epoch,
                "state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "scheduler_state_dict": scheduler.state_dict(),
                "scaler_state_dict": scaler.state_dict(),
                "best_val_iou": best_val_iou,
                "best_epoch": best_epoch,
                "epochs_without_improvement": epochs_without_improvement,
                "history": history,
            },
            latest_checkpoint_path,
        )

        # 2. If val mIoU improved, save best model in official backend format
        if validation["mean_iou"] > best_val_iou + min_delta:
            best_val_iou = validation["mean_iou"]
            best_epoch = epoch
            epochs_without_improvement = 0
            best_payload = {
                "state_dict": model.state_dict(),
                "class_names": list(CLASS_NAMES),
                "image_size": IMAGE_SIZE,
                "architecture": "buildguard-unet-v1",
                "best_epoch": best_epoch,
                "validation_mean_iou": best_val_iou,
                "seed": seed,
                "training_config": {
                    "epochs_requested": epochs,
                    "batch_size": batch_size,
                    "learning_rate": learning_rate,
                    "early_stopping_patience": early_stopping_patience,
                    "min_delta": min_delta,
                    "gradient_clip_norm": gradient_clip_norm,
                    "mixed_precision": use_amp,
                    "optimizer": "AdamW",
                    "scheduler": "ReduceLROnPlateau",
                },
            }
            # Save to main target checkpoint
            temporary_checkpoint = checkpoint_path.with_suffix(f"{checkpoint_path.suffix}.tmp")
            torch.save(best_payload, temporary_checkpoint)
            os.replace(temporary_checkpoint, checkpoint_path)
            # Also save companion copy named floorplan_unet_best.pt
            best_alt_path = checkpoint_dir / "floorplan_unet_best.pt"
            torch.save(best_payload, best_alt_path)
            print(f"*** New best validation mIoU: {best_val_iou:.4f}! Saved checkpoint to {checkpoint_path} ***")
        else:
            epochs_without_improvement += 1
            print(f"No improvement for {epochs_without_improvement}/{early_stopping_patience} epochs.")
            if epochs_without_improvement >= early_stopping_patience:
                print(
                    f"Early stopping triggered at epoch {epoch}: "
                    f"validation mIoU did not improve for {early_stopping_patience} consecutive epochs."
                )
                break

    result = {
        "checkpoint": str(checkpoint_path),
        "history": str(history_path),
        "best_epoch": best_epoch,
        "best_validation_mean_iou": best_val_iou,
        "device": str(device),
        "mixed_precision": use_amp,
        "epochs_completed": len(history),
        "train_samples": len(train_loader.dataset),
        "validation_samples": len(val_loader.dataset),
    }
    print(json.dumps(result, indent=2))
    write_progress(
        progress_path,
        {
            "status": "completed",
            "epoch": len(history),
            "total_epochs": epochs,
            "batch": total_batches,
            "total_batches": total_batches,
            "percent": round(len(history) * 100 / epochs, 2),
            "best_epoch": best_epoch,
            "best_validation_mean_iou": best_val_iou,
            "device": str(device),
            "early_stopped": len(history) < epochs,
        },
    )
    return result


def main() -> None:
    output_dir_env = os.environ.get("MODEL_OUTPUT_DIR")
    default_checkpoint = (
        Path(output_dir_env) / "floorplan_unet_gpu_candidate.pt"
        if output_dir_env
        else PROJECT_ROOT / "backend/models/floorplan_unet_gpu_candidate.pt"
    )

    parser = argparse.ArgumentParser(description="Train a floor-plan segmentation model on CubiCasa5K.")
    parser.add_argument("--prepared-dir", type=Path, default=PROJECT_ROOT / "data/processed/cubicasa")
    parser.add_argument("--split-dir", type=Path, default=PROJECT_ROOT / "data/processed/cubicasa/splits")
    parser.add_argument("--checkpoint", type=Path, default=default_checkpoint)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--early-stopping-patience", type=int, default=4)
    parser.add_argument("--min-delta", type=float, default=1e-4)
    parser.add_argument("--gradient-clip-norm", type=float, default=1.0)
    parser.add_argument("--num-workers", type=int, default=None)
    parser.add_argument("--resume", action="store_true", help="Resume training from latest_checkpoint.pt")
    parser.add_argument(
        "--max-train-samples",
        type=int,
        help="Randomly limit training samples; omit to use the full training split.",
    )
    parser.add_argument(
        "--max-val-samples",
        type=int,
        help="Randomly limit validation samples; omit to use the full validation split.",
    )
    args = parser.parse_args()
    train(
        args.prepared_dir,
        args.split_dir,
        args.checkpoint,
        args.epochs,
        args.batch_size,
        args.learning_rate,
        args.seed,
        args.max_train_samples,
        args.max_val_samples,
        args.early_stopping_patience,
        args.min_delta,
        args.gradient_clip_norm,
        args.num_workers,
        args.resume,
    )


if __name__ == "__main__":
    main()
