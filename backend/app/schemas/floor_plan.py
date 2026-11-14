from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class FloorPlanBase(BaseModel):
    filename: str
    original_filename: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    page_number: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    scale_pixels_per_mm: Optional[float] = None
    scale_source: Optional[str] = None
    status: str

class FloorPlanResponse(FloorPlanBase):
    id: int
    project_id: int
    created_at: datetime

    model_config = { "from_attributes": True }

class FloorPlanUploadResponse(BaseModel):
    id: int
    message: str
    filename: str


class ScaleCalibrationRequest(BaseModel):
    x1: Optional[float] = None
    y1: Optional[float] = None
    x2: Optional[float] = None
    y2: Optional[float] = None
    known_distance_mm: Optional[float] = Field(default=None, gt=0)
    scale_pixels_per_mm: Optional[float] = Field(default=None, gt=0)
    preset_type: Optional[str] = None
    reference_real_length_m: Optional[float] = None
