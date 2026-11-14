'use client';

import { useState, useMemo } from 'react';
import { MapPin, Info, Search } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { AnalysisElement } from './types';
import { getClassDefForElementType } from './colors';

interface ElementDetectionProps {
  elements: AnalysisElement[];
  selectedElementId?: number | null;
  onSelectElement?: (id: number | null) => void;
}

export function ElementDetection({
  elements,
  selectedElementId,
  onSelectElement,
}: ElementDetectionProps) {
  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Extract unique element types
  const types = useMemo(() => {
    const set = new Set<string>();
    elements.forEach((e) => {
      if (e.element_type) set.add(e.element_type);
    });
    return ['ALL', ...Array.from(set).sort()];
  }, [elements]);

  // Counts per type
  const countsByType = useMemo(() => {
    const map: Record<string, number> = {};
    elements.forEach((e) => {
      const t = e.element_type || 'other';
      map[t] = (map[t] || 0) + 1;
    });
    return map;
  }, [elements]);

  const filteredElements = useMemo(() => {
    return elements.filter((el) => {
      const type = el.element_type || 'element';
      const label = el.label || type;
      const matchesType = typeFilter === 'ALL' || type === typeFilter;
      const matchesQuery =
        label.toLowerCase().includes(searchQuery.toLowerCase()) ||
        String(el.id).includes(searchQuery);
      return matchesType && matchesQuery;
    });
  }, [elements, typeFilter, searchQuery]);

  return (
    <Card className="border-slate-200 bg-white shadow-xs">
      <CardHeader className="border-b border-slate-100 bg-slate-50/50 pb-3">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <CardTitle className="text-base font-bold text-slate-900">
              Detected Architectural Elements — {elements.length} Items
            </CardTitle>
            <p className="mt-0.5 text-xs text-slate-500">
              Structural and aperture elements extracted from 2D pixel segmentation.
            </p>
          </div>

          {/* Quick counts pills */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs">
            {Object.entries(countsByType).map(([t, count]) => {
              const def = getClassDefForElementType(t);
              return (
                <span
                  key={t}
                  className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-medium border border-slate-200 ${def.badgeBg} ${def.badgeText}`}
                >
                  <span className="capitalize">{t}s</span>: <strong>{count}</strong>
                </span>
              );
            })}
          </div>
        </div>

        {/* Uncalibrated Score Notice */}
        <div className="mt-2 flex items-start gap-2 rounded-lg border border-slate-200/80 bg-slate-50 p-2 text-xs text-slate-600">
          <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-cyan-600" />
          <span>
            <strong>Detection Score Notice:</strong> Element scores are uncalibrated mean max-softmax outputs.
            They indicate segmentation activation strength and should not be interpreted as validated probabilities.
          </span>
        </div>

        {/* Filter and Search Bar */}
        <div className="mt-3 flex flex-wrap items-center gap-2 pt-1">
          {/* Category tabs */}
          <div className="flex flex-wrap items-center gap-1">
            {types.map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setTypeFilter(t)}
                className={`rounded-md px-2.5 py-1 text-xs font-semibold capitalize transition ${
                  typeFilter === t
                    ? 'bg-slate-900 text-white shadow-xs'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {t === 'ALL' ? 'All Elements' : `${t}s (${countsByType[t] || 0})`}
              </button>
            ))}
          </div>

          <div className="relative ml-auto min-w-[160px]">
            <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search elements..."
              className="w-full rounded-md border border-slate-200 bg-white py-1 pl-8 pr-2.5 text-xs text-slate-800 outline-none focus:border-cyan-500"
            />
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-4">
        {filteredElements.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-6 text-center text-xs text-slate-500">
            No architectural elements match the filter criteria.
          </div>
        ) : (
          <div className="max-h-[380px] overflow-y-auto rounded-xl border border-slate-200">
            <table className="w-full text-left text-xs">
              <thead className="sticky top-0 z-10 border-b border-slate-200 bg-slate-50 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-3 py-2.5">Element ID</th>
                  <th className="px-3 py-2.5">Type</th>
                  <th className="px-3 py-2.5">Detection Score</th>
                  <th className="px-3 py-2.5">Vector Geometry</th>
                  <th className="px-3 py-2.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {filteredElements.map((el) => {
                  const def = getClassDefForElementType(el.element_type);
                  const isSelected = selectedElementId === el.id;
                  const scorePct = el.confidence != null ? Math.round(el.confidence * 100) : null;
                  const hasGeom = Boolean(el.geometry_json && el.geometry_json.length > 10);

                  return (
                    <tr
                      key={el.id}
                      onClick={() => onSelectElement?.(isSelected ? null : el.id)}
                      className={`hover:bg-slate-50 cursor-pointer ${isSelected ? 'bg-cyan-50/60' : ''}`}
                    >
                      <td className="px-3 py-2 font-mono text-slate-500">#{el.id}</td>
                      <td className="px-3 py-2">
                        <span className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${def.badgeBg} ${def.badgeText}`}>
                          <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: def.fill }} />
                          {el.label || el.element_type}
                        </span>
                      </td>
                      <td className="px-3 py-2 font-mono text-slate-700 font-medium">
                        {scorePct != null ? `${scorePct}%` : '—'}
                      </td>
                      <td className="px-3 py-2 text-slate-500 text-[11px]">
                        {hasGeom ? (
                          <span className="text-emerald-700 font-medium">Available (Polygon)</span>
                        ) : (
                          <span className="text-slate-400">Not extracted</span>
                        )}
                      </td>
                      <td className="px-3 py-2 text-right">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectElement?.(isSelected ? null : el.id);
                          }}
                          className="inline-flex items-center gap-1 text-xs font-semibold text-cyan-700 hover:text-cyan-800"
                        >
                          <MapPin className="h-3 w-3" />
                          {isSelected ? 'Deselect' : 'Locate'}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
