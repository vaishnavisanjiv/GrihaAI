import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parents[1]
IMAGE_SIZE = 512

# Compact semantic classes derived from CubiCasa5K's room and icon labels.
CLASS_NAMES = [
    "background",
    "wall",
    "kitchen",
    "living_dining",
    "bedroom",
    "bathroom",
    "entry",
    "railing",
    "storage",
    "garage",
    "other_room",
    "door",
    "window",
]
CLASS_ID = {name: index for index, name in enumerate(CLASS_NAMES)}
ROOM_CLASS_IDS = {
    "Alcove": 10, "Attic": 10, "Ballroom": 10, "Bar": 10, "Basement": 10,
    "Bath": 5, "Bedroom": 4, "Below150cm": 10, "CarPort": 9, "Church": 10,
    "Closet": 8, "ConferenceRoom": 10, "Conservatory": 10, "Counter": 10,
    "Den": 10, "Dining": 3, "DraughtLobby": 6, "DressingRoom": 8,
    "EatingArea": 3, "Elevated": 10, "Elevator": 10, "Entry": 6,
    "ExerciseRoom": 10, "Garage": 9, "Garbage": 10, "Hall": 6,
    "HallWay": 6, "HotTub": 10, "Kitchen": 2, "Library": 10, "LivingRoom": 3,
    "Loft": 10, "Lounge": 3, "MediaRoom": 10, "MeetingRoom": 10, "Museum": 10,
    "Nook": 10, "Office": 10, "OpenToBelow": 10, "Outdoor": 0, "Pantry": 8,
    "Reception": 10, "RecreationRoom": 10, "RetailSpace": 10, "Room": 10,
    "Sanctuary": 10, "Sauna": 5, "ServiceRoom": 10, "ServingArea": 10,
    "Skylights": 10, "Stable": 10, "Stage": 10, "StairWell": 10, "Storage": 8,
    "SunRoom": 10, "SwimmingPool": 10, "TechnicalRoom": 10, "Theatre": 10,
    "Undefined": 10, "UserDefined": 10, "Utility": 10, "Wall": 1, "Railing": 7,
}

NUMBER_PATTERN = re.compile(r"[-+]?(?:\d*\.)?\d+(?:[eE][-+]?\d+)?")
TRANSFORM_PATTERN = re.compile(r"([A-Za-z]+)\s*\(([^)]*)\)")
SVG_NS = "{http://www.w3.org/2000/svg}"


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _transform_matrix(transform: str) -> np.ndarray:
    result = np.eye(3, dtype=np.float64)
    for operation, arguments in TRANSFORM_PATTERN.findall(transform):
        values = [float(value) for value in NUMBER_PATTERN.findall(arguments)]
        matrix = np.eye(3, dtype=np.float64)
        if operation == "matrix" and len(values) == 6:
            a, b, c, d, e, f = values
            matrix = np.array([[a, c, e], [b, d, f], [0, 0, 1]], dtype=np.float64)
        elif operation == "translate" and values:
            matrix[0, 2] = values[0]
            matrix[1, 2] = values[1] if len(values) > 1 else 0
        elif operation == "scale" and values:
            matrix[0, 0] = values[0]
            matrix[1, 1] = values[1] if len(values) > 1 else values[0]
        elif operation == "rotate" and values:
            angle = np.deg2rad(values[0])
            rotation = np.array(
                [[np.cos(angle), -np.sin(angle), 0], [np.sin(angle), np.cos(angle), 0], [0, 0, 1]],
                dtype=np.float64,
            )
            if len(values) == 3:
                cx, cy = values[1:]
                to_origin = np.eye(3)
                to_origin[:2, 2] = [cx, cy]
                from_origin = np.eye(3)
                from_origin[:2, 2] = [-cx, -cy]
                matrix = to_origin @ rotation @ from_origin
            else:
                matrix = rotation
        else:
            raise ValueError(f"Unsupported or malformed SVG transform: {operation}({arguments})")
        result = result @ matrix
    return result


