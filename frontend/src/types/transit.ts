/**
 * 行运推运 (Transit & Progression) API types mirroring
 * `backend/app/schemas/transit.py`. snake_case is preserved end-to-end. The
 * embedded natal chart reuses the golden-tested `WesternChart` type, so the
 * bi-wheel overlay is fully self-contained in one response.
 */

import type { PlainSection, ProvenanceTable, Verdict } from './common';
import type { WesternChart } from './western';

/** Input: natal birth data (as for the natal chart) plus the target date. */
export interface TransitRequest {
  /** Gregorian birth date, ISO `yyyy-mm-dd`. */
  birth_date: string;
  /** Local clock birth time, `HH:MM` or `HH:MM:SS`. */
  birth_time: string;
  city?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  /** Local-time offset from UTC in hours; approximated from longitude if omitted. */
  utc_offset_hours?: number | null;
  /** House system code (P=Placidus, K=Koch, R, E, W…). */
  house_system?: string;
  /** The date transits/progressions are projected onto (must not precede birth). */
  target_date: string;
}

/** A planet's position in a *moving* layer (transit / progressed / directed). */
export interface MovingPoint {
  name: string;
  glyph: string;
  name_zh: string;
  /** Tropical ecliptic longitude, 0-360. */
  longitude: number;
  sign: string;
  sign_zh: string;
  sign_glyph: string;
  sign_index: number;
  degree_in_sign: number;
  degree_text: string;
  /** Which *natal* house this moving body falls in. */
  natal_house: number;
  retrograde: boolean;
  speed: number;
}

/** A progressed chart angle (ASC / MC), with no natal-house meaning of its own. */
export interface AnglePoint {
  name: string;
  label: string;
  longitude: number;
  sign: string;
  sign_zh: string;
  sign_index: number;
  degree_in_sign: number;
  degree_text: string;
}

/** An aspect from a moving-layer body to a natal point. */
export interface CrossAspect {
  /** Moving body's English name, e.g. Saturn. */
  moving: string;
  moving_zh: string;
  moving_glyph: string;
  /** Natal point's English name (a planet or ASC/MC). */
  natal: string;
  natal_zh: string;
  /** conjunction | sextile | square | trine | opposition */
  type: string;
  glyph: string;
  angle: number;
  orb: number;
  /** fusion | harmonious | challenging */
  nature: string;
  nature_zh: string;
}

/** Secondary-progression results for the target date. */
export interface ProgressionBlock {
  /** The 'day-for-a-year' chart date (birth + age in days). */
  progressed_date: string;
  progressed_julian_day: number;
  /** Decimal years from birth to the target date. */
  age_years: number;
  positions: MovingPoint[];
  /** Progressed ASC and MC. */
  angles: AnglePoint[];
  /** Progressed-to-natal aspects, tightest first. */
  aspects: CrossAspect[];
  /** Progressed Moon's sign — the key progression marker. */
  moon_sign_zh: string;
  /** Natal house the progressed Moon now transits. */
  moon_natal_house: number;
}

/** Solar-arc direction results for the target date. */
export interface SolarArcBlock {
  /** Progressed Sun's travel from the natal Sun (≈ 1°/year). */
  arc_degrees: number;
  /** The arc as degrees/minutes, e.g. 30°12'. */
  arc_text: string;
  /** Natal points directed forward by the arc. */
  positions: MovingPoint[];
  /** Directed-to-natal aspects, tightest first. */
  aspects: CrossAspect[];
}

/** Provenance + the method note explaining all three techniques. */
export interface TransitProvenance {
  engine: string;
  note: string;
  /** 行运一页真正读到的三张表（自撰白话两半 + 相位属性表）。 */
  tables: ProvenanceTable[];
}

/** Complete transit / progression reading over the natal chart. */
export interface TransitChart {
  /** The embedded real natal chart (base of the overlay). */
  natal: WesternChart;
  target_date: string;
  target_julian_day: number;
  /** Where the planets are on the target date (noon UT). */
  transit_positions: MovingPoint[];
  /** Transit-to-natal aspects, tightest first. */
  transit_aspects: CrossAspect[];
  progression: ProgressionBlock;
  solar_arc: SolarArcBlock;
  /** 页尾「白话详解」五段，序固定为 行运 / 次限 / 太阳弧 / 次限月亮 / 次限两轴。 */
  plain: PlainSection[];
  /** 综合结论卡片：档位/星级/结论句/分项/建议，由三层等权相位性质计数判定层合成。 */
  verdict: Verdict;
  provenance: TransitProvenance;
  engine: string;
}
