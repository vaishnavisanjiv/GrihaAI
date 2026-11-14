import io
import os
import tempfile

from PIL import Image

from app.services.preprocessing_service import normalize_floor_plan_image


def create_png_bytes(width=200, height=120, color=(0, 255, 0)):
    image = Image.new("RGB", (width, height), color)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_normalize_floor_plan_image_creates_processed_png():
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as source:
        source.write(create_png_bytes())
        source_path = source.name

    target_path = source_path + ".normalized.png"
    try:
        result = normalize_floor_plan_image(source_path, target_path)
        assert result["processed"] is True
        assert os.path.exists(target_path)
        assert result["width"] > 0
        assert result["height"] > 0
    finally:
        if os.path.exists(source_path):
            os.remove(source_path)
        if os.path.exists(target_path):
            os.remove(target_path)