def _parse_points(points: str) -> list[tuple[float, float]]:
    values = [float(value) for value in NUMBER_PATTERN.findall(points)]
    if len(values) < 6 or len(values) % 2:
        return []
    return list(zip(values[0::2], values[1::2]))


def _semantic_class(group: ET.Element) -> int | None:
    group_id = group.attrib.get("id", "").lower()
    if group_id == "wall":
        return CLASS_ID["wall"]
    if group_id == "door":
        return CLASS_ID["door"]
    if group_id == "window":
        return CLASS_ID["window"]
    classes = group.attrib.get("class", "").split()
    if len(classes) < 2 or classes[0] != "Space":
        return None
    return ROOM_CLASS_IDS.get(classes[1], CLASS_ID["other_room"])


def rasterize_annotation(svg_path: Path, output_path: Path, source_size: tuple[int, int]) -> dict[str, int]:
    root = ET.parse(svg_path).getroot()
    view_box_values = [float(value) for value in NUMBER_PATTERN.findall(root.attrib.get("viewBox", ""))]
    source_width, source_height = source_size
    if len(view_box_values) == 4:
        view_x, view_y, view_width, view_height = view_box_values
    else:
        view_x = view_y = 0.0
        view_width = float(NUMBER_PATTERN.search(root.attrib.get("width", "")).group()) if NUMBER_PATTERN.search(root.attrib.get("width", "")) else float(source_width)
        view_height = float(NUMBER_PATTERN.search(root.attrib.get("height", "")).group()) if NUMBER_PATTERN.search(root.attrib.get("height", "")) else float(source_height)
    if view_width <= 0 or view_height <= 0:
        raise ValueError(f"Invalid SVG dimensions in {svg_path}")

    mask = Image.new("L", (IMAGE_SIZE, IMAGE_SIZE), color=0)
    draw = ImageDraw.Draw(mask)
    counts = {"room_groups": 0, "wall_groups": 0, "door_groups": 0, "window_groups": 0, "polygons": 0}
    scale = np.array(
        [
            [IMAGE_SIZE / view_width, 0, -view_x * IMAGE_SIZE / view_width],
            [0, IMAGE_SIZE / view_height, -view_y * IMAGE_SIZE / view_height],
            [0, 0, 1],
        ],
        dtype=np.float64,
    )

    def visit(element: ET.Element, parent_transform: np.ndarray) -> None:
        current_transform = parent_transform @ _transform_matrix(element.attrib.get("transform", ""))
        if _local_name(element.tag) == "g":
            label_id = _semantic_class(element)
            if label_id is not None:
                if label_id in {2, 3, 4, 5, 6, 7, 8, 9, 10}:
                    counts["room_groups"] += 1
                elif label_id == 1:
                    counts["wall_groups"] += 1
                elif label_id == 11:
                    counts["door_groups"] += 1
                elif label_id == 12:
                    counts["window_groups"] += 1
                for shape in element:
                    if _local_name(shape.tag) != "polygon":
                        continue
                    vertices = _parse_points(shape.attrib.get("points", ""))
                    if not vertices:
                        continue
                    shape_transform = current_transform @ _transform_matrix(shape.attrib.get("transform", ""))
                    coordinates = []
                    for x, y in vertices:
                        px, py, _ = scale @ shape_transform @ np.array([x, y, 1.0])
                        coordinates.append((float(px), float(py)))
                    draw.polygon(coordinates, fill=label_id)
                    counts["polygons"] += 1
        for child in element:
            visit(child, current_transform)

    visit(root, np.eye(3, dtype=np.float64))
    if counts["room_groups"] == 0 or counts["polygons"] == 0:
        raise ValueError(
            f"No supported Space polygons found in {svg_path}; verify this is a CubiCasa5K model.svg annotation"
        )

    mask.save(output_path)
    return counts


