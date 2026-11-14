import os
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from app.models.floor_plan import FloorPlan
from app.models.project import Project
from app.core.config import settings
from app.services.cv_parser import analyze_plan_image
from app.services.preprocessing_service import prepare_plan_for_analysis
from PIL import Image, ImageDraw


def get_file_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


def validate_file(file: UploadFile):
    allowed_extensions = {".png", ".jpg", ".jpeg", ".webp", ".pdf"}
    ext = get_file_extension(file.filename or "")
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {allowed_extensions}",
        )
    return ext


async def save_upload_file(upload_file: UploadFile, destination: str) -> int:
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    total_size = 0
    try:
        with open(destination, "wb") as buffer:
            while chunk := await upload_file.read(1024 * 1024):
                total_size += len(chunk)
                if total_size > max_size:
                    raise HTTPException(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        detail=f"File too large. Max size is {settings.MAX_FILE_SIZE_MB}MB",
                    )
                buffer.write(chunk)
        return total_size
    except Exception:
        Path(destination).unlink(missing_ok=True)
        raise
    finally:
        await upload_file.close()


def _create_preview_image(source_path: str, preview_path: str) -> None:
    try:
        with Image.open(source_path) as img:
            resized = img.convert("RGB")
            resized = resized.resize((1400, max(900, resized.height)))
            resized.save(preview_path, format="PNG")
            return
    except Exception:
        pass

    placeholder = Image.new("RGB", (1400, 900), color=(15, 23, 42))
    draw = ImageDraw.Draw(placeholder)
    draw.rectangle((80, 80, 1320, 820), outline=(34, 211, 238), width=4)
    draw.text((150, 390), "Floor Plan Preview", fill=(255, 255, 255))
    placeholder.save(preview_path, format="PNG")


async def upload_floor_plan(db: Session, project_id: int, file: UploadFile) -> FloorPlan:
    ext = validate_file(file)
    unique_filename = f"{uuid.uuid4()}{ext}"
    storage_path = os.path.join(settings.STORAGE_PATH, unique_filename)

    file_size = await save_upload_file(file, storage_path)

    width, height = None, None
    if ext in {".png", ".jpg", ".jpeg", ".webp"}:
        try:
            with Image.open(storage_path) as img:
                img.verify()
            with Image.open(storage_path) as img:
                width, height = img.size
        except Exception:
            Path(storage_path).unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image file",
            )
    else:
        with open(storage_path, "rb") as uploaded_pdf:
            is_pdf = uploaded_pdf.read(5) == b"%PDF-"
        if not is_pdf:
            Path(storage_path).unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF file",
            )

    db_floor_plan = FloorPlan(
        project_id=project_id,
        filename=unique_filename,
        original_filename=Path(file.filename or unique_filename).name,
        storage_path=storage_path,
        file_type=ext,
        file_size=file_size,
        width=width,
        height=height,
        status="UPLOADED",
    )

    db.add(db_floor_plan)
    db.commit()
    db.refresh(db_floor_plan)
    return db_floor_plan


def list_floor_plans_for_user(db: Session, user_id: int):
    return (
        db.query(FloorPlan)
        .join(Project, FloorPlan.project_id == Project.id)
        .filter(Project.user_id == user_id)
        .order_by(FloorPlan.created_at.desc())
        .all()
    )


def get_floor_plan_for_user(db: Session, floor_plan_id: int, user_id: int) -> FloorPlan:
    floor_plan = db.query(FloorPlan).filter(FloorPlan.id == floor_plan_id).first()
    if not floor_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Floor plan not found")

    project = db.query(Project).filter(Project.id == floor_plan.project_id, Project.user_id == user_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return floor_plan


def process_floor_plan(db: Session, floor_plan_id: int, user_id: int) -> FloorPlan:
    floor_plan = get_floor_plan_for_user(db, floor_plan_id, user_id)
    floor_plan.status = "PROCESSING"
    db.commit()

    preview_dir = Path(settings.STORAGE_PATH) / "previews"
    preview_dir.mkdir(parents=True, exist_ok=True)
    preview_name = f"{uuid.uuid4()}.png"
    preview_path = preview_dir / preview_name

    analysis_source = floor_plan.storage_path
    if floor_plan.file_type == ".pdf":
        analysis_source = prepare_plan_for_analysis(floor_plan.storage_path, str(preview_dir))
        if Path(analysis_source).suffix.lower() == ".pdf":
            floor_plan.status = "FAILED"
            db.commit()
            raise HTTPException(
                status_code=422,
                detail="Could not convert this PDF. Install Poppler and add it to PATH, then retry.",
            )

    if floor_plan.file_type != ".pdf":
        _create_preview_image(floor_plan.storage_path, str(preview_path))

    if floor_plan.file_type == ".pdf":
        try:
            _create_preview_image(analysis_source, str(preview_path))
        except Exception:
            _create_preview_image(floor_plan.storage_path, str(preview_path))

    floor_plan.width = floor_plan.width or 1400
    floor_plan.height = floor_plan.height or 900

    features = analyze_plan_image(analysis_source)
    if not floor_plan.scale_pixels_per_mm:
        floor_plan.scale_source = "uncalibrated"
    floor_plan.status = "PROCESSED"

    db.commit()
    db.refresh(floor_plan)
    return floor_plan
