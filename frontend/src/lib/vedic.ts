/**
 * 吠陀占星 presentation helpers.
 *
 * The backend returns real sidereal positions, nakshatras and the Vimshottari
 * timeline. These helpers supply *display only* — graha colours, the two classical
 * Indian chart layouts (South = fixed signs, North = fixed houses) and small
 * geometry — so nothing interpretive is invented on the client (PRD no-mock rule).
 * Colour strings are written out in full so Tailwind's scanner keeps them.
 */

import type { VedicChart, VedicPlanet } from '../types/vedic';

/** The two classical chart-drawing conventions. */
export type ChartStyle = 'south' | 'north';

export const CHART_STYLES: ReadonlyArray<{ value: ChartStyle; label: string }> = [
  { value: 'south', label: '南印盘 South Indian' },
  { value: 'north', label: '北印盘 North Indian' },
];

/** Accent colour for each of the nine grahas, keyed by the backend's name. */
const GRAHA_COLOR: Record<string, string> = {
  Sun: '#f2ca50',
  Moon: '#c7cbff',
  Mars: '#f43f5e',
  Mercury: '#e1c46e',
  Jupiter: '#ffe088',
  Venus: '#2dd4bf',
  Saturn: '#d0c5af',
  Rahu: '#a5adff',
  Ketu: '#e08a2e',
};

export function grahaColor(name: string): string {
  return GRAHA_COLOR[name] ?? '#e2e2eb';
}

/** Rashi number (1-12) shown in the North-Indian house, from a 0-based sign index. */
export function rashiNumber(signIndex: number): number {
  return signIndex + 1;
}

// --- South Indian layout ----------------------------------------------------
// Signs occupy FIXED cells and run clockwise from Aries at the top-second column.
// The four centre cells are merged for the chart title.

export interface SouthCell {
  signIndex: number;
  row: number; // 1-based CSS grid row
  col: number; // 1-based CSS grid column
}

/** The 12 fixed sign positions of the South-Indian grid (4×4, centre merged). */
export const SOUTH_CELLS: ReadonlyArray<SouthCell> = [
  { signIndex: 0, row: 1, col: 2 },
  { signIndex: 1, row: 1, col: 3 },
  { signIndex: 2, row: 1, col: 4 },
  { signIndex: 3, row: 2, col: 4 },
  { signIndex: 4, row: 3, col: 4 },
  { signIndex: 5, row: 4, col: 4 },
  { signIndex: 6, row: 4, col: 3 },
  { signIndex: 7, row: 4, col: 2 },
  { signIndex: 8, row: 4, col: 1 },
  { signIndex: 9, row: 3, col: 1 },
  { signIndex: 10, row: 2, col: 1 },
  { signIndex: 11, row: 1, col: 1 },
];

// --- North Indian layout ----------------------------------------------------
// Houses occupy FIXED polygons and the signs rotate; house 1 is always the top
// centre. Built on a 400×400 square: corners, edge midpoints and the centre,
// joined by the two diagonals and the inner (midpoint) diamond → 12 regions.

export interface NorthHouse {
  house: number; // 1-12
  points: ReadonlyArray<readonly [number, number]>;
}

/** The 12 fixed house polygons of the North-Indian chart, clockwise from the top. */
export const NORTH_HOUSES: ReadonlyArray<NorthHouse> = [
  { house: 1, points: [[200, 0], [300, 100], [200, 200], [100, 100]] },
  { house: 2, points: [[200, 0], [400, 0], [300, 100]] },
  { house: 3, points: [[400, 0], [400, 200], [300, 100]] },
  { house: 4, points: [[400, 200], [300, 300], [200, 200], [300, 100]] },
  { house: 5, points: [[400, 200], [400, 400], [300, 300]] },
  { house: 6, points: [[400, 400], [200, 400], [300, 300]] },
  { house: 7, points: [[200, 400], [100, 300], [200, 200], [300, 300]] },
  { house: 8, points: [[200, 400], [0, 400], [100, 300]] },
  { house: 9, points: [[0, 400], [0, 200], [100, 300]] },
  { house: 10, points: [[0, 200], [100, 100], [200, 200], [100, 300]] },
  { house: 11, points: [[0, 200], [0, 0], [100, 100]] },
  { house: 12, points: [[0, 0], [200, 0], [100, 100]] },
];

/** SVG `points` attribute string for a polygon. */
export function toPointsAttr(points: ReadonlyArray<readonly [number, number]>): string {
  return points.map(([x, y]) => `${x},${y}`).join(' ');
}

/** Centroid (vertex mean) of a convex polygon, for placing its label. */
export function polygonCentroid(points: ReadonlyArray<readonly [number, number]>): { x: number; y: number } {
  const sum = points.reduce((acc, [x, y]) => ({ x: acc.x + x, y: acc.y + y }), { x: 0, y: 0 });
  return { x: sum.x / points.length, y: sum.y / points.length };
}

/** The sign index occupying a whole-sign house, given the Lagna's sign index. */
export function signIndexOfHouse(house: number, lagnaIndex: number): number {
  return (lagnaIndex + house - 1) % 12;
}

/** Look up the grahas sitting in a given sign (South Indian) by sign index. */
export function planetsInSign(planets: VedicPlanet[], signIndex: number): VedicPlanet[] {
  return planets.filter((planet) => planet.sign_index === signIndex);
}

/** Look up the grahas sitting in a given whole-sign house (North Indian). */
export function planetsInHouse(planets: VedicPlanet[], house: number): VedicPlanet[] {
  return planets.filter((planet) => planet.house === house);
}

/** The rashi cell for a sign index, from the chart's 12-cell list. */
export function rashiByIndex(chart: VedicChart, signIndex: number) {
  return chart.rashis.find((rashi) => rashi.sign_index === signIndex);
}

/** Format a dasha span as e.g. `16.0 年`, or `8 个月` when under a year. */
export function formatSpan(years: number): string {
  if (years < 1) {
    const months = Math.round(years * 12);
    return `${Math.max(months, 1)} 个月`;
  }
  return `${years.toFixed(1)} 年`;
}