def _find_plan_image(annotation_path: Path) -> Path | None:
    candidates = (
        annotation_path.parent / "F1_scaled.png",
        annotation_path.parent / "F1_original.png",
        annotation_path.parent / "F1.png",
    )
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def prepare_data(input_dir: Path, output_dir: Path, image_size: int = IMAGE_SIZE) -> int:
    if image_size != IMAGE_SIZE:
        raise ValueError(f"This model expects --image-size {IMAGE_SIZE}")
    annotation_paths = sorted(input_dir.rglob("model.svg"))
    if not annotation_paths:
        raise FileNotFoundError(
            f"No model.svg annotations found under {input_dir}. Download and extract CubiCasa5K first."
        )

    images_dir = output_dir / "images"
    masks_dir = output_dir / "masks"
    images_dir.mkdir(parents=True, exist_ok=True)
    masks_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.jsonl"
    records: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    used_ids: dict[str, str] = {}

    for annotation_path in annotation_paths:
        source = annotation_path.parent.relative_to(input_dir).as_posix()
        image_path = _find_plan_image(annotation_path)
        if image_path is None:
            skipped.append(
                {
                    "source": source,
                    "reason": "no F1_scaled.png, F1_original.png, or F1.png image",
                }
            )
            continue
        sample_id = source.replace("/", "_")
        if sample_id in used_ids:
            skipped.append(
                {
                    "source": source,
                    "reason": f"sample ID collides with {used_ids[sample_id]}",
                }
            )
            continue
        used_ids[sample_id] = source
        image_output = images_dir / f"{sample_id}.png"
        mask_output = masks_dir / f"{sample_id}.png"
        try:
            with Image.open(image_path) as image:
                source_size = image.size
                image = image.convert("RGB").resize((IMAGE_SIZE, IMAGE_SIZE), Image.Resampling.LANCZOS)
                image.save(image_output)
            annotation_counts = rasterize_annotation(annotation_path, mask_output, source_size)
            records.append(
                {
                    "id": sample_id,
                    "image": image_output.relative_to(output_dir).as_posix(),
                    "mask": mask_output.relative_to(output_dir).as_posix(),
                    "source": source,
                    "source_image": image_path.name,
                    "source_dimensions": {"width": source_size[0], "height": source_size[1]},
                    "prepared_dimensions": {"width": IMAGE_SIZE, "height": IMAGE_SIZE},
                    "annotation_counts": annotation_counts,
                }
            )
        except (ET.ParseError, OSError, ValueError) as exc:
            image_output.unlink(missing_ok=True)
            mask_output.unlink(missing_ok=True)
            skipped.append({"source": source, "reason": str(exc)})

    report = {
        "input_dir": str(input_dir),
        "image_size": IMAGE_SIZE,
        "annotation_count": len(annotation_paths),
        "prepared_count": len(records),
        "skipped_count": len(skipped),
        "skipped": skipped,
    }
    report_path = output_dir / "preparation_report.json"
    temporary_report_path = report_path.with_suffix(".json.tmp")
    temporary_report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    temporary_report_path.replace(report_path)
    if skipped:
        (output_dir / "prepare_errors.txt").write_text(
            "\n".join(f"{item['source']}: {item['reason']}" for item in skipped),
            encoding="utf-8",
        )
    else:
        (output_dir / "prepare_errors.txt").unlink(missing_ok=True)
    if not records:
        raise ValueError("No usable CubiCasa5K samples were prepared.")
    with manifest_path.open("w", encoding="utf-8") as manifest_file:
        for record in records:
            manifest_file.write(json.dumps(record) + "\n")
    print(f"Prepared {len(records)} plans; skipped {len(skipped)}. Manifest: {manifest_path}")
    return len(records)


def main() -> None:
    parser = argparse.ArgumentParser(description="Rasterize CubiCasa5K SVG annotations for segmentation training.")
    parser.add_argument("--input-dir", type=Path, default=PROJECT_ROOT / "data/raw/cubicasa5k")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "data/processed/cubicasa")
    parser.add_argument("--image-size", type=int, default=IMAGE_SIZE)
    args = parser.parse_args()
    prepare_data(args.input_dir, args.output_dir, args.image_size)


if __name__ == "__main__":
    main()
