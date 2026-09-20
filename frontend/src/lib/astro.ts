/**
 * Western (tropical) astrology presentation helpers shared by the natal page.
 *
 * The backend returns real astronomical values (longitudes, signs, aspects,
 * house cusps). These maps supply *presentation only* — colour, Chinese labels
 * and the wheel geometry — so nothing interpretive is invented on the client
 * (PRD no-mock rule). Colour strings are written out in full (never built at
 * runtime) so Tailwind's content scanner keeps them and SVG strokes stay stable.
 */

/** Ordered zodiac sign glyphs (Aries → Pisces) for the wheel's outer ring. */
export const SIGN_GLYPHS = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓'] as const;

/** Ordered zodiac sign Chinese names, matching the backend's `SIGNS_ZH`. */
export const SIGNS_ZH = [
  '白羊',
  '金牛',
  '双子',
  '巨蟹',
  '狮子',
  '处女',
  '天秤',
  '天蝎',
  '射手',
  '摩羯',
  '水瓶',
  '双鱼',
] as const;

// --- Aspects ---------------------------------------------------------------

/** Chinese label + chord colour for a major aspect type. */
export interface AspectStyle {
  label: string;
  color: string;
}

const ASPECT_STYLE: Record<string, AspectStyle> = {
  conjunction: { label: '合相', color: '#f2ca50' },
  sextile: { label: '六合', color: '#38bdf8' },
  square: { label: '刑相', color: '#f43f5e' },
  trine: { label: '拱相', color: '#2dd4bf' },
  opposition: { label: '冲相', color: '#c7cbff' },
};

const ASPECT_FALLBACK: AspectStyle = { label: '相位', color: '#99907c' };

/** Colour + Chinese label for an aspect type, with a neutral fallback. */
export function aspectStyle(type: string): AspectStyle {
  return ASPECT_STYLE[type] ?? ASPECT_FALLBACK;
}

// --- Element balance -------------------------------------------------------

/** Display metadata for one of the four triplicity elements. */
export interface ElementStyle {
  label: string;
  color: string;
  /** The three signs of this triplicity (fixed zodiac fact, not chart data). */
  signs: string;
}

const ELEMENT_STYLE: Record<string, ElementStyle> = {
  fire: { label: '火象 Fire', color: '#f43f5e', signs: '白羊 · 狮子 · 射手' },
  earth: { label: '土象 Earth', color: '#e1c46e', signs: '金牛 · 处女 · 摩羯' },
  air: { label: '风象 Air', color: '#38bdf8', signs: '双子 · 天秤 · 水瓶' },
  water: { label: '水象 Water', color: '#2dd4bf', signs: '巨蟹 · 天蝎 · 双鱼' },
};

/** Stable render order for the element balance. */
export const ELEMENT_ORDER = ['fire', 'earth', 'air', 'water'] as const;

/** Display metadata for an element key, with a neutral fallback. */
export function elementStyle(key: string): ElementStyle {
  return ELEMENT_STYLE[key] ?? { label: key, color: '#99907c', signs: '' };
}

// --- Modality balance ------------------------------------------------------

/** Display metadata for one of the three quadruplicities. */
export interface ModalityStyle {
  label: string;
  color: string;
}

const MODALITY_STYLE: Record<string, ModalityStyle> = {
  cardinal: { label: '基本宫 Cardinal', color: '#f2ca50' },
  fixed: { label: '固定宫 Fixed', color: '#c7cbff' },
  mutable: { label: '变动宫 Mutable', color: '#2dd4bf' },
};

/** Stable render order for the modality balance. */
export const MODALITY_ORDER = ['cardinal', 'fixed', 'mutable'] as const;

/** Display metadata for a modality key, with a neutral fallback. */
export function modalityStyle(key: string): ModalityStyle {
  return MODALITY_STYLE[key] ?? { label: key, color: '#99907c' };
}

// --- Planet accents --------------------------------------------------------

const PLANET_COLOR: Record<string, string> = {
  Sun: '#f2ca50',
  Moon: '#c7cbff',
  Mercury: '#e1c46e',
  Venus: '#2dd4bf',
  Mars: '#f43f5e',
  Jupiter: '#ffe088',
  Saturn: '#d0c5af',
  Uranus: '#38bdf8',
  Neptune: '#a5adff',
  Pluto: '#e2e2eb',
};

/** Accent colour for a body, keyed by the backend's English planet name. */
export function planetColor(name: string): string {
  return PLANET_COLOR[name] ?? '#e2e2eb';
}

/**
 * Format an ecliptic longitude as degrees+minutes within its sign, e.g. `10°22'`,
 * matching the backend's `degree_text`. Used for bodies (such as the lunar nodes)
 * whose payload carries a raw longitude but no pre-formatted degree string.
 */
export function formatDegreeInSign(longitude: number): string {
  const within = ((longitude % 30) + 30) % 30;
  const degrees = Math.floor(within);
  const minutes = Math.round((within - degrees) * 60);
  return `${degrees}°${String(minutes).padStart(2, '0')}'`;
}

// --- Wheel geometry --------------------------------------------------------

/** A point on the SVG canvas. */
export interface Point {
  x: number;
  y: number;
}

/**
 * Convert polar coordinates to SVG cartesian space (y grows downward), with the
 * angle measured counter-clockwise from the east (3-o'clock) direction.
 */
export function polarToCartesian(cx: number, cy: number, radius: number, angleDeg: number): Point {
  const rad = (angleDeg * Math.PI) / 180;
  return { x: cx + radius * Math.cos(rad), y: cy - radius * Math.sin(rad) };
}

/**
 * Screen angle (degrees, CCW from east) for an ecliptic longitude on a natal
 * wheel that places the Ascendant at 9 o'clock with the zodiac running
 * counter-clockwise — the standard Western chart orientation.
 */
export function wheelAngle(longitude: number, ascendantLongitude: number): number {
  const delta = (((longitude - ascendantLongitude) % 360) + 360) % 360;
  return 180 + delta;
}
