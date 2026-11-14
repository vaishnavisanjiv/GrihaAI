'use client';

import { useState, useMemo } from 'react';
import {
  ArrowRightLeft,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Clock,
  ShieldAlert,
  ChevronDown,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { AnalysisData, SpatialReviewStatus } from './types';

interface SpatialRelationshipsProps {
  data: AnalysisData;
  onRecordReview: (edgeId: number, status: SpatialReviewStatus) => Promise<void>;
  reviewingEdgeId: number | null;
  reviewError?: string;
}

const PAGE_SIZE = 10;

export function SpatialRelationships({
  data,
  onRecordReview,
  reviewingEdgeId,
  reviewError,
}: SpatialRelationshipsProps) {
  const edges = useMemo(() => data.spatial_edges || [], [data.spatial_edges]);
  const rooms = useMemo(() => data.rooms || [], [data.rooms]);
  const elements = useMemo(() => data.elements || [], [data.elements]);

  const [typeFilter, setTypeFilter] = useState<'ALL' | 'ADJACENT' | 'PROXIMATE'>('ALL');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'PENDING' | 'PLAUSIBLE' | 'NOT_PLAUSIBLE' | 'UNCERTAIN'>('ALL');
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);

  // Helper to parse properties
  const parsedEdges = useMemo(() => {
    return edges.map((edge) => {
      let props: {
        confidence?: number;
        source_node_type?: string;
        target_node_type?: string;
        evidence?: { distance_pixels?: number };
        review_status?: SpatialReviewStatus;
        reviewed_at?: string;
      } = {};

      try {
        props = JSON.parse(edge.properties_json || '{}');
      } catch {
        props = {};
      }

      // Resolve source label
      const sourceLabel =
        props.source_node_type === 'room'
          ? rooms.find((r) => r.id === edge.source_element_id)?.label || `Room #${edge.source_element_id}`
          : elements.find((el) => el.id === edge.source_element_id)?.label || `Element #${edge.source_element_id}`;

      // Resolve target label
      const targetLabel =
        props.target_node_type === 'room'
          ? rooms.find((r) => r.id === edge.target_element_id)?.label || `Room #${edge.target_element_id}`
          : elements.find((el) => el.id === edge.target_element_id)?.label || `Element #${edge.target_element_id}`;

      // Latest review
      const latestReview = edge.reviews && edge.reviews.length > 0
        ? edge.reviews[edge.reviews.length - 1].review_status
        : props.review_status || null;

      const relType = edge.relationship_type || 'SPATIAL_CANDIDATE';
      const isAdjacent = relType.toUpperCase().includes('ADJACENT');

      return {
        ...edge,
        props,
        sourceLabel,
        targetLabel,
        latestReview,
        isAdjacent,
        distancePixels: props.evidence?.distance_pixels,
        confidencePct: props.confidence != null ? Math.round(props.confidence * 100) : null,
      };
    });
  }, [edges, rooms, elements]);

  // Counts
  const reviewedCount = useMemo(() => parsedEdges.filter((e) => e.latestReview != null).length, [parsedEdges]);
  const pendingCount = parsedEdges.length - reviewedCount;

  // Filter edges
  const filteredEdges = useMemo(() => {
    return parsedEdges.filter((edge) => {
      // Type filter
      if (typeFilter === 'ADJACENT' && !edge.isAdjacent) return false;
      if (typeFilter === 'PROXIMATE' && edge.isAdjacent) return false;

      // Status filter
      if (statusFilter === 'PENDING' && edge.latestReview != null) return false;
      if (statusFilter === 'PLAUSIBLE' && edge.latestReview !== 'plausible') return false;
      if (statusFilter === 'NOT_PLAUSIBLE' && edge.latestReview !== 'not_plausible') return false;
      if (statusFilter === 'UNCERTAIN' && edge.latestReview !== 'uncertain') return false;

      return true;
    });
  }, [parsedEdges, typeFilter, statusFilter]);

  const displayedEdges = filteredEdges.slice(0, visibleCount);

  return (
    <Card className="border-slate-200 bg-white shadow-xs">
      <CardHeader className="border-b border-slate-100 bg-slate-50/50 pb-3">
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            <CardTitle className="text-base font-bold text-slate-900">
              Spatial Relationship Analysis
            </CardTitle>
            <p className="mt-0.5 text-xs text-slate-500">
              Potential geometric relationships inferred from detected floor-plan regions. These are candidates for human review, not verified room connections or safety findings.
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <span className="rounded-md border border-slate-200 bg-white px-2.5 py-1 text-slate-700 font-medium">
              Total: <strong>{edges.length}</strong>
            </span>
            <span className="rounded-md border border-amber-200 bg-amber-50 px-2.5 py-1 text-amber-800 font-medium">
              Pending: <strong>{pendingCount}</strong>
            </span>
            <span className="rounded-md border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-emerald-800 font-medium">
              Reviewed: <strong>{reviewedCount}</strong>
            </span>
          </div>
        </div>

        {/* Notice disclaimer */}
        <div className="mt-2 flex items-start gap-2 rounded-lg border border-amber-200/80 bg-amber-50/80 p-2.5 text-xs text-amber-900">
          <ShieldAlert className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-600" />
          <span>
            <strong>Geometric Precedence Note:</strong> Spatial adjacency candidates indicate polygon proximity (under 1.5 pixels apart).
            They do not verify door passages, handicap accessibility clearances, or fire egress circulation routes.
          </span>
        </div>

        {/* Error message */}
        {reviewError && (
          <p role="alert" className="mt-2 text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded p-2">
            {reviewError}
          </p>
        )}

        {/* Filters */}
        <div className="mt-3 flex flex-wrap items-center gap-2 pt-1 text-xs">
          {/* Type Filter */}
          <div className="flex items-center gap-1 rounded-md border border-slate-200 bg-white p-0.5">
            <button
              type="button"
              onClick={() => setTypeFilter('ALL')}
              className={`rounded px-2.5 py-1 font-semibold transition ${
                typeFilter === 'ALL' ? 'bg-slate-900 text-white' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              All Types
            </button>
            <button
              type="button"
              onClick={() => setTypeFilter('ADJACENT')}
              className={`rounded px-2.5 py-1 font-semibold transition ${
                typeFilter === 'ADJACENT' ? 'bg-slate-900 text-white' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Adjacency Candidates
            </button>
            <button
              type="button"
              onClick={() => setTypeFilter('PROXIMATE')}
              className={`rounded px-2.5 py-1 font-semibold transition ${
                typeFilter === 'PROXIMATE' ? 'bg-slate-900 text-white' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Proximity Candidates
            </button>
          </div>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as typeof statusFilter)}
            className="rounded-md border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-700 outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Review Statuses</option>
            <option value="PENDING">Awaiting Review ({pendingCount})</option>
            <option value="PLAUSIBLE">Seems Plausible</option>
            <option value="NOT_PLAUSIBLE">Seems Incorrect</option>
            <option value="UNCERTAIN">Unsure</option>
          </select>
        </div>
      </CardHeader>

      <CardContent className="p-4 space-y-3">
        {displayedEdges.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-6 text-center text-xs text-slate-500">
            No spatial relationship candidates match the active filter criteria.
          </div>
        ) : (
          <div className="space-y-2.5">
            {displayedEdges.map((edge) => {
              const isSaving = reviewingEdgeId === edge.id;
              const hasReview = Boolean(edge.latestReview);

              return (
                <div
                  key={edge.id}
                  className="rounded-xl border border-slate-200 bg-white p-3.5 shadow-2xs transition hover:border-slate-300"
                >
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    {/* Source <-> Target Details */}
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-mono font-semibold uppercase text-slate-400">
                          Candidate #{edge.id}
                        </span>
                        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-700">
                          {edge.isAdjacent ? 'Potential Adjacency' : 'Spatial Proximity'}
                        </span>
                      </div>

                      <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                        <span>{edge.sourceLabel}</span>
                        <ArrowRightLeft className="h-3.5 w-3.5 text-cyan-600 shrink-0" />
                        <span>{edge.targetLabel}</span>
                      </div>

                      <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
                        {edge.distancePixels != null && (
                          <span>Separation: <strong className="font-mono text-slate-700">{edge.distancePixels.toFixed(1)} px</strong></span>
                        )}
                        {edge.confidencePct != null && (
                          <span>Model score: <strong className="font-mono text-slate-700">{edge.confidencePct}%</strong> (uncalibrated)</span>
                        )}
                      </div>
                    </div>

                    {/* Status Badge */}
                    <div>
                      {edge.latestReview === 'plausible' && (
                        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700 border border-emerald-200">
                          <CheckCircle2 className="h-3 w-3 text-emerald-600" />
                          Seems Plausible
                        </span>
                      )}
                      {edge.latestReview === 'not_plausible' && (
                        <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2.5 py-1 text-xs font-semibold text-rose-700 border border-rose-200">
                          <XCircle className="h-3 w-3 text-rose-600" />
                          Seems Incorrect
                        </span>
                      )}
                      {edge.latestReview === 'uncertain' && (
                        <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-700 border border-amber-200">
                          <HelpCircle className="h-3 w-3 text-amber-600" />
                          Unsure
                        </span>
                      )}
                      {!edge.latestReview && (
                        <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600 border border-slate-200">
                          <Clock className="h-3 w-3 text-slate-400" />
                          Awaiting Review
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Review Actions Row */}
                  <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 pt-2.5">
                    <span className="text-[11px] text-slate-500">
                      {hasReview ? 'Update assessment decision:' : 'Record human-in-the-loop verification:'}
                    </span>

                    <div className="flex items-center gap-1.5">
                      <button
                        type="button"
                        disabled={isSaving}
                        onClick={() => void onRecordReview(edge.id, 'plausible')}
                        className={`rounded-md px-2.5 py-1 text-xs font-semibold transition border ${
                          edge.latestReview === 'plausible'
                            ? 'bg-emerald-600 text-white border-emerald-600'
                            : 'border-slate-200 bg-white text-slate-700 hover:border-emerald-300 hover:bg-emerald-50 hover:text-emerald-800'
                        }`}
                      >
                        {isSaving ? '...' : 'Seems Plausible'}
                      </button>

                      <button
                        type="button"
                        disabled={isSaving}
                        onClick={() => void onRecordReview(edge.id, 'not_plausible')}
                        className={`rounded-md px-2.5 py-1 text-xs font-semibold transition border ${
                          edge.latestReview === 'not_plausible'
                            ? 'bg-rose-600 text-white border-rose-600'
                            : 'border-slate-200 bg-white text-slate-700 hover:border-rose-300 hover:bg-rose-50 hover:text-rose-800'
                        }`}
                      >
                        {isSaving ? '...' : 'Seems Incorrect'}
                      </button>

                      <button
                        type="button"
                        disabled={isSaving}
                        onClick={() => void onRecordReview(edge.id, 'uncertain')}
                        className={`rounded-md px-2.5 py-1 text-xs font-semibold transition border ${
                          edge.latestReview === 'uncertain'
                            ? 'bg-amber-600 text-white border-amber-600'
                            : 'border-slate-200 bg-white text-slate-700 hover:border-amber-300 hover:bg-amber-50 hover:text-amber-800'
                        }`}
                      >
                        {isSaving ? '...' : 'Unsure'}
                      </button>
                    </div>
                  </div>

                  {/* Audit Log Trail */}
                  {edge.reviews && edge.reviews.length > 0 && (
                    <div className="mt-2 text-[10px] text-slate-400 bg-slate-50 rounded p-1.5 border border-slate-100 flex items-center gap-2">
                      <span className="font-medium text-slate-500">Audit trail:</span>
                      <span>
                        Last updated {new Date(edge.reviews[edge.reviews.length - 1].created_at).toLocaleString()}
                        {' · '}
                        Status: <strong className="text-slate-700">{edge.reviews[edge.reviews.length - 1].review_status.replace('_', ' ')}</strong>
                      </span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Progressive Load */}
        {filteredEdges.length > visibleCount && (
          <div className="text-center pt-2">
            <button
              type="button"
              onClick={() => setVisibleCount((prev) => prev + PAGE_SIZE)}
              className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 shadow-2xs hover:bg-slate-50"
            >
              Show more candidates ({visibleCount} of {filteredEdges.length} shown)
              <ChevronDown className="h-3.5 w-3.5 text-slate-500" />
            </button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
