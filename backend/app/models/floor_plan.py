from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class FloorPlan(Base):
    __tablename__ = "floor_plans"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    file_type = Column(String)
    file_size = Column(Integer)
    page_number = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    scale_pixels_per_mm = Column(Float)
    scale_source = Column(String)
    status = Column(String, default="UPLOADED")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
