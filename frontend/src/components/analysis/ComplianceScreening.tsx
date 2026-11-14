'use client';

import { useState } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  AlertOctagon,
  AlertTriangle,
  Ruler,
  HelpCircle,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { ComplianceFinding } from './types';

interface ComplianceScreeningProps {
  findings: ComplianceFinding[];
  isCalibrated?: boolean;
  onOpenCalibration?: () => void;
}

interface CategoryMeta {
  title: string;
  clause: string;
  evidence: string;
  missing: string;
  verification: string;
}

const CATEGORY_META: Record<string, CategoryMeta> = {
  'corridor-clear-width': {
    title: 'Corridor & Passageway Clear Width',
    clause: 'NBC 2016 Part 3, Clause 4.8 / 12.8',
    evidence: 'Measured clear widths of internal corridors, entry zones, and transit passages.',
    missing: 'Secondary furniture encroachments and inward door swings.',
    verification: 'Minimum 1.00 m clear width for residential circulation and 1.25 m for main corridors.',
  },
  'wall-spacing-and-shafts': {
    title: 'Spacing Between Walls & Internal Shafts',
    clause: 'NBC 2016 Part 3, Clause 4.9 & 8.2',
    evidence: 'Detected wall element spans and internal enclosure separations.',
    missing: 'Fire dampers, structural shaft lining, and acoustic insulation.',
    verification: 'Minimum 1.00 m passage width and 1.20 m clear span for internal ventilation/light shafts.',
  },
  'habitable-room-dimensions': {
    title: 'Habitable Room Dimensions',
    clause: 'NBC 2016 Part 3, Clause 4.1',
    evidence: '2D metric bounding boxes & segmented floor-plan carpet area footprints.',
    missing: 'Ceiling clear height (minimum 2.75 m) and structural column projections.',
    verification: 'Minimum clear width 2.40 m and minimum carpet area 9.50 m² for habitable rooms.',
  },
  'kitchen-dimensions': {
    title: 'Kitchen Dimensions & Clearances',
    clause: 'NBC 2016 Part 3, Clause 4.2',
    evidence: 'Kitchen spatial outline and usable floor footprint.',
    missing: 'Clear counter aisle width and mechanical ventilation duct.',
    verification: 'Minimum floor area 4.50 m² and minimum clear width 1.80 m (NBC Clause 4.2).',
  },
  'sanitary-facility-dimensions': {
    title: 'Sanitary Facility Dimensions',
    clause: 'NBC 2016 Part 3, Clause 4.4',
    evidence: 'Bathroom & water closet footprint polygons and width measurements.',
    missing: 'Plumbing fixture setbacks, water-seal trap depth, and vent pipe clearance.',
    verification: 'Minimum bathroom area 1.80 m² (width ≥ 1.20 m) and WC area 1.10 m² (width ≥ 0.90 m).',
  },
  'door-clear-width': {
    title: 'Doorway Clear Opening Width',
    clause: 'NBC 2016 Part 3, Clause 4.7 / 12.7',
    evidence: 'Door opening aperture predictions and detected leaf widths.',
    missing: 'Physical frame rebate deductions and emergency egress hardware.',
    verification: 'Main exit door ≥ 1.00 m, habitable rooms ≥ 0.90 m, bathroom/WC doors ≥ 0.75 m.',
  },
  'stair-and-exit-dimensions': {
    title: 'Stair & Egress Dimensions',
    clause: 'NBC 2016 Part 3, Clause 4.9',
    evidence: 'Circulation and stair footprint indicators.',
    missing: 'Riser height (max 190 mm), tread depth (min 250 mm), and handrail clearances.',
    verification: 'Minimum clear stair width 1.00 m for residential occupancy.',
  },
  'ventilation-and-daylight': {
    title: 'Ventilation & Glazing Aperture',
    clause: 'NBC 2016 Part 3, Clause 4.10',
    evidence: 'Window opening segmentations in exterior perimeter walls.',
    missing: 'Effective openable percentage, lintel heights, and exterior setbacks.',
    verification: 'Aggregate glazed opening area must be at least 10% (1/10th) of habitable floor area.',
  },
  'accessible-route-and-clearances': {
    title: 'Accessible Routes & Clearances',
    clause: 'NBC 2016 Part 3, Annex B',
    evidence: 'Hallway continuity and transit threshold clearances.',
    missing: 'Ramp slopes, step thresholds, turning circle diameter (1500 mm), and tactile paving.',
    verification: 'Continuous unobstructed clear route of at least 0.90 m – 1.00 m.',
  },
  'site-and-building-context': {
    title: 'Site & Building Context',
    clause: 'NBC 2016 Part 3, Section 3',
    evidence: 'Internal floor plan layout drawing.',
    missing: 'Plot boundary, exterior setbacks, road width, and floor-space index (FSI/FAR).',
    verification: 'Cross-reference municipal master plan, plot boundaries, and zoning bylaws.',
  },
  'governing-code-selection': {
    title: 'Governing Building Code',
    clause: 'NBC 2016 Part 3 & 4',
    evidence: 'National Building Code of India (NBC 2016) Residential Group A-4.',
    missing: 'Local municipal corporation amendments (e.g. BMC, BBMP, PMRDA, DDA).',
    verification: 'Confirm applicable local development control regulations (DCR) and amendments.',
  },
};

