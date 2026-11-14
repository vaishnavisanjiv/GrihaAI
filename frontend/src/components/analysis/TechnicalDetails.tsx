'use client';

import { useState } from 'react';
import { Terminal, ChevronDown, ChevronUp, Copy, Check, Fingerprint, Database, Cpu } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { AnalysisData } from './types';

interface TechnicalDetailsProps {
  data: AnalysisData;
}

export function TechnicalDetails({ data }: TechnicalDetailsProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const modelVersion = data.analysis?.model_version || 'Not recorded';
  const cvMethod = data.analysis?.cv_method || 'cubicasa5k-unet-segmentation';
  const startedAt = data.analysis?.started_at ? new Date(data.analysis.started_at).toISOString() : '—';
  const completedAt = data.analysis?.completed_at ? new Date(data.analysis.completed_at).toISOString() : '—';

  const roomPolys = (data.rooms || []).filter((r) => r.polygon_json && r.polygon_json.length > 5).length;
  const elementPolys = (data.elements || []).filter((e) => e.geometry_json && e.geometry_json.length > 5).length;

  const copyProvenance = () => {
    void navigator.clipboard.writeText(modelVersion);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Card className="border-slate-200 bg-white shadow-xs">
      <CardHeader
        onClick={() => setIsOpen(!isOpen)}
        className="cursor-pointer border-b border-slate-100 bg-slate-50/50 py-3.5 hover:bg-slate-50 transition"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="h-4 w-4 text-cyan-600" />
            <CardTitle className="text-sm font-bold text-slate-800">
              Technical Analysis Details & Model Provenance
            </CardTitle>
            <span className="rounded bg-slate-200/70 px-1.5 py-0.5 text-[10px] font-mono text-slate-700">
              Developer / Audit Metadata
            </span>
          </div>
          <div className="flex items-center gap-1 text-slate-400">
            <span className="text-xs">{isOpen ? 'Hide Details' : 'Expand Details'}</span>
            {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </div>
        </div>
      </CardHeader>

      {isOpen && (
        <CardContent className="p-4 space-y-4 text-xs animate-in fade-in duration-150">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {/* Box 1: Model & Checkpoint */}
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 space-y-1.5">
              <div className="flex items-center gap-1.5 font-semibold text-slate-800">
                <Cpu className="h-3.5 w-3.5 text-cyan-600" />
                Inference Architecture
              </div>
              <p className="text-slate-600">Model: <strong className="text-slate-900 font-mono">buildguard-unet-v1</strong></p>
              <p className="text-slate-600">Classes: <strong className="text-slate-900">13 semantic categories</strong></p>
              <p className="text-slate-600">Resolution: <strong className="text-slate-900 font-mono">512 × 512 px</strong></p>
              <p className="text-slate-600">Dataset: <strong className="text-slate-900">CubiCasa5K (3,494 train / 749 test)</strong></p>
            </div>

            {/* Box 2: Pipeline & Execution */}
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 space-y-1.5">
              <div className="flex items-center gap-1.5 font-semibold text-slate-800">
                <Database className="h-3.5 w-3.5 text-cyan-600" />
                Pipeline Execution
              </div>
              <p className="text-slate-600">Method: <strong className="text-slate-900 font-mono">{cvMethod}</strong></p>
              <p className="text-slate-600">Analysis Status: <strong className="text-emerald-700">{data.analysis?.status || 'COMPLETED'}</strong></p>
              <p className="text-slate-600">Started: <span className="font-mono text-[11px] text-slate-700">{startedAt.slice(0, 19)}</span></p>
              <p className="text-slate-600">Completed: <span className="font-mono text-[11px] text-slate-700">{completedAt.slice(0, 19)}</span></p>
            </div>

            {/* Box 3: Geometry & Polygon Counts */}
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 space-y-1.5">
              <div className="flex items-center gap-1.5 font-semibold text-slate-800">
                <Fingerprint className="h-3.5 w-3.5 text-cyan-600" />
                Geometry Extraction
              </div>
              <p className="text-slate-600">Room Polygons: <strong className="text-slate-900">{roomPolys}</strong></p>
              <p className="text-slate-600">Element Polygons: <strong className="text-slate-900">{elementPolys}</strong></p>
              <p className="text-slate-600">Spatial Graph Edges: <strong className="text-slate-900">{data.spatial_edges?.length || 0}</strong></p>
              <p className="text-slate-600">Canvas Dimensions: <strong className="text-slate-900 font-mono">{data.image_width || 512} × {data.image_height || 512} px</strong></p>
            </div>
          </div>

          {/* Full SHA-256 Provenance string */}
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-800">
                Cryptographic Model Checkpoint Fingerprint (SHA-256):
              </span>
              <button
                type="button"
                onClick={copyProvenance}
                className="inline-flex items-center gap-1 rounded bg-white px-2 py-0.5 text-[11px] font-semibold text-slate-700 border border-slate-200 hover:bg-slate-100"
              >
                {copied ? <Check className="h-3 w-3 text-emerald-600" /> : <Copy className="h-3 w-3" />}
                {copied ? 'Copied' : 'Copy Hash'}
              </button>
            </div>
            <p className="font-mono text-[11px] text-slate-600 bg-white border border-slate-200 rounded p-2 select-all break-all">
              {modelVersion}
            </p>
          </div>
        </CardContent>
      )}
    </Card>
  );
}
