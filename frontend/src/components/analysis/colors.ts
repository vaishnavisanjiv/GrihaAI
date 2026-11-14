export interface ClassColorDef {
  id: number;
  name: string;
  label: string;
  fill: string;
  stroke: string;
  badgeBg: string;
  badgeText: string;
  isRoom: boolean;
}

export const CUBICASA_CLASSES: Record<string, ClassColorDef> = {
  background: {
    id: 0,
    name: 'background',
    label: 'Background',
    fill: '#f8fafc',
    stroke: '#cbd5e1',
    badgeBg: 'bg-slate-100',
    badgeText: 'text-slate-600',
    isRoom: false,
  },
  wall: {
    id: 1,
    name: 'wall',
    label: 'Wall',
    fill: '#334155',
    stroke: '#1e293b',
    badgeBg: 'bg-slate-800',
    badgeText: 'text-slate-100',
    isRoom: false,
  },
  kitchen: {
    id: 2,
    name: 'kitchen',
    label: 'Kitchen',
    fill: '#06b6d4',
    stroke: '#0891b2',
    badgeBg: 'bg-cyan-100',
    badgeText: 'text-cyan-800',
    isRoom: true,
  },
  living_dining: {
    id: 3,
    name: 'living_dining',
    label: 'Living / Dining',
    fill: '#3b82f6',
    stroke: '#2563eb',
    badgeBg: 'bg-blue-100',
    badgeText: 'text-blue-800',
    isRoom: true,
  },
  bedroom: {
    id: 4,
    name: 'bedroom',
    label: 'Bedroom',
    fill: '#a855f7',
    stroke: '#9333ea',
    badgeBg: 'bg-purple-100',
    badgeText: 'text-purple-800',
    isRoom: true,
  },
  bathroom: {
    id: 5,
    name: 'bathroom',
    label: 'Bathroom',
    fill: '#14b8a6',
    stroke: '#0d9488',
    badgeBg: 'bg-teal-100',
    badgeText: 'text-teal-800',
    isRoom: true,
  },
  entry: {
    id: 6,
    name: 'entry',
    label: 'Entry / Hallway',
    fill: '#f97316',
    stroke: '#ea580c',
    badgeBg: 'bg-orange-100',
    badgeText: 'text-orange-800',
    isRoom: true,
  },
  railing: {
    id: 7,
    name: 'railing',
    label: 'Railing',
    fill: '#94a3b8',
    stroke: '#64748b',
    badgeBg: 'bg-slate-100',
    badgeText: 'text-slate-700',
    isRoom: false,
  },
  storage: {
    id: 8,
    name: 'storage',
    label: 'Storage',
    fill: '#eab308',
    stroke: '#ca8a04',
    badgeBg: 'bg-yellow-100',
    badgeText: 'text-yellow-800',
    isRoom: true,
  },
  garage: {
    id: 9,
    name: 'garage',
    label: 'Garage',
    fill: '#78350f',
    stroke: '#92400e',
    badgeBg: 'bg-amber-100',
    badgeText: 'text-amber-900',
    isRoom: true,
  },
  other_room: {
    id: 10,
    name: 'other_room',
    label: 'Other room',
    fill: '#38bdf8',
    stroke: '#0284c7',
    badgeBg: 'bg-sky-100',
    badgeText: 'text-sky-800',
    isRoom: true,
  },
  door: {
    id: 11,
    name: 'door',
    label: 'Door',
    fill: '#ef4444',
    stroke: '#dc2626',
    badgeBg: 'bg-red-100',
    badgeText: 'text-red-800',
    isRoom: false,
  },
  window: {
    id: 12,
    name: 'window',
    label: 'Window',
    fill: '#10b981',
    stroke: '#059669',
    badgeBg: 'bg-emerald-100',
    badgeText: 'text-emerald-800',
    isRoom: false,
  },
};

export function getClassDefForLabel(label?: string | null): ClassColorDef {
  if (!label) return CUBICASA_CLASSES.other_room;
  const normalized = label.toLowerCase();
  if (normalized.includes('kitchen')) return CUBICASA_CLASSES.kitchen;
  if (normalized.includes('living') || normalized.includes('dining')) return CUBICASA_CLASSES.living_dining;
  if (normalized.includes('bedroom')) return CUBICASA_CLASSES.bedroom;
  if (normalized.includes('bath')) return CUBICASA_CLASSES.bathroom;
  if (normalized.includes('entry') || normalized.includes('hall')) return CUBICASA_CLASSES.entry;
  if (normalized.includes('storage') || normalized.includes('closet')) return CUBICASA_CLASSES.storage;
  if (normalized.includes('garage')) return CUBICASA_CLASSES.garage;
  if (normalized.includes('door')) return CUBICASA_CLASSES.door;
  if (normalized.includes('window')) return CUBICASA_CLASSES.window;
  if (normalized.includes('wall')) return CUBICASA_CLASSES.wall;
  if (normalized.includes('railing')) return CUBICASA_CLASSES.railing;
  return CUBICASA_CLASSES.other_room;
}

export function getClassDefForElementType(type?: string | null): ClassColorDef {
  if (!type) return CUBICASA_CLASSES.other_room;
  const normalized = type.toLowerCase();
  if (normalized === 'door') return CUBICASA_CLASSES.door;
  if (normalized === 'window') return CUBICASA_CLASSES.window;
  if (normalized === 'wall') return CUBICASA_CLASSES.wall;
  return CUBICASA_CLASSES.other_room;
}
