from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from prepare_cubicasa import CLASS_NAMES, PROJECT_ROOT
from validate_dataset import validate_data


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _new_distribution() -> dict[str, Any]:
    return {
        "sample_count": 0,
        "class_pixels": Counter(),
        "samples_with_class": Counter(),
        "image_dimensions": Counter(),
        "mask_dimensions": Counter(),
    }


def _finalize_distribution(distribution: dict[str, Any]) -> dict[str, Any]:
    pixel_counts: Counter = distribution["class_pixels"]
    present_counts: Counter = distribution["samples_with_class"]
    total_pixels = sum(pixel_counts.values())
    class_distribution = {
        name: {
            "pixel_count": int(pixel_counts.get(index, 0)),
            "pixel_fraction": (
                float(pixel_counts.get(index, 0) / total_pixels) if total_pixels else 0.0
            ),
            "samples_present": int(present_counts.get(index, 0)),
        }
        for index, name in enumerate(CLASS_NAMES)
    }
    return {
        "sample_count": distribution["sample_count"],
        "pixel_count": total_pixels,
        "class_distribution": class_distribution,
        "prepared_image_dimensions": dict(sorted(distribution["image_dimensions"].items())),
        "prepared_mask_dimensions": dict(sorted(distribution["mask_dimensions"].items())),
    }


def build_dataset_statistics(prepared_dir: Path, split_dir: Path) -> dict[str, Any]:
    split_paths = {name: split_dir / f"{name}.jsonl" for name in ("train", "val", "test")}
    existing_splits = [path.is_file() for path in split_paths.values()]
    if any(existing_splits) and not all(existing_splits):
        raise ValueError("Dataset splits are incomplete; expected train.jsonl, val.jsonl, and test.jsonl")
    available_splits = all(existing_splits)
    validate_data(prepared_dir, split_dir if available_splits else None)

    records = _read_jsonl(prepared_dir / "manifest.jsonl")
    preparation_report_path = prepared_dir / "preparation_report.json"
    if preparation_report_path.is_file():
        preparation_report = json.loads(preparation_report_path.read_text(encoding="utf-8"))
        if preparation_report.get("prepared_count") != len(records):
            raise ValueError(
                "Preparation report and manifest disagree; rerun preparation before generating statistics"
            )
    split_membership: dict[str, set[str]] = {
        name: {record["id"] for record in _read_jsonl(path)}
        for name, path in split_paths.items()
    } if available_splits else {}
    distributions = {"all": _new_distribution()}
    distributions.update({name: _new_distribution() for name in split_membership})
    source_dimensions: Counter[str] = Counter()
    source_dimensions_missing = 0

    for record in records:
        image_path = prepared_dir / record["image"]
        mask_path = prepared_dir / record["mask"]
        with Image.open(image_path) as image:
            image_dimensions = f"{image.width}x{image.height}"
        with Image.open(mask_path) as mask:
            mask_array = np.asarray(mask.convert("L"), dtype=np.uint8)
            mask_dimensions = f"{mask.width}x{mask.height}"

        pixel_counts = np.bincount(mask_array.reshape(-1), minlength=len(CLASS_NAMES))
        sample_classes = np.unique(mask_array)
        target_distributions = [distributions["all"]]
        target_distributions.extend(
            distributions[name]
            for name, ids in split_membership.items()
            if record["id"] in ids
        )
        for distribution in target_distributions:
            distribution["sample_count"] += 1
            distribution["class_pixels"].update(
                {index: int(count) for index, count in enumerate(pixel_counts) if count}
            )
            distribution["samples_with_class"].update(int(class_id) for class_id in sample_classes)
            distribution["image_dimensions"][image_dimensions] += 1
            distribution["mask_dimensions"][mask_dimensions] += 1

        dimensions = record.get("source_dimensions")
        if dimensions and dimensions.get("width") and dimensions.get("height"):
            source_dimensions[f"{dimensions['width']}x{dimensions['height']}"] += 1
        else:
            source_dimensions_missing += 1

    if preparation_report_path.is_file():
        skipped_annotations = preparation_report.get("skipped", [])
    else:
        legacy_errors_path = prepared_dir / "prepare_errors.txt"
        skipped_annotations = (
            [
                {"reason": line}
                for line in legacy_errors_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            if legacy_errors_path.is_file()
            else []
        )

    return {
        "dataset": "CubiCasa5K",
        "class_names": list(CLASS_NAMES),
        "sample_count": len(records),
        "annotation_exclusions": {
            "count": len(skipped_annotations),
            "records": skipped_annotations,
        },
        "source_image_dimensions": {
            "counts": dict(sorted(source_dimensions.items())),
            "samples_without_recorded_dimensions": source_dimensions_missing,
        },
        "all_samples": _finalize_distribution(distributions["all"]),
        "splits": {
            name: _finalize_distribution(distribution)
            for name, distribution in distributions.items()
            if name != "all"
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate CubiCasa5K data and write class/dimension statistics."
    )
    parser.add_argument(
        "--prepared-dir",
        type=Path,
        default=PROJECT_ROOT / "data/processed/cubicasa",
    )
    parser.add_argument(
        "--split-dir",
        type=Path,
        default=PROJECT_ROOT / "data/processed/cubicasa/splits",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output JSON path (default: <prepared-dir>/dataset_statistics.json).",
    )
    args = parser.parse_args()
    report = build_dataset_statistics(args.prepared_dir, args.split_dir)
    output_path = args.output or args.prepared_dir / "dataset_statistics.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(f"{output_path.suffix}.tmp")
    temporary_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    temporary_path.replace(output_path)
    print(f"Wrote statistics for {report['sample_count']} plans to {output_path}")


if __name__ == "__main__":
    main()
