/**
 * 吠陀占星 (Vedic / Jyotish) API types mirroring
 * `backend/app/schemas/vedic.py`. snake_case is preserved end-to-end.
 */

import type { PlainSection, ProvenanceTable } from './common';

/** How the UTC offset was resolved (shared convention with the Western chart). */
export type UtcOffsetSource = 'explicit' | 'longitude_approximation';

/** Input: birth data plus an optional target date marking the live dasha. */
export interface VedicNatalRequest {
  birth_date: string;
  birth_time: string;
  city?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  utc_offset_hours?: number | null;
  /** Date whose Vimshottari period to mark current; defaults to today. */
  target_date?: string | null;
}

/** A graha's sidereal position, sign, whole-sign house and nakshatra. */
export interface VedicPlanet {
  name: string;
  glyph: string;
  name_zh: string;
  name_sa: string;
  /** Sidereal ecliptic longitude, 0-360. */
  longitude: number;
  sign: string;
  sign_zh: string;
  sign_glyph: string;
  sign_index: number;
  degree_in_sign: number;
  degree_text: string;
  /** Whole-sign house counted from the Lagna. */
  house: number;
  nakshatra: string;
  nakshatra_zh: string;
  nakshatra_devanagari: string;
  nakshatra_lord: string;
  nakshatra_lord_zh: string;
  /** Nakshatra quarter (1-4). */
  pada: number;
  retrograde: boolean;
  speed: number;
}

/** One sign (rashi) of the chart, with the grahas occupying it. */
export interface RashiCell {
  sign_index: number;
  sign: string;
  sign_zh: string;
  sign_glyph: string;
  house: number;
  is_lagna: boolean;
  /** Grahas in this sign, in Navagraha order. */
  planet_names: string[];
}

/** A sub-period (bhukti) within a mahadasha. */
export interface Antardasha {
  lord: string;
  lord_zh: string;
  glyph: string;
  start_date: string;
  end_date: string;
  years: number;
  is_current: boolean;
}

/** A major Vimshottari period with its nine antardashas. */
export interface Mahadasha {
  lord: string;
  lord_zh: string;
  glyph: string;
  start_date: string;
  end_date: string;
  /** Actual span from birth (the first is the balance). */
  years: number;
  is_current: boolean;
  antardashas: Antardasha[];
}

/** The Vimshottari period active on the target date. */
export interface CurrentDasha {
  target_date: string;
  mahadasha_lord: string;
  mahadasha_lord_zh: string;
  antardasha_lord: string | null;
  antardasha_lord_zh: string | null;
}

/** The full 120-year Vimshottari dasha timeline from the natal Moon. */
export interface Vimshottari {
  total_years: number;
  balance_at_birth_years: number;
  moon_elapsed_fraction: number;
  birth_nakshatra: string;
  birth_nakshatra_zh: string;
  birth_lord: string;
  birth_lord_zh: string;
  mahadashas: Mahadasha[];
  current: CurrentDasha | null;
}

/** Provenance + the method note. */
export interface VedicProvenance {
  engine: string;
  ayanamsa_name: string;
  content_version: string;
  source: string;
  note: string;
  tables: ProvenanceTable[];
}

/** Complete Vedic (sidereal) natal chart with the Vimshottari timeline. */
export interface VedicChart {
  local_datetime: string;
  utc_datetime: string;
  julian_day: number;
  latitude: number;
  longitude: number;
  utc_offset_hours: number;
  utc_offset_source: UtcOffsetSource;
  zodiac: string;

  /** Lahiri ayanamsa in degrees applied to tropical longitudes. */
  ayanamsa: number;
  ayanamsa_name: string;

  lagna_sign: string;
  lagna_sign_zh: string;
  lagna_sign_glyph: string;
  lagna_index: number;
  lagna_degree_text: string;
  lagna_nakshatra: string;
  lagna_nakshatra_zh: string;

  moon_sign: string;
  moon_sign_zh: string;
  moon_nakshatra: string;
  moon_nakshatra_zh: string;
  moon_nakshatra_lord: string;
  moon_nakshatra_lord_zh: string;
  moon_pada: number;

  planets: VedicPlanet[];
  rashis: RashiCell[];
  vimshottari: Vimshottari;

  plain: PlainSection[];

  provenance: VedicProvenance;
  engine: string;
}
