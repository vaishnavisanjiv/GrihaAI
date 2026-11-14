'use client';

import React, { useState } from 'react';
import {
  Ruler,
  CheckCircle2,
  AlertCircle,
  DoorOpen,
  Maximize2,
  Sliders,
  X,
  Loader2,
  Sparkles,
} from 'lucide-react';
import api from '@/lib/api';
import { AnalysisRoom, AnalysisElement } from './types';

interface ScaleCalibrationModalProps {
  isOpen: boolean;
  onClose: () => void;
  floorPlanId: number;
  currentScale?: number | null;
  rooms?: AnalysisRoom[];
  elements?: AnalysisElement[];
  onScaleApplied: () => Promise<void>;
}

export function ScaleCalibrationModal({
  isOpen,
  onClose,
  floorPlanId,
  currentScale,
  rooms = [],
  elements = [],
  onScaleApplied,
}: ScaleCalibrationModalProps) {
  const [tab, setTab] = useState<'preset' | 'room' | 'direct'>('preset');
  const [presetType, setPresetType] = useState('door_main_1m');
  const [selectedRoomId, setSelectedRoomId] = useState<number>(rooms[0]?.id || 0);
  const [knownRoomDimM, setKnownRoomDimM] = useState<string>('3.50');
  const [roomDimAxis, setRoomDimAxis] = useState<'width' | 'length'>('width');
  const [directPxPerMeter, setDirectPxPerMeter] = useState<string>(
    currentScale ? (currentScale * 1000).toFixed(1) : '50.0',
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  if (!isOpen) return null;

  const detectedDoors = elements.filter((e) => e.element_type === 'door');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMessage('');

    try {
      if (tab === 'preset') {
        const targetM =
          presetType === 'door_main_1m'
            ? 1.0
            : presetType === 'door_room_09m'
            ? 0.9
            : 0.75;

        await api.put(`/api/floor-plans/${floorPlanId}/scale`, {
          preset_type: presetType,
          reference_real_length_m: targetM,
        });
      } else if (tab === 'room') {
        const dimM = parseFloat(knownRoomDimM);
        if (!dimM || dimM <= 0) {
          throw new Error('Please enter a valid positive dimension in metres.');
        }

        const room = rooms.find((r) => r.id === selectedRoomId);
        if (!room || !room.polygon_json) {
          throw new Error('Selected room does not have a valid polygon.');
        }

        const poly = JSON.parse(room.polygon_json) as [number, number][];
        const xs = poly.map((p) => p[0]);
        const ys = poly.map((p) => p[1]);
        const bw = Math.max(...xs) - Math.min(...xs);
        const bh = Math.max(...ys) - Math.min(...ys);
        const refPx = roomDimAxis === 'width' ? Math.min(bw, bh) : Math.max(bw, bh);

        const scaleMm = refPx / (dimM * 1000);
        await api.put(`/api/floor-plans/${floorPlanId}/scale`, {
          scale_pixels_per_mm: scaleMm,
        });
      } else if (tab === 'direct') {
        const pxPerM = parseFloat(directPxPerMeter);
        if (!pxPerM || pxPerM <= 0) {
          throw new Error('Please enter a valid pixels-per-metre value.');
        }
        const scaleMm = pxPerM / 1000.0;
        await api.put(`/api/floor-plans/${floorPlanId}/scale`, {
          scale_pixels_per_mm: scaleMm,
        });
      }

      await onScaleApplied();
      onClose();
    } catch (err: unknown) {
      setErrorMessage(
        err instanceof Error ? err.message : 'Failed to apply drawing scale. Please retry.',
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 animate-in fade-in duration-150">
      <div className="relative w-full max-w-lg rounded-2xl bg-white shadow-2xl border border-slate-200 overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50/70 px-6 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-100 text-cyan-700">
              <Ruler className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">
                Calibrate Drawing Scale
              </h3>
              <p className="text-xs text-slate-500">
                Enables automated NBC 2016 corridor width, room area & clearance checks.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="grid grid-cols-3 border-b border-slate-200 bg-slate-50/40 text-xs font-semibold">
          <button
            type="button"
            onClick={() => setTab('preset')}
            className={`flex items-center justify-center gap-1.5 py-3 border-b-2 transition ${
              tab === 'preset'
                ? 'border-cyan-600 bg-white text-cyan-800'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <DoorOpen className="h-3.5 w-3.5" />
            Door Preset
          </button>
          <button
            type="button"
            onClick={() => setTab('room')}
            className={`flex items-center justify-center gap-1.5 py-3 border-b-2 transition ${
              tab === 'room'
                ? 'border-cyan-600 bg-white text-cyan-800'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Maximize2 className="h-3.5 w-3.5" />
            Room Dimension
          </button>
          <button
            type="button"
            onClick={() => setTab('direct')}
            className={`flex items-center justify-center gap-1.5 py-3 border-b-2 transition ${
              tab === 'direct'
                ? 'border-cyan-600 bg-white text-cyan-800'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Sliders className="h-3.5 w-3.5" />
            Custom Ratio
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {errorMessage && (
            <div className="flex items-center gap-2 rounded-lg bg-rose-50 border border-rose-200 p-3 text-xs text-rose-700">
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* TAB 1: PRESET DOOR CALIBRATION */}
          {tab === 'preset' && (
            <div className="space-y-3">
              <div className="rounded-xl border border-cyan-100 bg-cyan-50/50 p-3.5 text-xs text-cyan-900 leading-relaxed">
                <div className="flex items-center gap-1.5 font-semibold text-cyan-800 mb-1">
                  <Sparkles className="h-3.5 w-3.5" />
                  Fastest 1-Click Calibration
                </div>
                The system detected <strong>{detectedDoors.length} door opening(s)</strong> in your plan.
                Select an architectural standard door width to calibrate drawing scale automatically.
              </div>

              <div className="space-y-2 pt-1">
                <label className="text-xs font-semibold text-slate-700">
                  Select Architectural Standard Door Reference:
                </label>

                <div className="space-y-2">
                  <label className="flex items-center justify-between rounded-xl border border-slate-200 p-3 cursor-pointer hover:bg-slate-50 has-checked:border-cyan-500 has-checked:bg-cyan-50/30">
                    <div className="flex items-center gap-2.5">
                      <input
                        type="radio"
                        name="preset"
                        value="door_main_1m"
                        checked={presetType === 'door_main_1m'}
                        onChange={(e) => setPresetType(e.target.value)}
                        className="text-cyan-600 focus:ring-cyan-500"
                      />
                      <div>
                        <div className="text-xs font-bold text-slate-900">
                          Main Entrance / Exit Door
                        </div>
                        <div className="text-[11px] text-slate-500">
                          Standard clear width: 1.00 m (1000 mm) as per NBC Clause 4.7
                        </div>
                      </div>
                    </div>
                    <span className="font-mono text-xs font-semibold text-cyan-700">1.00 m</span>
                  </label>

                  <label className="flex items-center justify-between rounded-xl border border-slate-200 p-3 cursor-pointer hover:bg-slate-50 has-checked:border-cyan-500 has-checked:bg-cyan-50/30">
                    <div className="flex items-center gap-2.5">
                      <input
                        type="radio"
                        name="preset"
                        value="door_room_09m"
                        checked={presetType === 'door_room_09m'}
                        onChange={(e) => setPresetType(e.target.value)}
                        className="text-cyan-600 focus:ring-cyan-500"
                      />
                      <div>
                        <div className="text-xs font-bold text-slate-900">
                          Internal Habitable Room Door
                        </div>
                        <div className="text-[11px] text-slate-500">
                          Standard bedroom/living clear width: 0.90 m (900 mm)
                        </div>
                      </div>
                    </div>
                    <span className="font-mono text-xs font-semibold text-cyan-700">0.90 m</span>
                  </label>

                  <label className="flex items-center justify-between rounded-xl border border-slate-200 p-3 cursor-pointer hover:bg-slate-50 has-checked:border-cyan-500 has-checked:bg-cyan-50/30">
                    <div className="flex items-center gap-2.5">
                      <input
                        type="radio"
                        name="preset"
                        value="door_bath_075m"
                        checked={presetType === 'door_bath_075m'}
                        onChange={(e) => setPresetType(e.target.value)}
                        className="text-cyan-600 focus:ring-cyan-500"
                      />
                      <div>
                        <div className="text-xs font-bold text-slate-900">
                          Bathroom / Water Closet Door
                        </div>
                        <div className="text-[11px] text-slate-500">
                          Standard minimum bathroom clear width: 0.75 m (750 mm)
                        </div>
                      </div>
                    </div>
                    <span className="font-mono text-xs font-semibold text-cyan-700">0.75 m</span>
                  </label>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: ROOM DIMENSION CALIBRATION */}
          {tab === 'room' && (
            <div className="space-y-3">
              <p className="text-xs text-slate-600 leading-relaxed">
                If you know the real-world width or length of a room from design drawings,
                select the room and enter its measurement in metres.
              </p>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Select Room:
                </label>
                <select
                  value={selectedRoomId}
                  onChange={(e) => setSelectedRoomId(Number(e.target.value))}
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-800 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
                >
                  {rooms.map((r) => (
                    <option key={r.id} value={r.id}>
                      Room #{r.id} — {r.label || 'Other room'} (
                      {r.area_pixels?.toLocaleString()} px²)
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Measurement Axis:
                  </label>
                  <select
                    value={roomDimAxis}
                    onChange={(e) => setRoomDimAxis(e.target.value as 'width' | 'length')}
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-800"
                  >
                    <option value="width">Clear Width (Shorter dimension)</option>
                    <option value="length">Length (Longer dimension)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Known Distance (metres):
                  </label>
                  <div className="relative">
                    <input
                      type="number"
                      step="0.05"
                      min="0.5"
                      max="50"
                      value={knownRoomDimM}
                      onChange={(e) => setKnownRoomDimM(e.target.value)}
                      placeholder="e.g. 3.50"
                      className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs font-mono font-medium text-slate-900 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 pr-8"
                    />
                    <span className="absolute right-3 top-2 text-xs font-semibold text-slate-400">
                      m
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: DIRECT PIXEL SCALE */}
          {tab === 'direct' && (
            <div className="space-y-3">
              <p className="text-xs text-slate-600 leading-relaxed">
                Directly specify the drawing pixel resolution in pixels per metre.
                For standard 512×512 floor plans, typical values are between 40.0 and 70.0 px/m.
              </p>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Scale (Pixels per Metre):
                </label>
                <div className="relative">
                  <input
                    type="number"
                    step="0.5"
                    min="1"
                    max="1000"
                    value={directPxPerMeter}
                    onChange={(e) => setDirectPxPerMeter(e.target.value)}
                    placeholder="e.g. 50.0"
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs font-mono font-medium text-slate-900 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 pr-12"
                  />
                  <span className="absolute right-3 top-2 text-xs font-semibold text-slate-400">
                    px / m
                  </span>
                </div>
                <p className="mt-1 text-[11px] text-slate-400">
                  Equivalent to {(parseFloat(directPxPerMeter || '0') / 1000).toFixed(4)} px/mm.
                </p>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="inline-flex items-center gap-1.5 rounded-lg bg-cyan-600 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-cyan-700 transition disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  Recalculating & Checking NBC...
                </>
              ) : (
                <>
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Apply Scale & Run NBC Checks
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
