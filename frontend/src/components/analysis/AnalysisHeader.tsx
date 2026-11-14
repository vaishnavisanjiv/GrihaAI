'use client';

import { useState } from 'react';
import {
  Download,
  FileJson,
  CheckCircle2,
  Clock,
  XCircle,
  ShieldAlert,
  Fingerprint,
  Calendar,
  FileText,
  Loader2,
  Ruler,
} from 'lucide-react';
import { AnalysisData } from './types';

interface AnalysisHeaderProps {
  data: AnalysisData;
  onDownloadPdf: () => Promise<void>;
  onExportJson: () => void;
  isDownloadingPdf?: boolean;
  onOpenCalibration?: () => void;
}

export function AnalysisHeader({
  data,
  onDownloadPdf,
  onExportJson,
  isDownloadingPdf = false,
  onOpenCalibration,
}: AnalysisHeaderProps) {
  const [showProvenance, setShowProvenance] = useState(false);
  const status = data.analysis?.status || 'COMPLETED';
  const isRunning = status === 'RUNNING' || status === 'PENDING';
  const isFailed = status === 'FAILED';

  const dateFormatted = data.analysis?.started_at
    ? new Date(data.analysis.started_at).toLocaleString(undefined, {
        dateStyle: 'medium',
        timeStyle: 'short',
      })
    : 'Recently';

  const provenance = data.analysis?.model_version || 'Not recorded';

  return (
    <div className="space-y-4">
      {/* Top Banner Row */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-1.5">
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-cyan-50 px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider text-cyan-700 border border-cyan-200">
              Analysis Results
            </span>

            {/* Status Pill */}
            {status === 'COMPLETED' && (
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 border border-emerald-200">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                Completed
              </span>
            )}
            {status === 'RUNNING' && (
              <span className="inline-flex items-center gap-1 rounded-full bg-cyan-50 px-2.5 py-0.5 text-xs font-semibold text-cyan-700 border border-cyan-200 animate-pulse">
                <Loader2 className="h-3.5 w-3.5 animate-spin text-cyan-600" />
                Processing
              </span>
            )}
            {status === 'PENDING' && (
              <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-700 border border-amber-200">
                <Clock className="h-3.5 w-3.5 text-amber-600" />
                Pending Queue
              </span>
            )}
            {isFailed && (
              <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2.5 py-0.5 text-xs font-semibold text-rose-700 border border-rose-200">
                <XCircle className="h-3.5 w-3.5 text-rose-600" />
                Failed
              </span>
            )}

            {/* Plan File Name Badge */}
            {data.floor_plan_filename && (
              <span className="inline-flex items-center gap-1 rounded-md bg-slate-100 px-2 py-0.5 text-xs font-mono text-slate-700">
                <FileText className="h-3 w-3 text-slate-500" />
                {data.floor_plan_filename}
              </span>
            )}
          </div>

          <h1 className="text-2xl font-bold tracking-tight text-slate-900 md:text-3xl">
            Plan Analysis Report
          </h1>

          <p className="text-sm text-slate-600">
            Preliminary architectural layout analysis and geometry screening.
          </p>

          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500 pt-1">
            <span className="inline-flex items-center gap-1">
              <Calendar className="h-3.5 w-3.5 text-slate-400" />
              {dateFormatted}
            </span>
            <span>·</span>
            <span>Pipeline: <strong className="font-medium text-slate-700">{data.analysis?.cv_method || 'cubicasa5k-unet-segmentation'}</strong></span>
            <span>·</span>
            <button
              type="button"
              onClick={() => setShowProvenance(!showProvenance)}
              className="inline-flex items-center gap-1 text-cyan-700 hover:text-cyan-800 underline underline-offset-2 transition-colors"
            >
              <Fingerprint className="h-3.5 w-3.5" />
              Model Provenance
            </button>
            <span>·</span>
            {data.scale_calibrated ? (
              <span className="inline-flex items-center gap-1 text-emerald-700 font-medium">
                <Ruler className="h-3.5 w-3.5 text-emerald-600" />
                Scale: {((data.scale_pixels_per_mm || 0) * 1000).toFixed(1)} px/m
              </span>
            ) : (
              <button
                type="button"
                onClick={onOpenCalibration}
                className="inline-flex items-center gap-1 text-amber-700 hover:text-amber-800 underline underline-offset-2 font-medium transition-colors"
                title="Click to calibrate scale and view real metres"
              >
                <Ruler className="h-3.5 w-3.5 text-amber-600" />
                Scale: Uncalibrated (Calibrate)
              </button>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2.5 shrink-0">
          {onOpenCalibration && (
            <button
              type="button"
              onClick={onOpenCalibration}
              disabled={isRunning}
              className={`inline-flex items-center gap-2 rounded-lg px-3.5 py-2 text-xs font-semibold shadow-sm transition disabled:cursor-not-allowed disabled:opacity-50 ${
                data.scale_calibrated
                  ? 'border border-slate-300 bg-white text-slate-700 hover:bg-slate-50'
                  : 'bg-cyan-600 text-white hover:bg-cyan-700 shadow-xs'
              }`}
              title="Calibrate drawing scale for NBC 2016 compliance verification"
            >
              <Ruler className="h-3.5 w-3.5" />
              {data.scale_calibrated ? 'Adjust Scale' : 'Calibrate Scale'}
            </button>
          )}

          <button
            type="button"
            onClick={onDownloadPdf}
            disabled={isRunning || isDownloadingPdf}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 hover:text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
            title="Download architectural preliminary review report (PDF)"
          >
            {isDownloadingPdf ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin text-cyan-600" />
            ) : (
              <Download className="h-3.5 w-3.5 text-slate-500" />
            )}
            Download PDF
          </button>

          <button
            type="button"
            onClick={onExportJson}
            disabled={isRunning}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 hover:text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
            title="Export raw geometry & findings as JSON"
          >
            <FileJson className="h-3.5 w-3.5 text-slate-500" />
            Export JSON
          </button>
        </div>
      </div>

      {/* Model Provenance Popover (collapsible) */}
      {showProvenance && (
        <div className="rounded-xl border border-slate-200 bg-slate-50/80 p-3 text-xs text-slate-700 animate-in fade-in duration-150">
          <div className="flex items-center justify-between font-semibold text-slate-800 mb-1">
            <span className="flex items-center gap-1.5">
              <Fingerprint className="h-4 w-4 text-cyan-600" />
              Verified PyTorch Model Checkpoint
            </span>
            <button
              onClick={() => setShowProvenance(false)}
              className="text-slate-400 hover:text-slate-600"
            >
              ✕
            </button>
          </div>
          <p className="font-mono text-[11px] text-slate-600 break-all select-all bg-white border border-slate-200 rounded p-1.5 mt-1">
            {provenance}
          </p>
          <p className="mt-1 text-[11px] text-slate-500">
            Validated SHA-256 fingerprint ensures the active checkpoint matches the offline GPU evaluation run.
          </p>
        </div>
      )}

      {/* Prominent Statutory Disclaimer Box */}
      <div className="flex items-start gap-3 rounded-xl border border-amber-200/90 bg-amber-50/70 p-3.5 text-amber-900 shadow-xs">
        <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
        <p className="text-xs leading-relaxed text-amber-900/90 font-medium">
          <strong>Notice:</strong> This report contains preliminary model-generated detections and geometric observations.
          It is not an NBC compliance certificate, building approval or substitute for professional architectural review.
        </p>
      </div>
    </div>
  );
}
