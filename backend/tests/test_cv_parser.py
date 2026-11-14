import io
import os
import tempfile

from PIL import Image

from app.services.cv_parser import analyze_plan_image


def create_png_bytes(width=200, height=120, color=(0, 255, 0)):
    image = Image.new("RGB", (width, height), color)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_analyze_plan_image_returns_layout_features():
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        temp_file.write(create_png_bytes())
        temp_path = temp_file.name

    try:
        features = analyze_plan_image(temp_path)
        assert "room_count_estimate" in features
        assert "wall_density" in features
        assert "door_candidates" in features
        assert "estimated_scale_mm_per_px" in features
        assert features["room_count_estimate"] >= 3
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
