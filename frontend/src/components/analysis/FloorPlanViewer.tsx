'use client';

import { useState, useRef, useMemo, useCallback } from 'react';
import {
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Maximize2,
  Minimize2,
  Eye,
  EyeOff,
  Layers,
  Sliders,
  Tag,
  Info,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { AnalysisData, AnalysisRoom, AnalysisElement, PolygonPoint } from './types';
import { CUBICASA_CLASSES, getClassDefForLabel, getClassDefForElementType } from './colors';

interface FloorPlanViewerProps {
  data: AnalysisData;
  planImageUrl?: string;
  selectedRoomId?: number | null;
  selectedElementId?: number | null;
  onSelectRoom?: (id: number | null) => void;
  onSelectElement?: (id: number | null) => void;
}

type ViewMode = 'composite' | 'original' | 'rooms' | 'elements';

export function FloorPlanViewer({
  data,
  planImageUrl,
  selectedRoomId,
  selectedElementId,
  onSelectRoom,
  onSelectElement,
}: FloorPlanViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  // View state
  const [viewMode, setViewMode] = useState<ViewMode>('composite');
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [opacity, setOpacity] = useState(0.55);
  const [showLabels, setShowLabels] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Class visibility toggles
  const [hiddenClasses, setHiddenClasses] = useState<Set<string>>(new Set());

  const toggleClassVisibility = (className: string) => {
    setHiddenClasses((prev) => {
      const next = new Set(prev);
      if (next.has(className)) {
        next.delete(className);
      } else {
        next.add(className);
      }
      return next;
    });
  };

  // Safe polygon parser
  const parsePolygon = useCallback((value: unknown): PolygonPoint[] => {
    if (!Array.isArray(value)) return [];
    return value.filter(
      (point): point is PolygonPoint =>
        Array.isArray(point) &&
        point.length >= 2 &&
        typeof point[0] === 'number' &&
        typeof point[1] === 'number',
    );
  }, []);

  const getRoomPolygon = useCallback(
    (room: AnalysisRoom): PolygonPoint[] => {
      try {
        return parsePolygon(JSON.parse(room.polygon_json || '[]'));
      } catch {
        return [];
      }
    },
    [parsePolygon],
  );

  const getElementPolygon = useCallback(
    (element: AnalysisElement): PolygonPoint[] => {
      try {
        const geometry: unknown = JSON.parse(element.geometry_json || '{}');
        if (typeof geometry !== 'object' || geometry === null || !('polygon_pixels' in geometry)) return [];
        return parsePolygon((geometry as { polygon_pixels: unknown }).polygon_pixels);
      } catch {
        return [];
      }
    },
    [parsePolygon],
  );

  // Extracted rooms with polygon
  const parsedRooms = useMemo(() => {
    return (data.rooms || []).map((room) => ({
      ...room,
      points: getRoomPolygon(room),
      classDef: getClassDefForLabel(room.label),
    }));
  }, [data.rooms, getRoomPolygon]);

  // Extracted elements with polygon
  const parsedElements = useMemo(() => {
    return (data.elements || []).map((element) => ({
      ...element,
      points: getElementPolygon(element),
      classDef: getClassDefForElementType(element.element_type),
    }));
  }, [data.elements, getElementPolygon]);

  // Active detected classes for the interactive legend
  const detectedClasses = useMemo(() => {
    const classMap = new Map<string, { def: typeof CUBICASA_CLASSES[string]; count: number }>();

    for (const r of parsedRooms) {
      if (r.points.length >= 3) {
        const key = r.classDef.name;
        const existing = classMap.get(key);
        if (existing) {
          existing.count += 1;
        } else {
          classMap.set(key, { def: r.classDef, count: 1 });
        }
      }
    }

    for (const el of parsedElements) {
      if (el.points.length >= 3) {
        const key = el.classDef.name;
        const existing = classMap.get(key);
        if (existing) {
          existing.count += 1;
        } else {
          classMap.set(key, { def: el.classDef, count: 1 });
        }
      }
    }

    return Array.from(classMap.values());
  }, [parsedRooms, parsedElements]);

  // Pan controls
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0) return; // Primary click only
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPan({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // Zoom controls
  const handleZoomIn = () => setZoom((z) => Math.min(z * 1.25, 5));
  const handleZoomOut = () => setZoom((z) => Math.max(z / 1.25, 0.4));
  const handleResetZoom = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      void containerRef.current.requestFullscreen();
      setIsFullscreen(true);
    } else {
      void document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  const imageW = data.image_width || 512;
  const imageH = data.image_height || 512;

  const hasAnyPolygons =
    parsedRooms.some((r) => r.points.length >= 3) ||
    parsedElements.some((e) => e.points.length >= 3);

  return (
    <div ref={containerRef} className="overflow-hidden rounded-xl">
      <Card className="border-slate-200 bg-white shadow-xs overflow-hidden">
      <CardHeader className="border-b border-slate-100 bg-slate-50/60 pb-3">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-1">
            <CardTitle className="flex items-center gap-2 text-base font-bold text-slate-900">
              <Layers className="h-4 w-4 text-cyan-600" />
              Floor Plan Spatial Visualization
            </CardTitle>
            <p className="text-xs text-slate-500">
              Interactive 2D overlay of model-segmented room regions, partition walls, doors, and window openings.
            </p>
          </div>

          {/* View Modes Tabs */}
          <div className="flex flex-wrap items-center gap-1 rounded-lg border border-slate-200 bg-white p-1 shadow-2xs">
            <button
              type="button"
              onClick={() => setViewMode('composite')}
              className={`rounded-md px-2.5 py-1 text-xs font-semibold transition ${
                viewMode === 'composite'
                  ? 'bg-cyan-600 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Composite Overlay
            </button>
            <button
              type="button"
              onClick={() => setViewMode('rooms')}
              className={`rounded-md px-2.5 py-1 text-xs font-semibold transition ${
                viewMode === 'rooms'
                  ? 'bg-cyan-600 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Rooms Only
            </button>
            <button
              type="button"
              onClick={() => setViewMode('elements')}
              className={`rounded-md px-2.5 py-1 text-xs font-semibold transition ${
                viewMode === 'elements'
                  ? 'bg-cyan-600 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Elements Only
            </button>
            <button
              type="button"
              onClick={() => setViewMode('original')}
              className={`rounded-md px-2.5 py-1 text-xs font-semibold transition ${
                viewMode === 'original'
                  ? 'bg-cyan-600 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Original Plan
            </button>
          </div>
        </div>

        {/* Toolbar & Viewer Controls */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2 text-xs text-slate-600">
          <div className="flex items-center gap-2">
            {/* Opacity slider */}
            {viewMode !== 'original' && (
              <div className="flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-2.5 py-1">
                <Sliders className="h-3.5 w-3.5 text-slate-400" />
                <span className="text-[11px] font-medium text-slate-600">Opacity:</span>
                <input
                  type="range"
                  min="0.1"
                  max="0.9"
                  step="0.05"
                  value={opacity}
                  onChange={(e) => setOpacity(parseFloat(e.target.value))}
                  className="h-1.5 w-16 accent-cyan-600 cursor-pointer"
                  title="Adjust segmentation layer opacity"
                />
                <span className="text-[10px] font-mono text-slate-500">{Math.round(opacity * 100)}%</span>
              </div>
            )}

            {/* Labels toggle */}
            <button
              type="button"
              onClick={() => setShowLabels(!showLabels)}
              className={`inline-flex items-center gap-1 rounded-md border px-2 py-1 text-[11px] font-medium transition ${
                showLabels
                  ? 'border-cyan-200 bg-cyan-50 text-cyan-700'
                  : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
              }`}
              title="Toggle text labels on room centroids"
            >
              <Tag className="h-3 w-3" />
              Labels
            </button>
          </div>

          {/* Zoom / Pan / Reset Controls */}
          <div className="flex items-center gap-1 rounded-md border border-slate-200 bg-white p-0.5 shadow-2xs">
            <button
              type="button"
              onClick={handleZoomIn}
              className="rounded p-1 text-slate-600 hover:bg-slate-100 hover:text-slate-900"
              title="Zoom In (+)"
            >
              <ZoomIn className="h-3.5 w-3.5" />
            </button>
            <span className="px-1 text-[11px] font-mono font-medium text-slate-600">
              {Math.round(zoom * 100)}%
            </span>
            <button
              type="button"
              onClick={handleZoomOut}
              className="rounded p-1 text-slate-600 hover:bg-slate-100 hover:text-slate-900"
              title="Zoom Out (-)"
            >
              <ZoomOut className="h-3.5 w-3.5" />
            </button>
            <div className="h-3 w-px bg-slate-200 mx-0.5" />
            <button
              type="button"
              onClick={handleResetZoom}
              className="rounded p-1 text-slate-600 hover:bg-slate-100 hover:text-slate-900"
              title="Reset Zoom & Pan (1:1)"
            >
              <RotateCcw className="h-3.5 w-3.5" />
            </button>
            <button
              type="button"
              onClick={toggleFullscreen}
              className="rounded p-1 text-slate-600 hover:bg-slate-100 hover:text-slate-900"
              title={isFullscreen ? 'Exit Fullscreen' : 'View Fullscreen'}
            >
              {isFullscreen ? <Minimize2 className="h-3.5 w-3.5" /> : <Maximize2 className="h-3.5 w-3.5" />}
            </button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-4 space-y-3">
        {/* SVG Drawing Canvas */}
        <div
          className={`relative overflow-hidden rounded-xl border border-slate-200 bg-slate-900/5 select-none ${
            isFullscreen ? 'h-[85vh]' : 'h-[460px]'
          } ${isDragging ? 'cursor-grabbing' : 'cursor-grab'}`}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        >
          <svg
            viewBox={`0 0 ${imageW} ${imageH}`}
            className="h-full w-full"
            preserveAspectRatio="xMidYMid meet"
            style={{
              transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
              transformOrigin: 'center center',
              transition: isDragging ? 'none' : 'transform 0.15s ease-out',
            }}
          >
            {/* Defs for active glow effect */}
            <defs>
              <filter id="active-glow" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow dx="0" dy="0" stdDeviation="3" floodColor="#0284c7" floodOpacity="0.8" />
              </filter>
            </defs>

            {/* 1. Original Floor Plan Image Layer */}
            {planImageUrl && (
              <image
                href={planImageUrl}
                x="0"
                y="0"
                width={imageW}
                height={imageH}
                preserveAspectRatio="xMidYMid meet"
                opacity={viewMode === 'composite' ? 0.95 : viewMode === 'original' ? 1.0 : 0.4}
              />
            )}

            {/* 2. Room Regions Layer */}
            {viewMode !== 'original' &&
              viewMode !== 'elements' &&
              parsedRooms.map((room) => {
                if (room.points.length < 3) return null;
                if (hiddenClasses.has(room.classDef.name)) return null;

                const isSelected = selectedRoomId === room.id;
                const strokeColor = isSelected ? '#0284c7' : room.classDef.stroke;
                const strokeWidth = isSelected ? 3.5 : 1.5;
                const fillOpacity = isSelected ? Math.min(opacity + 0.25, 0.9) : opacity;

                return (
                  <g
                    key={`room-${room.id}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectRoom?.(isSelected ? null : room.id);
                    }}
                    className="cursor-pointer transition-opacity"
                  >
                    <polygon
                      points={room.points.map(([x, y]) => `${x},${y}`).join(' ')}
                      fill={room.classDef.fill}
                      fillOpacity={fillOpacity}
                      stroke={strokeColor}
                      strokeWidth={strokeWidth}
                      strokeDasharray={isSelected ? '6,3' : 'none'}
                      vectorEffect="non-scaling-stroke"
                      filter={isSelected ? 'url(#active-glow)' : 'none'}
                    >
                      <title>{`${room.label} (Area: ${Math.round(room.area_pixels || 0)} px)`}</title>
                    </polygon>

                    {/* Centroid Tag Label */}
                    {showLabels && room.centroid_x != null && room.centroid_y != null && (
                      <g transform={`translate(${room.centroid_x}, ${room.centroid_y})`}>
                        <rect
                          x={-(room.label?.length || 6) * 3.5 - 4}
                          y="-9"
                          width={(room.label?.length || 6) * 7 + 8}
                          height="16"
                          rx="3"
                          fill="#ffffff"
                          fillOpacity="0.85"
                          stroke={room.classDef.stroke}
                          strokeWidth="0.8"
                          vectorEffect="non-scaling-stroke"
                        />
                        <text
                          textAnchor="middle"
                          y="3"
                          fontSize="9"
                          fontWeight="600"
                          fill="#0f172a"
                          className="pointer-events-none select-none font-sans"
                        >
                          {room.label}
                        </text>
                      </g>
                    )}
                  </g>
                );
              })}

            {/* 3. Architectural Elements Layer (Walls, Doors, Windows) */}
            {viewMode !== 'original' &&
              viewMode !== 'rooms' &&
              parsedElements.map((el) => {
                if (el.points.length < 3) return null;
                if (hiddenClasses.has(el.classDef.name)) return null;

                const isSelected = selectedElementId === el.id;
                const strokeColor = isSelected ? '#0284c7' : el.classDef.stroke;
                const strokeWidth = isSelected ? 3.5 : 2;
                const fillOpacity = isSelected ? 0.85 : 0.65;

                return (
                  <g
                    key={`element-${el.id}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectElement?.(isSelected ? null : el.id);
                    }}
                    className="cursor-pointer"
                  >
                    <polygon
                      points={el.points.map(([x, y]) => `${x},${y}`).join(' ')}
                      fill={el.classDef.fill}
                      fillOpacity={fillOpacity}
                      stroke={strokeColor}
                      strokeWidth={strokeWidth}
                      strokeDasharray={isSelected ? '4,2' : 'none'}
                      vectorEffect="non-scaling-stroke"
                      filter={isSelected ? 'url(#active-glow)' : 'none'}
                    >
                      <title>{`${el.label || el.element_type} (Score: ${Math.round((el.confidence || 0) * 100)}%)`}</title>
                    </polygon>
                  </g>
                );
              })}
          </svg>
        </div>

        {/* Fallback notice if polygons are empty */}
        {!hasAnyPolygons && (
          <div className="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 p-2.5 text-xs text-amber-800">
            <Info className="h-4 w-4 shrink-0 text-amber-600" />
            <span>
              No vector geometry was detected for this floor plan. Viewing in original image mode.
            </span>
          </div>
        )}

        {/* Interactive Legend with Visibility Toggles */}
        <div className="border-t border-slate-100 pt-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Interactive Class Legend (Click to show / hide layer)
            </span>
            <span className="text-[11px] text-slate-400">
              {detectedClasses.length} active classes
            </span>
          </div>

          <div className="flex flex-wrap gap-1.5">
            {detectedClasses.map(({ def, count }) => {
              const isHidden = hiddenClasses.has(def.name);
              return (
                <button
                  key={def.name}
                  type="button"
                  onClick={() => toggleClassVisibility(def.name)}
                  className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium border transition-all ${
                    isHidden
                      ? 'border-slate-200 bg-slate-100 text-slate-400 line-through opacity-60'
                      : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 shadow-2xs'
                  }`}
                  title={isHidden ? `Show ${def.label}` : `Hide ${def.label}`}
                >
                  <span
                    className="h-2.5 w-2.5 rounded-full shrink-0"
                    style={{ backgroundColor: def.fill }}
                  />
                  <span>{def.label}</span>
                  <span className="text-[10px] text-slate-400 font-mono">({count})</span>
                  {isHidden ? (
                    <EyeOff className="h-3 w-3 text-slate-400 ml-0.5" />
                  ) : (
                    <Eye className="h-3 w-3 text-slate-400 ml-0.5" />
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
    </div>
  );
}
