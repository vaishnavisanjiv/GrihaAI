'use client';

import { useState } from 'react';
import { BellRing, ShieldCheck, SlidersHorizontal, Sparkles } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

const settingsGroups = [
  {
    title: 'Workspace preferences',
    icon: SlidersHorizontal,
    items: ['Default compliance profile', 'Notification thresholds', 'Regional code presets'],
  },
  {
    title: 'Security',
    icon: ShieldCheck,
    items: ['JWT session status', 'Two-factor readiness', 'Password change policy'],
  },
  {
    title: 'Automation',
    icon: Sparkles,
    items: ['Auto-run checks on upload', 'AI summary generation', 'CSV export preferences'],
  },
];

export default function SettingsPage() {
  const [preferences, setPreferences] = useState({
    autoRun: true,
    emailAlerts: true,
    exportCsv: false,
    highRiskThreshold: 'Medium',
  });

  const updatePreference = (key: keyof typeof preferences, value: boolean | string) => {
    setPreferences((current) => ({ ...current, [key]: value }));
  };

  return (
    <div className="space-y-6 p-6 md:p-8">
      <div>
        <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-600">Settings</p>
        <h1 className="mt-2 text-3xl font-bold text-slate-900">Workspace controls</h1>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {settingsGroups.map(({ title, icon: Icon, items }) => (
          <Card key={title} className="border-slate-200 bg-white">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-slate-900">
                <Icon className="h-5 w-5 text-cyan-600" />
                {title}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {items.map((item) => (
                <div key={item} className="rounded-xl bg-slate-50 px-3 py-2 text-sm text-slate-700">
                  {item}
                </div>
              ))}
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="border-slate-200 bg-white">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-slate-900">
            <BellRing className="h-5 w-5 text-cyan-600" />
            Alert center
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-lg font-semibold text-slate-800">Notification preferences</p>
              <p className="text-sm text-slate-600">Receive review updates, threshold alerts, and summary digests by email.</p>
            </div>
            <Button variant="outline">Update notifications</Button>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <label className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
              <span>Auto-run compliance checks on upload</span>
              <input
                type="checkbox"
                checked={preferences.autoRun}
                onChange={(e) => updatePreference('autoRun', e.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-cyan-600 focus:ring-cyan-500"
              />
            </label>

            <label className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
              <span>Email alert digest</span>
              <input
                type="checkbox"
                checked={preferences.emailAlerts}
                onChange={(e) => updatePreference('emailAlerts', e.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-cyan-600 focus:ring-cyan-500"
              />
            </label>

            <label className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
              <span>CSV export preference</span>
              <input
                type="checkbox"
                checked={preferences.exportCsv}
                onChange={(e) => updatePreference('exportCsv', e.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-cyan-600 focus:ring-cyan-500"
              />
            </label>

            <label className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
              <span>High-risk threshold</span>
              <select
                value={preferences.highRiskThreshold}
                onChange={(e) => updatePreference('highRiskThreshold', e.target.value)}
                className="rounded-md border border-slate-200 bg-white px-2 py-1 text-sm text-slate-700"
              >
                <option value="Low">Low</option>
                <option value="Medium">Medium</option>
                <option value="High">High</option>
              </select>
            </label>
          </div>

          <div className="flex justify-end">
            <Button variant="primary">Save settings</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
