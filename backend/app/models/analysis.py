from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id = Column(Integer, primary_key=True, index=True)
    floor_plan_id = Column(Integer, ForeignKey("floor_plans.id"), nullable=False)
    status = Column(String, default="PENDING")
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    model_version = Column(String)
    cv_method = Column(String)
    error_message = Column(Text)

class DetectedElement(Base):
    __tablename__ = "detected_elements"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analysis_runs.id"), nullable=False)
    element_type = Column(String, nullable=False)
    label = Column(String)
    confidence = Column(Float)
    geometry_json = Column(Text)
    properties_json = Column(Text)

class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analysis_runs.id"), nullable=False)
    element_id = Column(Integer, ForeignKey("detected_elements.id"))
    label = Column(String)
    polygon_json = Column(Text)
    area_pixels = Column(Float)
    area_sqm = Column(Float)
    width_m = Column(Float)
    length_m = Column(Float)
    centroid_x = Column(Float)
    centroid_y = Column(Float)
    confidence = Column(Float)

class SpatialEdge(Base):
    __tablename__ = "spatial_edges"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analysis_runs.id"), nullable=False)
    source_element_id = Column(Integer)
    target_element_id = Column(Integer)
    relationship_type = Column(String)
    properties_json = Column(Text)
    reviews = relationship(
        "SpatialEdgeReview",
        back_populates="edge",
        cascade="all, delete-orphan",
        order_by="SpatialEdgeReview.id",
    )

class SpatialEdgeReview(Base):
    __tablename__ = "spatial_edge_reviews"

    id = Column(Integer, primary_key=True, index=True)
    spatial_edge_id = Column(Integer, ForeignKey("spatial_edges.id"), nullable=False, index=True)
    reviewer_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    review_status = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    edge = relationship("SpatialEdge", back_populates="reviews")

class ComplianceResult(Base):
    __tablename__ = "compliance_results"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analysis_runs.id"), nullable=False)
    rule_id = Column(String, nullable=False)
    status = Column(String, nullable=False)
    severity = Column(String)
    evidence_json = Column(Text)
    measurement_json = Column(Text)
    message = Column(Text)
    explanation = Column(Text)
    recommendation = Column(Text)
