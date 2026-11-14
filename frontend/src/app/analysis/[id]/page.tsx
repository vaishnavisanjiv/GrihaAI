'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { isAxiosError } from 'axios';
import { Loader2, AlertCircle, RefreshCw, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

import api from '@/lib/api';
import {
  AnalysisData,
  ReportData,
  AssistantResponse,
  SpatialReviewStatus,
  SpatialEdge,
} from '@/components/analysis/types';
import { AnalysisHeader } from '@/components/analysis/AnalysisHeader';
import { ExecutiveSummary } from '@/components/analysis/ExecutiveSummary';
import { FloorPlanViewer } from '@/components/analysis/FloorPlanViewer';
import { RoomAnalysis } from '@/components/analysis/RoomAnalysis';
import { ElementDetection } from '@/components/analysis/ElementDetection';
import { SpatialRelationships } from '@/components/analysis/SpatialRelationships';
import { ComplianceScreening } from '@/components/analysis/ComplianceScreening';
import { RecommendationsPanel } from '@/components/analysis/RecommendationsPanel';
import { TechnicalDetails } from '@/components/analysis/TechnicalDetails';
import { AnalysisAssistant } from '@/components/analysis/AnalysisAssistant';
import { ScaleCalibrationModal } from '@/components/analysis/ScaleCalibrationModal';

const POLL_INTERVAL_MS = 3000;

export default function AnalysisPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const analysisId = params.id;

  const [data, setData] = useState<AnalysisData | null>(null);
  const [report, setReport] = useState<ReportData | null>(null);
  const [assistantResponse, setAssistantResponse] = useState<AssistantResponse | null>(null);
  const [planImageUrl, setPlanImageUrl] = useState('');
  const [loading, setLoading] = useState(true);
  const [pollingStatus, setPollingStatus] = useState<string | null>(null);
  const pollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Selection states across visualizer and lists
  const [selectedRoomId, setSelectedRoomId] = useState<number | null>(null);
  const [selectedElementId, setSelectedElementId] = useState<number | null>(null);

  // Operation states
  const [assistantLoading, setAssistantLoading] = useState(false);
  const [assistantError, setAssistantError] = useState('');
  const [reviewingEdgeId, setReviewingEdgeId] = useState<number | null>(null);
  const [reviewError, setReviewError] = useState('');
  const [analysisError, setAnalysisError] = useState('');
  const [legacyFloorPlanId, setLegacyFloorPlanId] = useState<number | null>(null);
  const [isReanalyzing, setIsReanalyzing] = useState(false);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);
  const [isCalibrationOpen, setIsCalibrationOpen] = useState(false);

  // Record a review on a spatial edge
  const recordSpatialReview = async (edgeId: number, reviewStatus: SpatialReviewStatus) => {
    setReviewingEdgeId(edgeId);
    setReviewError('');
    try {
      const response = await api.put<SpatialEdge>(
        `/api/analysis/${analysisId}/graph/${edgeId}/review`,
        { review_status: reviewStatus },
      );
      setData((current) =>
        current
          ? {
              ...current,
              spatial_edges: current.spatial_edges?.map((edge) =>
                edge.id === edgeId ? response.data : edge,
              ),
            }
          : current,
      );
    } catch (error: unknown) {
      setReviewError(
        isAxiosError<{ detail?: string }>(error)
          ? error.response?.data?.detail || error.message
          : error instanceof Error
            ? error.message
            : 'Could not save the review decision.',
      );
    } finally {
      setReviewingEdgeId(null);
    }
  };

  // Ask BuildGuard Assistant
  const askAssistant = async (question: string) => {
    if (!analysisId || !question.trim()) return;

    setAssistantLoading(true);
    setAssistantError('');
    try {
      const response = await api.post<AssistantResponse>(`/api/assistant/${analysisId}/ask`, {
        question,
      });
      setAssistantResponse(response.data);
    } catch (error: unknown) {
      setAssistantResponse(null);
      setAssistantError(
        isAxiosError<{ detail?: string }>(error)
          ? error.response?.data?.detail || error.message
          : error instanceof Error
            ? error.message
            : 'The assistant request failed.',
      );
    } finally {
      setAssistantLoading(false);
    }
  };

  // Download PDF Report
  const downloadPdfReport = async () => {
    if (!analysisId) return;
    setIsDownloadingPdf(true);
    try {
      const response = await api.get(`/api/reports/${analysisId}/download`, {
        responseType: 'blob',
      });
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `buildguard-report-${analysisId}.pdf`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (err: unknown) {
      alert(`Could not download PDF report: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  // Export JSON Report
  const exportJsonReport = () => {
    if (!data) return;
    const payload = {
      analysis: data.analysis,
      rooms: data.rooms,
      elements: data.elements,
      compliance_results: data.compliance_results,
      spatial_edges: data.spatial_edges,
      report: report || {},
    };

    const json = JSON.stringify(payload, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `buildguard-report-${data.analysis?.id || analysisId}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  // Re-run analysis with trained model for legacy records
  const reanalyzeWithTrainedModel = async () => {
    if (!legacyFloorPlanId) return;
    setIsReanalyzing(true);
    setAnalysisError('');
    try {
      const startRes = await api.post<{ id: number }>(`/api/analysis/${legacyFloorPlanId}/start`);
      router.push(`/analysis/${startRes.data.id}`);
    } catch (err: unknown) {
      setAnalysisError(
        isAxiosError<{ detail?: string }>(err)
          ? err.response?.data?.detail || err.message
          : 'Failed to start analysis.',
      );
    } finally {
      setIsReanalyzing(false);
    }
  };

  // Fetch complete analysis details once COMPLETED
  const fetchCompletedAnalysis = useCallback(async () => {
    if (!analysisId) return;
    try {
      const response = await api.get<AnalysisData>(`/api/analysis/${analysisId}`);

      // Check for legacy synthetic demo result
      if (response.data.analysis?.cv_method !== 'cubicasa5k-unet-segmentation') {
        setLegacyFloorPlanId(response.data.analysis?.floor_plan_id ?? null);
        setAnalysisError(
          'This saved result was not produced by the trained floor-plan model. It may be a legacy synthetic demo result and is hidden to avoid showing fabricated plan measurements.',
        );
        setData(null);
        setLoading(false);
        return;
      }

      setData(response.data);

      // Fetch plan image
      if (response.data.analysis?.floor_plan_id) {
        try {
          const imageResponse = await api.get(
            `/api/floor-plans/${response.data.analysis.floor_plan_id}/image`,
            { responseType: 'blob' },
          );
          setPlanImageUrl(URL.createObjectURL(imageResponse.data));
        } catch {
          setPlanImageUrl('');
        }
      }

      // Fetch report
      try {
        const reportResponse = await api.get<ReportData>(`/api/reports/${analysisId}`);
        setReport(reportResponse.data);
      } catch {
        setReport(null);
      }

      setLoading(false);
      setPollingStatus(null);
    } catch (error: unknown) {
      setData(null);
      setAnalysisError(
        isAxiosError<{ detail?: string }>(error)
          ? error.response?.data?.detail || error.message
          : error instanceof Error
            ? error.message
            : 'Could not load this analysis.',
      );
      setLoading(false);
      setPollingStatus(null);
    }
  }, [analysisId]);

  // Main loader and status polling effect
  useEffect(() => {
    let isCancelled = false;

    const pollStatus = async () => {
      if (!analysisId || isCancelled) return;
      try {
        const statusRes = await api.get<{ status: string; error_message?: string }>(
          `/api/analysis/${analysisId}/status`,
        );

        if (isCancelled) return;
        const currentStatus = statusRes.data.status;

        if (currentStatus === 'PENDING' || currentStatus === 'RUNNING') {
          setPollingStatus(currentStatus);
          setLoading(true);
          pollTimerRef.current = setTimeout(pollStatus, POLL_INTERVAL_MS);
        } else if (currentStatus === 'COMPLETED') {
          setPollingStatus(null);
          await fetchCompletedAnalysis();
        } else if (currentStatus === 'FAILED') {
          setPollingStatus('FAILED');
          setAnalysisError(
            statusRes.data.error_message || 'Floor plan analysis failed during model execution.',
          );
          setLoading(false);
        } else {
          await fetchCompletedAnalysis();
        }
      } catch {
        // Fallback to full fetch if status endpoint is not reachable
        if (!isCancelled) {
          await fetchCompletedAnalysis();
        }
      }
    };

    void pollStatus();

    return () => {
      isCancelled = true;
      if (pollTimerRef.current) clearTimeout(pollTimerRef.current);
    };
  }, [analysisId, fetchCompletedAnalysis]);

  // Cleanup image blob
  useEffect(() => {
    return () => {
      if (planImageUrl) URL.revokeObjectURL(planImageUrl);
    };
  }, [planImageUrl]);

  // 1. Loading State (with explicit polling progress)
  if (loading) {
    const isInProgress = pollingStatus === 'PENDING' || pollingStatus === 'RUNNING';
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4 p-8 text-slate-600">
        <Loader2 className="h-10 w-10 animate-spin text-cyan-600" />
        <div className="text-center space-y-1">
          <h2 className="text-lg font-bold text-slate-800">
            {isInProgress ? 'Running Architectural Layout Analysis...' : 'Loading Analysis Results...'}
          </h2>
          <p className="text-xs text-slate-500 max-w-md">
            {isInProgress
              ? `Status: ${pollingStatus}. Semantic segmentation and polygon extraction are running in the background. The page will refresh automatically.`
              : 'Fetching verified geometry records, spatial candidates, and compliance screening findings.'}
          </p>
        </div>
      </div>
    );
  }

  // 2. Error / Legacy Demo Warning State
  if (!data) {
    return (
      <div className="space-y-6 p-6 md:p-8 max-w-4xl">
        <Link
          href="/upload"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Floor Plan Upload
        </Link>

        <div className="rounded-xl border border-amber-200 bg-amber-50 p-6 text-amber-900 shadow-xs space-y-3">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 shrink-0 text-amber-600" />
            <h1 className="text-base font-bold text-slate-900">
              No Verified Model Analysis Available
            </h1>
          </div>

          <p className="text-xs leading-relaxed text-slate-700">
            {analysisError ||
              'This saved result was not produced by the trained floor-plan model. It may be a legacy synthetic demo result and is hidden to avoid displaying fabricated measurements.'}
          </p>

          <p className="text-xs text-slate-600">
            A verified PyTorch checkpoint is active at <code>backend/models/floorplan_unet.pt</code>.
            You can re-analyze this floor plan now with the trained 13-class model.
          </p>

          {legacyFloorPlanId && (
            <div className="pt-2">
              <button
                type="button"
                onClick={reanalyzeWithTrainedModel}
                disabled={isReanalyzing}
                className="inline-flex items-center gap-2 rounded-lg bg-cyan-600 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-cyan-700 disabled:opacity-50"
              >
                {isReanalyzing ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
                {isReanalyzing ? 'Starting Analysis...' : 'Run Analysis with Trained Model'}
              </button>
            </div>
          )}
        </div>
      </div>
    );
  }

  // 3. Redesigned Complete Dashboard
  return (
    <div className="space-y-6 p-6 md:p-8 max-w-7xl mx-auto">
      {/* SECTION A: Analysis Header */}
      <AnalysisHeader
        data={data}
        onDownloadPdf={downloadPdfReport}
        onExportJson={exportJsonReport}
        isDownloadingPdf={isDownloadingPdf}
        onOpenCalibration={() => setIsCalibrationOpen(true)}
      />

      {/* SECTION B: Executive Summary */}
      <ExecutiveSummary data={data} />

      {/* SECTION C: Floor Plan Visualization (Spatial Overlay Board) */}
      <FloorPlanViewer
        data={data}
        planImageUrl={planImageUrl}
        selectedRoomId={selectedRoomId}
        selectedElementId={selectedElementId}
        onSelectRoom={setSelectedRoomId}
        onSelectElement={setSelectedElementId}
      />

      {/* SECTION D: Room Analysis */}
      <RoomAnalysis
        rooms={data.rooms || []}
        selectedRoomId={selectedRoomId}
        onSelectRoom={setSelectedRoomId}
        isCalibrated={Boolean(data.scale_calibrated || data.rooms?.some((r) => r.area_sqm != null))}
      />

      {/* SECTION E: Architectural Element Detection */}
      <ElementDetection
        elements={data.elements || []}
        selectedElementId={selectedElementId}
        onSelectElement={setSelectedElementId}
      />

      {/* SECTION F: Spatial Relationship Analysis */}
      <SpatialRelationships
        data={data}
        onRecordReview={recordSpatialReview}
        reviewingEdgeId={reviewingEdgeId}
        reviewError={reviewError}
      />

      {/* SECTION G: Preliminary Compliance and Safety Screening */}
      <ComplianceScreening
        findings={data.compliance_results || []}
        isCalibrated={Boolean(data.scale_calibrated || data.rooms?.some((r) => r.area_sqm != null))}
        onOpenCalibration={() => setIsCalibrationOpen(true)}
      />

      {/* SECTION H: Recommendations & Next Steps */}
      <RecommendationsPanel
        recommendations={report?.recommendations}
        isCalibrated={Boolean(data.scale_calibrated || data.rooms?.some((r) => r.area_sqm != null))}
      />

      {/* SECTION 4: Ask BuildGuard Assistant */}
      <AnalysisAssistant
        onAsk={askAssistant}
        response={assistantResponse}
        isLoading={assistantLoading}
        error={assistantError}
      />

      {/* SECTION I: Technical Details (Collapsible) */}
      <TechnicalDetails data={data} />

      {/* Scale Calibration Modal */}
      <ScaleCalibrationModal
        isOpen={isCalibrationOpen}
        onClose={() => setIsCalibrationOpen(false)}
        floorPlanId={data.floor_plan_id || data.analysis?.floor_plan_id || 0}
        currentScale={data.scale_pixels_per_mm}
        rooms={data.rooms || []}
        elements={data.elements || []}
        onScaleApplied={fetchCompletedAnalysis}
      />
    </div>
  );
}
