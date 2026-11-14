"""
Helper script to package code and dataset for Google Colab GPU training.
Generates:
  1. colab_package/BuildGuardAI_training.zip (scripts and model definition)
  2. colab_package/CubiCasa5K_processed.zip (images, masks, splits)
"""
import os
import sys
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "colab_package"


def create_training_code_zip(output_zip: Path) -> None:
    print(f"Creating training code bundle: {output_zip}...")
    files_to_pack = [
        # Scripts
        ("scripts/train_floorplan_model.py", "scripts/train_floorplan_model.py"),
        ("scripts/floorplan_training.py", "scripts/floorplan_training.py"),
        ("scripts/evaluate_floorplan_model.py", "scripts/evaluate_floorplan_model.py"),
        # Backend modules required for imports
        ("backend/app/__init__.py", "backend/app/__init__.py"),
        ("backend/app/services/__init__.py", "backend/app/services/__init__.py"),
        ("backend/app/services/floorplan_model.py", "backend/app/services/floorplan_model.py"),
    ]

    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative_src, arcname in files_to_pack:
            full_src = PROJECT_ROOT / relative_src
            if full_src.is_file():
                archive.write(full_src, arcname)
                print(f"  + {arcname}")
            else:
                print(f"  ! Missing file: {full_src}")

    print(f"Code bundle created: {output_zip.stat().st_size / 1024:.1f} KB\n")


def create_dataset_zip(output_zip: Path) -> None:
    data_dir = PROJECT_ROOT / "data/processed/cubicasa"
    if not data_dir.is_dir():
        print(f"ERROR: Dataset directory not found at {data_dir}")
        return

    print(f"Creating dataset bundle: {output_zip} (this may take 1-2 minutes)...")
    count = 0
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        # Splits and manifest
        for f in ["splits/train.jsonl", "splits/val.jsonl", "splits/test.jsonl", "manifest.jsonl"]:
            src = data_dir / f
            if src.is_file():
                archive.write(src, arcname=f)
                count += 1

        # Images and masks
        for folder in ["images", "masks"]:
            folder_path = data_dir / folder
            if folder_path.is_dir():
                for item in folder_path.glob("*.png"):
                    archive.write(item, arcname=f"{folder}/{item.name}")
                    count += 1
                    if count % 1000 == 0:
                        print(f"  Packed {count} files...")

    size_mb = output_zip.stat().st_size / (1024 * 1024)
    print(f"Dataset bundle created: {count} files, {size_mb:.1f} MB\n")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    code_zip = OUTPUT_DIR / "BuildGuardAI_training.zip"
    dataset_zip = OUTPUT_DIR / "CubiCasa5K_processed.zip"

    create_training_code_zip(code_zip)

    if "--with-data" in sys.argv:
        create_dataset_zip(dataset_zip)
    else:
        print("Note: To also pack the dataset ZIP (~50-100 MB), run:")
        print("  python scripts/package_for_colab.py --with-data\n")

    print("Colab packaging finished successfully.")


if __name__ == "__main__":
    main()
