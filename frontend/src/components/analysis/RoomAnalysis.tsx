'use client';

import { useState, useMemo } from 'react';
import {
  Search,
  LayoutGrid,
  List,
  Info,
  MapPin,
  ChevronDown,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { AnalysisRoom } from './types';
import { getClassDefForLabel } from './colors';

interface RoomAnalysisProps {
  rooms: AnalysisRoom[];
  selectedRoomId?: number | null;
  onSelectRoom?: (id: number | null) => void;
  isCalibrated?: boolean;
}

type SortOption = 'area-desc' | 'area-asc' | 'score-desc' | 'label-asc';

const PAGE_SIZE = 12;

export function RoomAnalysis({
  rooms,
  selectedRoomId,
  onSelectRoom,
  isCalibrated = false,
}: RoomAnalysisProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [sortOption, setSortOption] = useState<SortOption>('area-desc');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);

  // Extract all unique room categories
  const categories = useMemo(() => {
    const set = new Set<string>();
    rooms.forEach((r) => {
      if (r.label) set.add(r.label);
    });
    return ['ALL', ...Array.from(set).sort()];
  }, [rooms]);

  // Filter and sort rooms
  const filteredRooms = useMemo(() => {
    const result = rooms.filter((room) => {
      const label = room.label || 'Other room';
      const matchesSearch = label.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesCat = categoryFilter === 'ALL' || label === categoryFilter;
      return matchesSearch && matchesCat;
    });

    result.sort((a, b) => {
      switch (sortOption) {
        case 'area-desc':
          return (b.area_pixels || 0) - (a.area_pixels || 0);
        case 'area-asc':
          return (a.area_pixels || 0) - (b.area_pixels || 0);
        case 'score-desc':
          return (b.confidence || 0) - (a.confidence || 0);
        case 'label-asc':
          return (a.label || '').localeCompare(b.label || '');
        default:
          return 0;
      }
    });

    return result;
  }, [rooms, searchQuery, categoryFilter, sortOption]);

  const displayedRooms = filteredRooms.slice(0, visibleCount);

  return (
    <Card className="border-slate-200 bg-white shadow-xs">
      <CardHeader className="border-b border-slate-100 bg-slate-50/50 pb-3">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <CardTitle className="text-base font-bold text-slate-900">
              Room Analysis — {rooms.length} Detected Regions
            </CardTitle>
            <p className="mt-0.5 text-xs text-slate-500">
              Structured segmentation output for individual spatial enclosures.
            </p>
          </div>

          {/* Grid / List toggle */}
          <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white p-0.5 shadow-2xs">
            <button
              type="button"
              onClick={() => setViewMode('grid')}
              className={`rounded p-1 text-slate-600 transition ${
                viewMode === 'grid' ? 'bg-slate-100 text-slate-900 font-semibold' : 'hover:bg-slate-50'
              }`}
              title="Grid View"
            >
              <LayoutGrid className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={() => setViewMode('list')}
              className={`rounded p-1 text-slate-600 transition ${
                viewMode === 'list' ? 'bg-slate-100 text-slate-900 font-semibold' : 'hover:bg-slate-50'
              }`}
              title="List View"
            >
              <List className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Measurement Disclaimer Box */}
        <div className="mt-2 flex items-start gap-2 rounded-lg border border-slate-200/80 bg-slate-50 p-2.5 text-xs text-slate-600">
          <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-cyan-600" />
          <span>
            <strong>Measurement Disclaimer:</strong> Pixel area represents the size of the detected region in the image.
            It cannot be interpreted as square metres without a verified image-to-real-world scale calibration.
          </span>
        </div>

        {/* Filter Controls Row */}
        <div className="mt-3 flex flex-wrap items-center gap-2 pt-1 text-xs">
          {/* Search Box */}
          <div className="relative min-w-[180px] flex-1">
            <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filter by room type..."
              className="w-full rounded-md border border-slate-200 bg-white py-1.5 pl-8 pr-3 text-xs text-slate-800 placeholder-slate-400 outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
            />
          </div>

          {/* Category Dropdown */}
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 outline-none focus:border-cyan-500"
          >
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat === 'ALL' ? 'All Room Categories' : cat}
              </option>
            ))}
          </select>

          {/* Sort Dropdown */}
          <select
            value={sortOption}
            onChange={(e) => setSortOption(e.target.value as SortOption)}
            className="rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 outline-none focus:border-cyan-500"
          >
            <option value="area-desc">Area: Largest first</option>
            <option value="area-asc">Area: Smallest first</option>
            <option value="score-desc">Model score: High to low</option>
            <option value="label-asc">Label: A to Z</option>
          </select>
        </div>
      </CardHeader>

      <CardContent className="p-4 space-y-4">
        {displayedRooms.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-6 text-center text-xs text-slate-500">
            No rooms match the selected filter criteria.
          </div>
        ) : viewMode === 'grid' ? (
          /* Grid View of Room Cards */
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {displayedRooms.map((room) => {
              const classDef = getClassDefForLabel(room.label);
              const isSelected = selectedRoomId === room.id;
              const formattedArea = Math.round(room.area_pixels || 0).toLocaleString();
              const scorePct = room.confidence != null ? Math.round(room.confidence * 100) : null;

              return (
                <div
                  key={room.id}
                  onClick={() => onSelectRoom?.(isSelected ? null : room.id)}
                  className={`flex flex-col justify-between rounded-xl border p-3.5 transition cursor-pointer ${
                    isSelected
                      ? 'border-cyan-500 bg-cyan-50/50 shadow-xs ring-1 ring-cyan-500'
                      : 'border-slate-200 bg-white hover:border-slate-300 hover:shadow-2xs'
                  }`}
                >
                  <div className="space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <div className="space-y-0.5">
                        <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                          Room #{room.id}
                        </span>
                        <h4 className="text-sm font-semibold text-slate-900">{room.label || 'Other room'}</h4>
                      </div>
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${classDef.badgeBg} ${classDef.badgeText}`}>
                        {classDef.label}
                      </span>
                    </div>

                    {/* Area & Dimensions */}
                    <div className="rounded-lg bg-slate-50 p-2 text-xs space-y-1">
                      <div className="flex items-baseline justify-between">
                        <span className="text-slate-500 font-medium">Detected Area:</span>
                        <span className="font-mono font-semibold text-slate-800">
                          {room.area_sqm != null ? `${room.area_sqm.toFixed(2)} m²` : `${formattedArea} px²`}
                        </span>
                      </div>

                      <div className="flex items-baseline justify-between text-[11px] text-slate-500">
                        <span>Dimensions:</span>
                        <span>
                          {room.width_m != null && room.length_m != null
                            ? `${room.width_m.toFixed(2)}m × ${room.length_m.toFixed(2)}m`
                            : isCalibrated
                            ? 'Calculated'
                            : 'Scale required'}
                        </span>
                      </div>
                    </div>

                    {/* Model Confidence Score with uncalibrated explanation */}
                    <div className="flex items-center justify-between text-xs pt-1">
                      <span
                        className="text-[11px] text-slate-500 underline decoration-dotted cursor-help"
                        title="Uncalibrated mean max-softmax score. Represents model activation certainty, not a verified probability of human correctness."
                      >
                        Model output score:
                      </span>
                      <span className="font-mono text-xs font-semibold text-slate-700">
                        {scorePct != null ? `${scorePct}%` : '—'}
                      </span>
                    </div>
                  </div>

                  {/* Locate on plan button */}
                  <div className="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectRoom?.(isSelected ? null : room.id);
                      }}
                      className="inline-flex items-center gap-1 text-[11px] font-semibold text-cyan-700 hover:text-cyan-800"
                    >
                      <MapPin className="h-3 w-3" />
                      {isSelected ? 'Deselect on Plan' : 'Locate on Plan'}
                    </button>
                    {isSelected && (
                      <span className="text-[10px] font-semibold uppercase text-cyan-600 bg-cyan-100 px-1.5 py-0.2 rounded">
                        Active
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          /* List View (Table) */
          <div className="overflow-x-auto rounded-xl border border-slate-200">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-200 bg-slate-50 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-3 py-2.5">ID</th>
                  <th className="px-3 py-2.5">Room Label</th>
                  <th className="px-3 py-2.5">Category</th>
                  <th className="px-3 py-2.5">Detected Area</th>
                  <th className="px-3 py-2.5">Estimated Dimensions</th>
                  <th className="px-3 py-2.5">Model Score</th>
                  <th className="px-3 py-2.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {displayedRooms.map((room) => {
                  const classDef = getClassDefForLabel(room.label);
                  const isSelected = selectedRoomId === room.id;
                  const scorePct = room.confidence != null ? Math.round(room.confidence * 100) : null;

                  return (
                    <tr
                      key={room.id}
                      onClick={() => onSelectRoom?.(isSelected ? null : room.id)}
                      className={`hover:bg-slate-50 cursor-pointer ${isSelected ? 'bg-cyan-50/60' : ''}`}
                    >
                      <td className="px-3 py-2.5 font-mono text-slate-500">#{room.id}</td>
                      <td className="px-3 py-2.5 font-medium text-slate-900">{room.label || 'Other room'}</td>
                      <td className="px-3 py-2.5">
                        <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${classDef.badgeBg} ${classDef.badgeText}`}>
                          {classDef.label}
                        </span>
                      </td>
                      <td className="px-3 py-2.5 font-mono font-medium text-slate-800">
                        {room.area_sqm != null
                          ? `${room.area_sqm.toFixed(2)} m²`
                          : `${Math.round(room.area_pixels || 0).toLocaleString()} px²`}
                      </td>
                      <td className="px-3 py-2.5 text-slate-500">
                        {room.width_m != null && room.length_m != null
                          ? `${room.width_m.toFixed(2)}m × ${room.length_m.toFixed(2)}m`
                          : 'Scale required'}
                      </td>
                      <td className="px-3 py-2.5 font-mono font-semibold text-slate-700">
                        {scorePct != null ? `${scorePct}%` : '—'}
                      </td>
                      <td className="px-3 py-2.5 text-right">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectRoom?.(isSelected ? null : room.id);
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

        {/* Progressive Load / Pagination Controls */}
        {filteredRooms.length > visibleCount && (
          <div className="text-center pt-2">
            <button
              type="button"
              onClick={() => setVisibleCount((prev) => prev + PAGE_SIZE)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 shadow-2xs hover:bg-slate-50 hover:text-slate-900 transition"
            >
              Show more rooms ({visibleCount} of {filteredRooms.length} shown)
              <ChevronDown className="h-3.5 w-3.5 text-slate-500" />
            </button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
