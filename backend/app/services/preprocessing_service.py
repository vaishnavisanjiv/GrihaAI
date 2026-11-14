from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
from PIL import Image, ImageOps


def convert_pdf_to_image(pdf_path: str, output_dir: str, page_number: int = 0) -> Optional[str]:
    """Convert the first page of a PDF into a PNG for analysis/previews."""
    try:
        from pdf2image import convert_from_path
    except Exception:
        return None

    try:
        images = convert_from_path(pdf_path, dpi=220, first_page=page_number + 1, last_page=page_number + 1)
    except Exception:
        return None

    if not images:
        return None

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    target_path = out_dir / f"{uuid.uuid4()}.png"
    images[0].save(target_path, format="PNG")
    return str(target_path)


def normalize_floor_plan_image(source_path: str, target_path: str) -> Dict[str, Any]:
    """Apply a lightweight preprocessing pass that improves downstream CV quality."""
    try:
        with Image.open(source_path) as image:
            image = ImageOps.exif_transpose(image).convert("L")
            width, height = image.size
            if max(width, height) > 3000:
                scale = 3000 / max(width, height)
                image = image.resize((max(1, int(width * scale)), max(1, int(height * scale))))

            numpy_image = np.asarray(image)
            blurred = cv2.GaussianBlur(numpy_image, (5, 5), 0)
            _, thresholded = cv2.threshold(blurred, 180, 255, cv2.THRESH_BINARY)
            normalized = Image.fromarray(thresholded)
            normalized.save(target_path, format="PNG")
            return {
                "source_path": source_path,
                "normalized_path": target_path,
                "width": normalized.size[0],
                "height": normalized.size[1],
                "processed": True,
            }
    except Exception:
        return {
            "source_path": source_path,
            "normalized_path": target_path,
            "width": 0,
            "height": 0,
            "processed": False,
        }


def prepare_plan_for_analysis(file_path: str, output_dir: str) -> str:
    """Normalize uploads to a single PNG suitable for CV analysis."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        converted = convert_pdf_to_image(file_path, output_dir)
        if converted:
            normalized_path = str(Path(output_dir) / f"{uuid.uuid4()}.png")
            normalize_floor_plan_image(converted, normalized_path)
            return normalized_path
        return file_path

    normalized_path = str(Path(output_dir) / f"{uuid.uuid4()}.png")
    normalize_floor_plan_image(file_path, normalized_path)
    return normalized_path
