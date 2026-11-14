from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, Optional, List


class DetectedElementResponse(BaseModel):
    id: int
    element_type: str
    label: Optional[str] = None
    confidence: Optional[float] = None
    geometry_json: Optional[str] = None
    properties_json: Optional[str] = None

    model_config = {"from_attributes": True}


class RoomResponse(BaseModel):
    id: int
    label: Optional[str] = None
    polygon_json: Optional[str] = None
    area_pixels: Optional[float] = None
    area_sqm: Optional[float] = None
    width_m: Optional[float] = None
    length_m: Optional[float] = None
    confidence: Optional[float] = None

    model_config = {"from_attributes": True}


class SpatialEdgeReviewResponse(BaseModel):
    id: int
    reviewer_user_id: int
    review_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SpatialEdgeResponse(BaseModel):
    id: int
    source_element_id: Optional[int] = None
    target_element_id: Optional[int] = None
    relationship_type: Optional[str] = None
    properties_json: Optional[str] = None
    reviews: List[SpatialEdgeReviewResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class SpatialEdgeReviewRequest(BaseModel):
    review_status: Literal["plausible", "not_plausible", "uncertain"]


class ComplianceResultResponse(BaseModel):
    id: int
    rule_id: str
    status: str
    severity: Optional[str] = None
    message: Optional[str] = None
    explanation: Optional[str] = None
    recommendation: Optional[str] = None

    model_config = {"from_attributes": True}


class AnalysisResponse(BaseModel):
    """
    Core analysis record. Returned by both the start-analysis (202) endpoint
    and the status-polling endpoint. Clients should poll GET /{id}/status
    until status is COMPLETED or FAILED, then fetch the full summary.
    """
    id: int
    floor_plan_id: int
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    model_version: Optional[str] = None
    cv_method: Optional[str] = None

    model_config = {"from_attributes": True}


# Alias used by the status-polling endpoint; same fields as AnalysisResponse.
AnalysisStatusResponse = AnalysisResponse


class AnalysisSummaryResponse(BaseModel):
    analysis: AnalysisResponse
    rooms: List[RoomResponse]
    elements: List[DetectedElementResponse]
    compliance_results: List[ComplianceResultResponse]
    spatial_edges: List[SpatialEdgeResponse] = Field(default_factory=list)
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    floor_plan_filename: Optional[str] = None
