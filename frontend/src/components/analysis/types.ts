export type PolygonPoint = [number, number];

export interface ComplianceFinding {
  id: number;
  rule_id: string;
  status: string;
  severity?: string | null;
  message?: string | null;
  explanation?: string | null;
  recommendation?: string | null;
}

export interface AnalysisRoom {
  id: number;
  label?: string | null;
  polygon_json?: string | null;
  area_pixels?: number | null;
  area_sqm?: number | null;
  width_m?: number | null;
  length_m?: number | null;
  confidence?: number | null;
  centroid_x?: number | null;
  centroid_y?: number | null;
}

export interface AnalysisElement {
  id: number;
  element_type: string;
  label?: string | null;
  confidence?: number | null;
  geometry_json?: string | null;
  properties_json?: string | null;
}

export type SpatialReviewStatus = 'plausible' | 'not_plausible' | 'uncertain';

export interface SpatialEdgeReview {
  id: number;
  reviewer_user_id: number;
  review_status: SpatialReviewStatus;
  created_at: string;
}

export interface SpatialEdge {
  id: number;
  source_element_id?: number | null;
  target_element_id?: number | null;
  relationship_type?: string | null;
  properties_json?: string | null;
  reviews?: SpatialEdgeReview[];
}

export interface AnalysisData {
  analysis?: {
    id?: number;
    floor_plan_id?: number;
    status?: string;
    started_at?: string;
    completed_at?: string | null;
    cv_method?: string | null;
    model_version?: string | null;
    error_message?: string | null;
  };
  rooms: AnalysisRoom[];
  elements: AnalysisElement[];
  spatial_edges?: SpatialEdge[];
  compliance_results: ComplianceFinding[];
  image_width?: number | null;
  image_height?: number | null;
  floor_plan_filename?: string | null;
  floor_plan_id?: number | null;
  scale_calibrated?: boolean;
  scale_pixels_per_mm?: number | null;
  scale_source?: string | null;
}

export interface ReportData {
  status?: string;
  narrative?: string;
  recommendations?: string[];
  assessment_notice?: string;
  summary?: {
    pass_count?: number;
    warning_count?: number;
    fail_count?: number;
    not_assessed_count?: number;
  };
  executive_summary?: {
    room_count?: number;
    element_count?: number;
    candidate_count?: number;
    reviewed_candidate_count?: number;
    not_assessed_count?: number;
  };
  room_breakdown?: { category: string; count: number }[];
  element_breakdown?: { type: string; count: number }[];
  rules?: ComplianceFinding[];
}

export interface AssistantResponse {
  answer: string;
  context?: string[];
  evidence?: unknown[];
  suggested_actions?: string[];
}
