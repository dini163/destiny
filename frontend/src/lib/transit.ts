/**
 * 行运推运 presentation helpers.
 *
 * The backend returns real astronomical positions and geometrically-detected
 * cross-aspects carrying a standard nature taxonomy. These helpers supply
 * *display only* — the moving-layer mode config, nature colours and the wheel's
 * name→longitude lookups — so nothing interpretive is invented on the client
 * (PRD no-mock rule).
 */

import type { CrossAspect, MovingPoint, TransitChart } from '../types/transit';
import type { WesternChart } from '../types/western';

/** The three predictive layers the bi-wheel's outer ring can show. */
export type TransitMode = 'transit' | 'progression' | 'solarArc';

export interface ModeConfig {
  id: TransitMode;
  /** Segmented-control label. */
  label: string;
  /** Short chip label for card headers. */
  short: string;
  /** One-line method blurb shown under the toggle. */
  blurb: string;
}

/** Stable display order for the three layers. */
export const TRANSIT_MODES: ReadonlyArray<ModeConfig> = [
  {
    id: 'transit',
    label: '行运 Transits',
    short: '行运',
    blurb: '目标日正午世界时的真实行星黄经，叠加本命看其过境所成相位。',
  },
  {
    id: 'progression',
    label: '次限 Progressed',
    short: '次限',
    blurb: '「一日当一年」推进本命时刻得推运盘，含推运行星与推运上升/中天。',
  },
  {
    id: 'solarArc',
    label: '太阳弧 Solar Arc',
    short: '太阳弧',
    blurb: '以次限太阳相对本命太阳行过的弧度（约每年 1°）推进本命诸星。',
  },
];

/** Label + blurb for a mode id, for headers and captions. */
export function modeConfig(mode: TransitMode): ModeConfig {
  return TRANSIT_MODES.find((m) => m.id === mode) ?? TRANSIT_MODES[0];
}

/** Accent colour + Chinese label for a cross-aspect nature, with a neutral fallback. */
const NATURE_STYLE: Record<string, { color: string; label: string }> = {
  fusion: { color: '#f2ca50', label: '融合' },
  harmonious: { color: '#2dd4bf', label: '和谐' },
  challenging: { color: '#f43f5e', label: '挑战' },
};
const NATURE_FALLBACK = { color: '#99907c', label: '相位' };

export function natureStyle(nature: string): { color: string; label: string } {
  return NATURE_STYLE[nature] ?? NATURE_FALLBACK;
}

/** The moving-layer points + cross-aspects for a given mode. */
export function modeData(
  chart: TransitChart,
  mode: TransitMode,
): { positions: MovingPoint[]; aspects: CrossAspect[] } {
  switch (mode) {
    case 'transit':
      return { positions: chart.transit_positions, aspects: chart.transit_aspects };
    case 'progression':
      return { positions: chart.progression.positions, aspects: chart.progression.aspects };
    case 'solarArc':
      return { positions: chart.solar_arc.positions, aspects: chart.solar_arc.aspects };
  }
}

/**
 * Map every natal target name (ten planets plus ASC/DES/MC/IC) → longitude, so a
 * cross-aspect's `natal` name resolves to a wheel position for its chord.
 */
export function natalLongitudeByName(natal: WesternChart): Map<string, number> {
  const map = new Map<string, number>();
  natal.planets.forEach((planet) => map.set(planet.name, planet.longitude));
  natal.axes.forEach((axis) => map.set(axis.name, axis.longitude));
  return map;
}

/** Format decimal years as e.g. `26.73 岁`, for the progression headline. */
export function formatAgeYears(years: number): string {
  return `${years.toFixed(2)} 岁`;
}
