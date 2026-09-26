/**
 * 西洋合盘 (Western Synastry & Composite) API types mirroring
 * `backend/app/schemas/synastry.py`. snake_case is preserved end-to-end. Both
 * natal charts reuse the golden-tested `WesternChart`, and the composite chart
 * reuses `PlanetPlacement`/`AxisPoint`/`HouseCusp`/`Aspect`, so the bi-wheel and
 * the composite wheel are rendered by the existing western visualizations.
 */

import type { ProvenanceTable } from './common';
import type { ScoreValue } from './scoring';
import type { Aspect, AxisPoint, HouseCusp, PlanetPlacement, WesternChart } from './western';

/** One person's birth data for the comparison. */
export interface SynastryPerson {
  /** Gregorian birth date, ISO `yyyy-mm-dd`. */
  birth_date: string;
  /** Local clock birth time, `HH:MM` or `HH:MM:SS`. */
  birth_time: string;
  city?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  /** Local-time offset from UTC in hours; approximated from longitude if omitted. */
  utc_offset_hours?: number | null;
  /** 称谓，仅回显，不进计算。 */
  name?: string | null;
}

/** Two birth profiles plus a house system shared by both charts and the composite. */
export interface SynastryRequest {
  person_a: SynastryPerson;
  person_b: SynastryPerson;
  /** House system code (P=Placidus, K=Koch, R=Regiomontanus, W=Whole…). */
  house_system?: string;
}

/** A person-to-person aspect between one point of A and one point of B. */
export interface SynastryAspect {
  /** Person A's point English name (a planet or ASC/MC). */
  point_a: string;
  point_a_zh: string;
  point_a_glyph: string;
  /** Person B's point English name (a planet or ASC/MC). */
  point_b: string;
  point_b_zh: string;
  point_b_glyph: string;
  /** conjunction | sextile | square | trine | opposition */
  type: string;
  glyph: string;
  angle: number;
  orb: number;
  /** fusion | harmonious | challenging */
  nature: string;
  nature_zh: string;
  /** One of the classic relationship axes (scored with emphasis). */
  core_bond: boolean;
  /** Contributes to the score (both endpoints are personal points). */
  counted: boolean;
}

/** The midpoint (composite) chart of the two natals. */
export interface CompositeChart {
  /** Construction method: shorter-arc midpoint of the two natal longitudes. */
  method: string;
  sun_sign: string;
  sun_sign_zh: string;
  moon_sign: string;
  moon_sign_zh: string;
  ascendant_sign: string;
  ascendant_sign_zh: string;
  /** Ten composite bodies: Sun..Pluto (midpoints; speed 0, never retrograde). */
  planets: PlanetPlacement[];
  /** Composite ASC, DES, MC, IC. */
  axes: AxisPoint[];
  /** Twelve composite house cusps (cusp midpoints). */
  houses: HouseCusp[];
  /** Major aspects among the composite planets. */
  aspects: Aspect[];
  element_balance: Record<string, number>;
  modality_balance: Record<string, number>;
}

/** Provenance + the method note explaining synastry, composite and the score. */
export interface SynastryProvenance {
  engine: string;
  note: string;
  method: string;
  tables: ProvenanceTable[];
}

/** Complete synastry / composite reading for two people. */
export interface SynastryChart {
  person_a_name: string;
  person_b_name: string;
  /** Person A's real natal chart. */
  person_a: WesternChart;
  /** Person B's real natal chart. */
  person_b: WesternChart;
  /** Person-to-person aspects, tightest first. */
  synastry_aspects: SynastryAspect[];
  composite: CompositeChart;
  /** 相契度总分与逐条账本（Σ factors[].delta == value）。 */
  score: ScoreValue;
  provenance: SynastryProvenance;
  engine: string;
}
