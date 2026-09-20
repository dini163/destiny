/**
 * Western (tropical) natal-astrology API types mirroring
 * `backend/app/schemas/western.py`. snake_case is preserved end-to-end.
 */

/** One of the four chart angles. */
export type AxisName = 'ASC' | 'DES' | 'MC' | 'IC';

/** A major aspect type between two bodies. */
export type AspectType = 'conjunction' | 'sextile' | 'square' | 'trine' | 'opposition';

/** How the UTC offset was resolved. */
export type UtcOffsetSource = 'explicit' | 'longitude_approximation';

/** Input for a Western natal chart. */
export interface WesternNatalRequest {
  /** Gregorian birth date, ISO `yyyy-mm-dd`. */
  birth_date: string;
  /** Local clock birth time, `HH:MM` or `HH:MM:SS`. */
  birth_time: string;
  city?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  /** Local-time offset from UTC in hours; approximated from longitude if omitted. */
  utc_offset_hours?: number | null;
  /** House system code (P=Placidus, K=Koch, R=Regiomontanus, W=Whole). */
  house_system?: string;
}

/** A planet's tropical position, sign and house. */
export interface PlanetPlacement {
  name: string;
  glyph: string;
  name_zh: string;
  /** Tropical ecliptic longitude, 0-360 degrees. */
  longitude: number;
  sign: string;
  sign_zh: string;
  sign_glyph: string;
  sign_index: number;
  degree_in_sign: number;
  /** Degrees/minutes within the sign, e.g. `10°22'`. */
  degree_text: string;
  house: number;
  retrograde: boolean;
  /** Longitudinal speed in degrees/day (negative = retrograde). */
  speed: number;
}

/** A house cusp position. */
export interface HouseCusp {
  house: number;
  longitude: number;
  sign: string;
  sign_zh: string;
  degree_in_sign: number;
  degree_text: string;
}

/** One of the four chart angles (ASC / DES / MC / IC). */
export interface AxisPoint {
  name: AxisName;
  /** Human-readable name, e.g. Ascendant. */
  label: string;
  longitude: number;
  sign: string;
  sign_zh: string;
  sign_index: number;
  degree_in_sign: number;
  degree_text: string;
  /** House the axis rules: ASC=1, IC=4, DES=7, MC=10. */
  house: number;
}

/** A major aspect between two planets. */
export interface Aspect {
  planet1: string;
  planet2: string;
  type: AspectType;
  glyph: string;
  /** Exact aspect angle in degrees. */
  angle: number;
  /** Absolute deviation from the exact angle. */
  orb: number;
}

/** Lunar node positions (North / South). */
export interface NodeInfo {
  north_node_longitude: number;
  north_node_sign: string;
  north_node_sign_zh: string;
  north_node_house: number;
  south_node_longitude: number;
  south_node_sign: string;
  south_node_sign_zh: string;
  south_node_house: number;
}

/** Complete Western natal chart produced by the backend engine. */
export interface WesternChart {
  local_datetime: string;
  utc_datetime: string;
  julian_day: number;
  latitude: number;
  longitude: number;
  utc_offset_hours: number;
  utc_offset_source: UtcOffsetSource;
  house_system: string;
  zodiac: string;

  sun_sign: string;
  sun_sign_zh: string;
  moon_sign: string;
  moon_sign_zh: string;
  ascendant_sign: string;
  ascendant_sign_zh: string;

  /** Ten major bodies: Sun..Pluto. */
  planets: PlanetPlacement[];
  /** ASC, DES, MC, IC. */
  axes: AxisPoint[];
  /** Twelve house cusps. */
  houses: HouseCusp[];
  aspects: Aspect[];
  nodes: NodeInfo;
  /** fire/earth/air/water counts among the planets. */
  element_balance: Record<string, number>;
  /** cardinal/fixed/mutable counts among the planets. */
  modality_balance: Record<string, number>;

  engine: string;
}
