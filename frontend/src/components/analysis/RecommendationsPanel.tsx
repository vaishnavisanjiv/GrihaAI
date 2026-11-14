'use client';

import { ShieldCheck, Ruler, DoorOpen, Compass, Building, FileCheck } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';

interface RecommendationsPanelProps {
  recommendations?: string[];
  isCalibrated?: boolean;
}

export function RecommendationsPanel({
  recommendations,
  isCalibrated = false,
}: RecommendationsPanelProps) {
  const customRecommendations = recommendations || [];
  const defaultSteps = [
    {
      icon: Ruler,
      title: 'Drawing Scale & Dimensional Verification',
      desc: isCalibrated
        ? 'Scale factor is calibrated. Cross-verify critical wall lengths and clear passages against known site measurements.'
        : 'Drawing scale is uncalibrated. Calibrate a known dimension on the upload page before relying on metric calculations.',
      actionText: isCalibrated ? 'Verified' : 'Scale Required',
      isWarning: !isCalibrated,
    },
    {
      icon: Compass,
      title: 'Review Room Segmentation Boundaries',
      desc: 'Inspect detected polygonal room boundaries on the Spatial Board against architectural wall lines to ensure enclosed spaces are accurately parsed.',
      actionText: 'Visual Review',
      isWarning: false,
    },
    {
      icon: DoorOpen,
      title: 'Confirm Aperture & Clear Opening Dimensions',
      desc: 'Verify that door clear widths satisfy minimum exit egress requirements (typically ≥ 0.9m for interior doors, ≥ 1.0m for main exits).',
      actionText: 'Egress Check',
      isWarning: false,
    },
    {
      icon: FileCheck,
      title: 'Audit Spatial Adjacency Candidates',
      desc: 'Review potential geometric relationships in the Spatial Analysis table. Confirm real circulation pathways between living, kitchen, and sanitary spaces.',
      actionText: 'Review Candidates',
      isWarning: false,
    },
    {
      icon: Building,
      title: 'Confirm Municipal Jurisdiction & Bylaws',
      desc: 'Identify the applicable local development authority (e.g. municipal corporation DCR) and building classification to select relevant code editions.',
      actionText: 'Jurisdiction Check',
      isWarning: false,
    },
    {
      icon: ShieldCheck,
      title: 'Professional Architectural Validation',
      desc: 'Engage a certified architect or structural engineer to sign off on statutory compliance, fire resistance ratings, and local building permit requirements.',
      actionText: 'Professional Sign-off',
      isWarning: false,
    },
  ];

  return (
    <Card className="border-slate-200 bg-white shadow-xs">
      <CardHeader className="border-b border-slate-100 bg-slate-50/50 pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base font-bold text-slate-900">
              Recommended Next Steps & Verification Checklist
            </CardTitle>
            <p className="mt-0.5 text-xs text-slate-500">
              Actionable tasks to validate geometric screening and advance toward formal design compliance.
            </p>
          </div>
          <span className="rounded-full bg-cyan-50 px-2.5 py-0.5 text-xs font-semibold text-cyan-700 border border-cyan-200">
            6 Action Items
          </span>
        </div>
      </CardHeader>

      <CardContent className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {defaultSteps.map((step, idx) => {
            const Icon = step.icon;
            return (
              <div
                key={idx}
                className="flex items-start gap-3 rounded-xl border border-slate-200/90 bg-slate-50/60 p-3.5 transition hover:border-cyan-300 hover:bg-slate-50"
              >
                <div className={`mt-0.5 rounded-lg p-2 shrink-0 ${
                  step.isWarning ? 'bg-amber-100 text-amber-800' : 'bg-cyan-100 text-cyan-800'
                }`}>
                  <Icon className="h-4 w-4" />
                </div>
                <div className="space-y-1 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <h4 className="text-xs font-bold text-slate-900">{step.title}</h4>
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                      step.isWarning ? 'bg-amber-100 text-amber-800' : 'bg-slate-200/70 text-slate-700'
                    }`}>
                      {step.actionText}
                    </span>
                  </div>
                  <p className="text-xs leading-relaxed text-slate-600">
                    {step.desc}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {customRecommendations.length > 0 && (
          <div className="mt-3 rounded-lg bg-slate-50 p-3 border border-slate-200/80">
            <p className="text-[11px] font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Additional Screening Notes:
            </p>
            <ul className="space-y-1 text-xs text-slate-600">
              {customRecommendations.map((rec, i) => (
                <li key={i} className="flex items-start gap-1.5">
                  <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-cyan-600 shrink-0" />
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
