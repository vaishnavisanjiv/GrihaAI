import argparse
import json
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def split_data(
    manifest_path: Path,
    output_dir: Path,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    seed: int = 42,
) -> dict[str, int]:
    if not 0 < train_ratio < 1 or not 0 < val_ratio < 1 or train_ratio + val_ratio >= 1:
        raise ValueError("train_ratio and val_ratio must be positive and sum to less than 1")
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Prepared sample manifest not found: {manifest_path}")
    records = [
        json.loads(line)
        for line in manifest_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(records) < 3:
        raise ValueError("At least three annotated plans are required for train/validation/test splits")
    ids = [record["id"] for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError("Manifest has duplicate sample IDs; refusing a potentially leaking split")

    random.Random(seed).shuffle(records)
    train_end = max(1, int(len(records) * train_ratio))
    val_end = max(train_end + 1, int(len(records) * (train_ratio + val_ratio)))
    val_end = min(val_end, len(records) - 1)
    splits = {
        "train": records[:train_end],
        "val": records[train_end:val_end],
        "test": records[val_end:],
    }
    if not all(splits.values()):
        raise ValueError("Split ratios produced an empty train, validation, or test split")
    output_dir.mkdir(parents=True, exist_ok=True)
    for split_name, split_records in splits.items():
        path = output_dir / f"{split_name}.jsonl"
        with path.open("w", encoding="utf-8") as split_file:
            for record in split_records:
                split_file.write(json.dumps(record) + "\n")

    split_ids = [{record["id"] for record in split_records} for split_records in splits.values()]
    if any(split_ids[i] & split_ids[j] for i in range(3) for j in range(i + 1, 3)):
        raise RuntimeError("Data leakage detected: a sample occurs in more than one split")
    return {name: len(values) for name, values in splits.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description="Create deterministic train/validation/test plan splits.")
    parser.add_argument("--manifest", type=Path, default=PROJECT_ROOT / "data/processed/cubicasa/manifest.jsonl")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "data/processed/cubicasa/splits")
    parser.add_argument("--train-ratio", type=float, default=0.7)
    parser.add_argument("--val-ratio", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    counts = split_data(args.manifest, args.output_dir, args.train_ratio, args.val_ratio, args.seed)
    print(f"Split {sum(counts.values())} plans: {counts}")


if __name__ == "__main__":
    main()
