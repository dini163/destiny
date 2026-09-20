/**
 * Tarot presentation helpers shared by the oracle page.
 *
 * The backend returns real card data (names, arcana, suit, rank, element,
 * orientation, keywords, meanings) drawn from the curated 78-card deck. These
 * maps supply *presentation only* — the spread catalogue, Chinese labels and
 * accent colours — so nothing interpretive is invented on the client (PRD
 * no-mock rule). Colour strings are written out in full (never concatenated at
 * runtime) so Tailwind's content scanner keeps them and SVG strokes stay stable.
 */

import type { Arcana, CardOrientation, DrawnCard, TarotElement, TarotRank, TarotSuit } from '../types/tarot';

// --- Spread catalogue ------------------------------------------------------

/** A spread layout offered by the picker before a draw. */
export interface SpreadOption {
  id: string;
  name: string;
  name_zh: string;
  /** Number of cards the spread draws (its position count). */
  size: number;
  description: string;
}

/**
 * The six classic Rider-Waite spreads. Values mirror the authoritative spread
 * library in `backend/app/content/tarot_deck.py` (id, bilingual name, position
 * count and description) so the picker never shows an invented layout.
 */
export const SPREAD_CATALOG: readonly SpreadOption[] = [
  {
    id: 'single',
    name: 'Single Card',
    name_zh: '单张牌',
    size: 1,
    description: 'One card for a daily reflection or a quick, focused answer.',
  },
  {
    id: 'three_card',
    name: 'Three Card',
    name_zh: '时间之流三张',
    size: 3,
    description: 'The flow of a situation across time: past, present and future.',
  },
  {
    id: 'celtic_cross',
    name: 'Celtic Cross',
    name_zh: '凯尔特十字',
    size: 10,
    description: 'The classic ten-card spread for a deep, layered reading of a situation.',
  },
  {
    id: 'relationship',
    name: 'Relationship',
    name_zh: '关系牌阵',
    size: 5,
    description: 'A five-card spread reading both partners and the bond between them.',
  },
  {
    id: 'career',
    name: 'Career',
    name_zh: '事业牌阵',
    size: 5,
    description: 'A five-card spread for work, projects and professional direction.',
  },
  {
    id: 'decision',
    name: 'Decision',
    name_zh: '是非抉择牌阵',
    size: 5,
    description: 'A five-card spread comparing two options to inform a choice.',
  },
];

// --- Numerals --------------------------------------------------------------

const ROMAN_STEPS: ReadonlyArray<readonly [number, string]> = [
  [10, 'X'],
  [9, 'IX'],
  [5, 'V'],
  [4, 'IV'],
  [1, 'I'],
];

/** Roman numeral for 1-39 (tarot only needs 0-21); 0 and negatives pass through. */
export function romanNumeral(value: number): string {
  if (value <= 0) {
    return String(value);
  }
  let remaining = value;
  let out = '';
  for (const [step, symbol] of ROMAN_STEPS) {
    while (remaining >= step) {
      out += symbol;
      remaining -= step;
    }
  }
  return out;
}

// --- Suit / rank / element labels -----------------------------------------

const SUIT_ZH: Record<TarotSuit, string> = {
  wands: '权杖',
  cups: '圣杯',
  swords: '宝剑',
  pentacles: '星币',
};

/** Accent colour per suit, matching its classical element. */
const SUIT_COLOR: Record<TarotSuit, string> = {
  wands: '#F43F5E',
  cups: '#38BDF8',
  swords: '#818CF8',
  pentacles: '#E6C65C',
};

const RANK_ZH: Record<TarotRank, string> = {
  Page: '侍从',
  Knight: '骑士',
  Queen: '王后',
  King: '国王',
};

const ELEMENT_ZH: Record<TarotElement, string> = {
  fire: '火',
  water: '水',
  air: '风',
  earth: '土',
};

/** Chinese suit name (权杖/圣杯/宝剑/星币). */
export function suitZh(suit: TarotSuit): string {
  return SUIT_ZH[suit];
}

/** Accent colour for a suit. */
export function suitColor(suit: TarotSuit): string {
  return SUIT_COLOR[suit];
}

/** Chinese court-rank name (侍从/骑士/王后/国王). */
export function rankZh(rank: TarotRank): string {
  return RANK_ZH[rank];
}

/** Chinese element name (火/水/风/土). */
export function elementZh(element: TarotElement): string {
  return ELEMENT_ZH[element];
}

// --- Card-level display helpers -------------------------------------------

/** Gold accent reserved for the Major Arcana. */
const MAJOR_ACCENT = '#F5D77F';

/** The corner numeral/rank glyph shown on a card face. */
export function cardCornerLabel(card: DrawnCard): string {
  if (card.arcana === 'major') {
    return card.number === 0 ? '0' : romanNumeral(card.number);
  }
  if (card.rank) {
    return rankZh(card.rank);
  }
  return card.number === 1 ? 'A' : romanNumeral(card.number);
}

/** Accent colour for a card: gold for majors, the suit colour for minors. */
export function cardAccent(card: DrawnCard): string {
  if (card.arcana === 'major' || !card.suit) {
    return MAJOR_ACCENT;
  }
  return suitColor(card.suit);
}

/** Chinese arcana label (大阿卡纳 / 小阿卡纳). */
export function arcanaZh(arcana: Arcana): string {
  return arcana === 'major' ? '大阿卡纳' : '小阿卡纳';
}

/** Orientation label + accent colour (upright teal, reversed crimson). */
export interface OrientationMeta {
  label: string;
  color: string;
}

export function orientationMeta(orientation: CardOrientation): OrientationMeta {
  return orientation === 'reversed'
    ? { label: '逆位', color: '#F43F5E' }
    : { label: '正位', color: '#2DD4BF' };
}