export function ComplianceScreening({
  findings,
  isCalibrated = false,
  onOpenCalibration,
}: ComplianceScreeningProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  const passCount = findings.filter((f) => f.status === 'PASS').length;
  const failCount = findings.filter((f) => f.status === 'FAIL').length;
  const warnCount = findings.filter((f) => f.status === 'WARNING').length;

  return (
    <Card className="border-slate-200 bg-white shadow-xs">
      <CardHeader className="border-b border-slate-100 bg-slate-50/50 pb-3">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
              NBC 2016 Architectural Compliance Screening
              {isCalibrated && (
                <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[11px] font-semibold text-emerald-800">
                  Calibrated Metres
                </span>
              )}
            </CardTitle>
            <p className="mt-0.5 text-xs text-slate-500">
              Evaluated against National Building Code of India (NBC 2016) Part 3 (General Building Requirements) & Part 4 (Fire Safety).
            </p>
          </div>

          {/* Header Status Badge */}
          {isCalibrated ? (
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-800 border border-emerald-200">
                <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
                {passCount} Passed · {failCount} Violations · {warnCount} Warnings
              </span>
              {onOpenCalibration && (
                <button
                  type="button"
                  onClick={onOpenCalibration}
                  className="inline-flex items-center gap-1 rounded-lg border border-slate-300 bg-white px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition shadow-2xs"
                >
                  <Ruler className="h-3.5 w-3.5 text-slate-500" />
                  Adjust Scale
                </button>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-800 border border-amber-200">
                <ShieldAlert className="h-3.5 w-3.5 text-amber-600" />
                Scale Calibration Required
              </span>
              {onOpenCalibration && (
                <button
                  type="button"
                  onClick={onOpenCalibration}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-cyan-600 px-3 py-1 text-xs font-semibold text-white hover:bg-cyan-700 transition shadow-xs"
                >
                  <Ruler className="h-3.5 w-3.5" />
                  Calibrate Scale Now
                </button>
              )}
            </div>
          )}
        </div>

        {/* Dynamic Context Banner */}
        <div
          className={`mt-2.5 rounded-lg border p-3 text-xs leading-relaxed ${
            isCalibrated
              ? 'border-emerald-200 bg-emerald-50/60 text-emerald-950'
              : 'border-amber-200 bg-amber-50/70 text-amber-950'
          }`}
        >
          {isCalibrated ? (
            <p>
              <strong>Active Statutory Assessment:</strong> Dimensions, corridor widths, and wall clearances have been mapped from drawing pixels to real-world metres ($m$). Findings reflect exact geometric measurements checked against NBC 2016 norms.
            </p>
          ) : (
            <p>
              <strong>Drawing Scale Uncalibrated:</strong> The system has segmented all rooms, doors, and walls in pixels. Click <strong>Calibrate Scale Now</strong> above (or select standard door = 1.0 m) to instantly compute real corridor widths and room carpet areas against NBC 2016 norms.
            </p>
          )}
        </div>
      </CardHeader>

      <CardContent className="p-4">
        <div className="overflow-x-auto rounded-xl border border-slate-200">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-slate-200 bg-slate-50 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-3.5 py-2.5">NBC Provision / Category</th>
                <th className="px-3.5 py-2.5">Statutory Standard</th>
                <th className="px-3.5 py-2.5">Compliance Verdict</th>
                <th className="px-3.5 py-2.5">Measured Observation</th>
                <th className="px-3.5 py-2.5 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {findings.map((rule) => {
                const normId = rule.rule_id.toLowerCase().replace(/_/g, '-');
                const meta = CATEGORY_META[normId] || {
                  title: rule.rule_id.replace(/[-_]/g, ' ').toUpperCase(),
                  clause: 'NBC 2016 Part 3',
                  evidence: 'Preliminary 2D floor plan layout detections.',
                  missing: 'Statutory verification against local municipal code.',
                  verification: 'Verify with qualified architect.',
                };
                const isExpanded = expandedId === rule.rule_id;

                const statusUpper = (rule.status || '').toUpperCase();
                const isPass = statusUpper === 'PASS';
                const isFail = statusUpper === 'FAIL';
                const isWarn = statusUpper === 'WARNING';

                return (
                  <tr key={rule.id} className="group hover:bg-slate-50/80 transition-colors">
                    <td colSpan={5} className="p-0">
                      {/* Main Table Row */}
                      <div
                        onClick={() => toggleExpand(rule.rule_id)}
                        className="grid grid-cols-[1.6fr_1.6fr_1.1fr_2.4fr_40px] items-center px-3.5 py-3 cursor-pointer"
                      >
                        {/* 1. Category */}
                        <div className="pr-2">
                          <div className="font-semibold text-slate-900">{meta.title}</div>
                          <div className="text-[10px] font-mono text-slate-400 mt-0.5">{meta.clause}</div>
                        </div>

                        {/* 2. Statutory Standard */}
                        <div className="text-slate-600 text-xs pr-2">
                          {meta.verification}
                        </div>

                        {/* 3. Status Badge */}
                        <div>
                          {isPass && (
                            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-[11px] font-bold text-emerald-700 border border-emerald-200">
                              <CheckCircle2 className="h-3 w-3 text-emerald-600 shrink-0" />
                              PASS
                            </span>
                          )}
                          {isFail && (
                            <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2.5 py-1 text-[11px] font-bold text-rose-700 border border-rose-200">
                              <AlertOctagon className="h-3 w-3 text-rose-600 shrink-0" />
                              FAIL
                            </span>
                          )}
                          {isWarn && (
                            <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-1 text-[11px] font-bold text-amber-700 border border-amber-200">
                              <AlertTriangle className="h-3 w-3 text-amber-600 shrink-0" />
                              WARNING
                            </span>
                          )}
                          {!isPass && !isFail && !isWarn && (
                            <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600 border border-slate-200">
                              <HelpCircle className="h-3 w-3 text-slate-400 shrink-0" />
                              {rule.status}
                            </span>
                          )}
                        </div>

                        {/* 4. Measured Observation */}
                        <div className="text-slate-700 text-xs pr-2 truncate">
                          {rule.message || meta.evidence}
                        </div>

                        {/* 5. Expand Icon */}
                        <div className="text-right text-slate-400">
                          {isExpanded ? (
                            <ChevronUp className="h-4 w-4 inline" />
                          ) : (
                            <ChevronDown className="h-4 w-4 inline" />
                          )}
                        </div>
                      </div>

                      {/* Expandable Details Drawer */}
                      {isExpanded && (
                        <div className="border-t border-slate-100 bg-slate-50/90 px-4 py-3 text-xs space-y-2.5 animate-in fade-in duration-150">
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                            <div className="rounded-lg bg-white p-3 border border-slate-200">
                              <p className="font-semibold text-slate-800 text-[11px] uppercase tracking-wider">
                                Measured Finding
                              </p>
                              <p className="mt-1 text-slate-700 leading-relaxed">
                                {rule.message || 'Observation recorded.'}
                              </p>
                              {rule.explanation && (
                                <p className="mt-2 text-[11px] text-slate-500 border-t border-slate-100 pt-1.5">
                                  {rule.explanation}
                                </p>
                              )}
                            </div>

                            <div className="rounded-lg bg-white p-3 border border-slate-200">
                              <p className="font-semibold text-cyan-800 text-[11px] uppercase tracking-wider">
                                Statutory NBC Provision
                              </p>
                              <p className="mt-1 text-slate-700 font-medium">
                                {meta.clause}
                              </p>
                              <p className="mt-1 text-slate-600">
                                {meta.verification}
                              </p>
                            </div>

                            <div className="rounded-lg bg-white p-3 border border-slate-200">
                              <p className="font-semibold text-emerald-800 text-[11px] uppercase tracking-wider">
                                Architectural Action
                              </p>
                              <p className="mt-1 text-slate-600">
                                {rule.recommendation || meta.verification}
                              </p>
                            </div>
                          </div>
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
