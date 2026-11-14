import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
NUM_CLASSES = 13


def validate_data(prepared_dir: Path, split_dir: Path | None = None) -> bool:
    manifest_path = prepared_dir / "manifest.jsonl"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Prepared manifest does not exist: {manifest_path}")
    records = [
        json.loads(line)
        for line in manifest_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not records:
        raise ValueError("Prepared manifest has no samples")
    sample_ids = [record["id"] for record in records]
    if len(sample_ids) != len(set(sample_ids)):
        raise ValueError("Prepared manifest contains duplicate sample IDs")
    sources = [record.get("source") for record in records if record.get("source")]
    if len(sources) != len(set(sources)):
        raise ValueError("Prepared manifest contains duplicate source plans")

    prepared_root = prepared_dir.resolve()

    for record in records:
        image_path = (prepared_dir / record["image"]).resolve()
        mask_path = (prepared_dir / record["mask"]).resolve()
        if prepared_root not in image_path.parents or prepared_root not in mask_path.parents:
            raise ValueError(f"Sample {record['id']} has an image or mask path outside the prepared dataset")
        if not image_path.is_file() or not mask_path.is_file():
            raise FileNotFoundError(f"Missing image or mask for sample {record['id']}")
        with Image.open(image_path) as image, Image.open(mask_path) as mask:
            if image.size != mask.size:
                raise ValueError(f"Image/mask size mismatch for sample {record['id']}")
            labels = np.asarray(mask.convert("L"))
            if labels.size == 0 or labels.min() < 0 or labels.max() >= NUM_CLASSES:
                raise ValueError(f"Invalid semantic class values for sample {record['id']}")
            if len(np.unique(labels)) < 2:
                raise ValueError(f"Sample {record['id']} contains only one label; inspect its SVG rasterization")

    if split_dir is not None:
        split_ids: dict[str, set[str]] = {}
        records_by_id = {record["id"]: record for record in records}
        for split in ("train", "val", "test"):
            path = split_dir / f"{split}.jsonl"
            if not path.is_file():
                raise FileNotFoundError(f"Missing {split} split: {path}")
            split_records = [
                json.loads(line)
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            split_record_ids = [record["id"] for record in split_records]
            if len(split_record_ids) != len(set(split_record_ids)):
                raise ValueError(f"{split} split contains duplicate sample IDs")
            split_ids[split] = set(split_record_ids)
            if not split_ids[split]:
                raise ValueError(f"{split} split is empty")
            for split_record in split_records:
                manifest_record = records_by_id.get(split_record["id"])
                if manifest_record is None:
                    raise ValueError(f"{split} split references unknown sample {split_record['id']}")
                for key in ("image", "mask", "source"):
                    if key in manifest_record and split_record.get(key) != manifest_record[key]:
                        raise ValueError(
                            f"{split} split sample {split_record['id']} does not match manifest field {key}"
                        )
        if (
            split_ids["train"] & split_ids["val"]
            or split_ids["train"] & split_ids["test"]
            or split_ids["val"] & split_ids["test"]
        ):
            raise ValueError("Train/validation/test splits overlap")
        if set.union(*split_ids.values()) != set(sample_ids):
            raise ValueError("Split files do not account for every prepared sample exactly")

    print(f"Validated {len(records)} annotated floor plans in {prepared_dir}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate prepared CubiCasa5K masks and dataset splits.")
    parser.add_argument("--prepared-dir", type=Path, default=PROJECT_ROOT / "data/processed/cubicasa")
    parser.add_argument("--split-dir", type=Path, default=PROJECT_ROOT / "data/processed/cubicasa/splits")
    args = parser.parse_args()
    validate_data(args.prepared_dir, args.split_dir)


if __name__ == "__main__":
    main()
