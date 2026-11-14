'use client';

import { useMemo } from 'react';
import { Home, Layers, GitFork, ShieldAlert, ShieldCheck, Sparkles } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/Card';
import { AnalysisData } from './types';

interface ExecutiveSummaryProps {
  data: AnalysisData;
}

export function ExecutiveSummary({ data }: ExecutiveSummaryProps) {
  const roomCount = data.rooms?.length || 0;
  const elementCount = data.elements?.length || 0;
  const edges = useMemo(() => data.spatial_edges || [], [data.spatial_edges]);
  const edgeCount = edges.length;

  const reviewedEdgeCount = useMemo(() => {
    return edges.filter((e) => e.reviews && e.reviews.length > 0).length;
  }, [edges]);

  const unreviewedEdgeCount = edgeCount - reviewedEdgeCount;
  const complianceResults = useMemo(
    () => data.compliance_results || [],
    [data.compliance_results],
  );

  const isCalibrated = Boolean(
    data.scale_calibrated || data.rooms?.some((r) => r.area_sqm != null),
  );

  const passCount = useMemo(
    () => complianceResults.filter((f) => f.status === 'PASS').length,
    [complianceResults],
  );
  const failCount = useMemo(
    () => complianceResults.filter((f) => f.status === 'FAIL').length,
    [complianceResults],
  );
  const warnCount = useMemo(
    () => complianceResults.filter((f) => f.status === 'WARNING').length,
    [complianceResults],
  );

  // Breakdown metrics
  const uniqueRoomCategories = useMemo(() => {
    const set = new Set(data.rooms?.map((r) => r.label || 'Other room'));
    return set.size;
  }, [data.rooms]);

  const elementTypes = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const el of data.elements || []) {
      const t = el.element_type || 'element';
      counts[t] = (counts[t] || 0) + 1;
    }
    return counts;
  }, [data.elements]);

  // Construct accurate dynamic narrative
  const dynamicSummary = useMemo(() => {
    const parts: string[] = [];
    parts.push(
      `The system identified ${roomCount} room region${roomCount === 1 ? '' : 's'} across ${uniqueRoomCategories} functional space categories`,
    );

    if (elementCount > 0) {
      const elDetails = Object.entries(elementTypes)
        .map(([k, v]) => `${v} ${k}${v === 1 ? '' : 's'}`)
        .join(', ');
      parts.push(
        `and ${elementCount} architectural element${elementCount === 1 ? '' : 's'} (${elDetails}) in the uploaded floor plan.`,
      );
    } else {
      parts.push('in the uploaded floor plan.');
    }

    if (edgeCount > 0) {
      parts.push(
        `${edgeCount} spatial relationship candidates were generated for review (${reviewedEdgeCount} reviewed, ${unreviewedEdgeCount} pending).`,
      );
    }

    if (isCalibrated) {
      parts.push(
        `Drawing scale is calibrated (${((data.scale_pixels_per_mm || 0) * 1000).toFixed(1)} px/m). Geometry was evaluated against National Building Code of India (NBC 2016) Part 3 & 4: ${passCount} provisions compliant, ${failCount} action items / violations detected.`,
      );
    } else {
      parts.push(
        'Building-code compliance is in uncalibrated screening mode. Calibrate scale to evaluate corridor clear widths and room carpet areas against statutory NBC 2016 provisions.',
      );
    }

    return parts.join(' ');
  }, [
    roomCount,
    uniqueRoomCategories,
    elementCount,
    elementTypes,
    edgeCount,
    reviewedEdgeCount,
    unreviewedEdgeCount,
    isCalibrated,
    data.scale_pixels_per_mm,
    passCount,
    failCount,
  ]);

  return (
    <div className="space-y-4">
      {/* 4 Executive Metric Cards */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {/* Card 1: Detected Rooms */}
        <Card className="border-slate-200/90 bg-white shadow-xs transition hover:border-cyan-300">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Detected Rooms
              </span>
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-50 text-cyan-700">
                <Home className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-900">{roomCount}</span>
              <span className="text-xs text-slate-500 font-medium">regions</span>
            </div>
            <p className="mt-1 text-xs text-slate-500">
              <strong className="font-semibold text-slate-700">{uniqueRoomCategories}</strong> functional categories identified
            </p>
          </CardContent>
        </Card>

        {/* Card 2: Detected Elements */}
        <Card className="border-slate-200/90 bg-white shadow-xs transition hover:border-emerald-300">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Detected Elements
              </span>
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50 text-emerald-700">
                <Layers className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-900">{elementCount}</span>
              <span className="text-xs text-slate-500 font-medium">elements</span>
            </div>
            <p className="mt-1 text-xs text-slate-500 truncate">
              {elementTypes.door || 0} doors · {elementTypes.window || 0} windows · {elementTypes.wall || 0} walls
            </p>
          </CardContent>
        </Card>

        {/* Card 3: Spatial Relationship Candidates */}
        <Card className="border-slate-200/90 bg-white shadow-xs transition hover:border-indigo-300">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Spatial Candidates
              </span>
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-50 text-indigo-700">
                <GitFork className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-900">{edgeCount}</span>
              <span className="text-xs text-slate-500 font-medium">candidates</span>
            </div>
            <p className="mt-1 text-xs text-slate-500">
              <strong className="font-semibold text-emerald-600">{reviewedEdgeCount}</strong> reviewed ·{' '}
              <strong className="font-semibold text-amber-600">{unreviewedEdgeCount}</strong> pending
            </p>
          </CardContent>
        </Card>

        {/* Card 4: Code Assessment Status */}
        <Card
          className={`border bg-white shadow-xs transition ${
            isCalibrated ? 'border-emerald-300/80 hover:border-emerald-400' : 'border-slate-200/90 hover:border-slate-300'
          }`}
        >
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                NBC 2016 Compliance
              </span>
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-lg ${
                  isCalibrated ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600'
                }`}
              >
                {isCalibrated ? <ShieldCheck className="h-4 w-4" /> : <ShieldAlert className="h-4 w-4" />}
              </div>
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-900">
                {isCalibrated ? `${passCount} / ${complianceResults.length}` : complianceResults.length}
              </span>
              <span
                className={`text-xs font-bold px-1.5 py-0.5 rounded ${
                  isCalibrated
                    ? 'text-emerald-700 bg-emerald-100/80'
                    : 'text-amber-700 bg-amber-100/70'
                }`}
              >
                {isCalibrated ? 'EVALUATED' : 'SCALE REQUIRED'}
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-500 truncate">
              {isCalibrated
                ? `${failCount} violation(s) · ${warnCount} warning(s)`
                : 'Calibrate scale to assess NBC norms'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Dynamic Plain-Language Executive Summary */}
      <div className="rounded-xl border border-slate-200/80 bg-slate-50/70 p-4 shadow-2xs">
        <div className="flex items-start gap-2.5">
          <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-cyan-600" />
          <div className="space-y-1">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-700">
              Executive Screening Summary
            </h2>
            <p className="text-xs leading-relaxed text-slate-600">
              {dynamicSummary}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
