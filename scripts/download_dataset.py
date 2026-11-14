import argparse
import hashlib
import urllib.request
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_URL = "https://zenodo.org/api/records/2613548/files/cubicasa5k.zip/content"
EXPECTED_MD5 = "0ce0b203d1e3c125b51087b219bd23b9"


def _md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as archive:
        while chunk := archive.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def verify_archive(archive_path: Path) -> Path:
    if not archive_path.is_file():
        raise FileNotFoundError(f"Dataset archive not found: {archive_path}")
    if _md5(archive_path) != EXPECTED_MD5:
        raise ValueError(
            f"Dataset archive checksum did not match Zenodo: {archive_path}. "
            "The archive was left untouched; finish or replace the download before retrying."
        )
    return archive_path


def download_dataset(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = output_dir / "cubicasa5k.zip"
    if archive_path.exists():
        return verify_archive(archive_path)

    partial_path = archive_path.with_suffix(f"{archive_path.suffix}.part")
    partial_path.unlink(missing_ok=True)
    request = urllib.request.Request(DATASET_URL, headers={"User-Agent": "BuildGuardAI-dataset-setup/1.0"})
    digest = hashlib.md5()
    try:
        with urllib.request.urlopen(request, timeout=60) as response, partial_path.open("wb") as archive:
            total_size = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            while chunk := response.read(1024 * 1024):
                archive.write(chunk)
                digest.update(chunk)
                downloaded += len(chunk)
                if downloaded // (100 * 1024 * 1024) != (downloaded - len(chunk)) // (100 * 1024 * 1024):
                    if total_size:
                        print(f"Downloaded {downloaded / total_size:.0%} ({downloaded / (1024**3):.2f} GiB)")
                    else:
                        print(f"Downloaded {downloaded / (1024**3):.2f} GiB")
    except Exception:
        partial_path.unlink(missing_ok=True)
        raise
    if digest.hexdigest() != EXPECTED_MD5:
        partial_path.unlink(missing_ok=True)
        raise ValueError("Downloaded archive checksum did not match Zenodo; incomplete download removed")
    partial_path.replace(archive_path)
    return archive_path


def extract_dataset(archive_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    root = output_dir.resolve()
    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            destination = (root / member.filename).resolve()
            if destination != root and root not in destination.parents:
                raise ValueError(f"Unsafe path in dataset archive: {member.filename}")
        archive.extractall(root)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download the official 5.47 GB CubiCasa5K archive.")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "data/raw")
    parser.add_argument("--download", action="store_true", help="Opt in to downloading the multi-GB dataset")
    parser.add_argument("--extract", action="store_true", help="Extract the verified archive in output-dir")
    args = parser.parse_args()
    if not args.download and not args.extract:
        print(f"Dataset source: {DATASET_URL}")
        print("Size: approximately 5.47 GB. License: CC BY-NC-SA 4.0 (non-commercial use).")
        print("Use --download to opt in, then --extract to extract the verified archive.")
        return
    archive_path = (
        download_dataset(args.output_dir)
        if args.download
        else verify_archive(args.output_dir / "cubicasa5k.zip")
    )
    print(f"Verified dataset archive: {archive_path}")
    if args.extract:
        extract_dataset(archive_path, args.output_dir / "cubicasa5k")
        print(f"Extracted dataset to {args.output_dir / 'cubicasa5k'}")


if __name__ == "__main__":
    main()
