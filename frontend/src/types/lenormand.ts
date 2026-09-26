/**
 * 雷诺曼 (Lenormand) API types mirroring `backend/app/schemas/lenormand.py`.
 * snake_case is preserved end-to-end. Lenormand reads by combination and never
 * reverses a card, so there is no `orientation` field (unlike tarot).
 */

/** Spread layout families. */
export type LenormandLayout = 'line' | 'box' | 'tableau';

/** Querent significator selector value. */
export type SignificatorChoice = 'none' | 'male' | 'female';

/** Input for a Lenormand draw. */
export interface LenormandRequest {
  spread_id: string;
  question?: string | null;
  /** male | female | null — the querent's 指示牌. */
  significator?: string | null;
}

/** A compact reference to a card (inside combinations / significator neighbours). */
export interface CardRef {
  number: number;
  name_zh: string;
  essence: string;
}

/** One 组合直读 pair: `left` is the subject, `right` the modifier. */
export interface Combination {
  left: CardRef;
  right: CardRef;
  phrase: string;
  context: string;
}

/** Where the querent's 指示牌 landed and what surrounds it. */
export interface SignificatorInfo {
  number: number;
  name_zh: string;
  position_index: number;
  row: number;
  col: number;
  behind: CardRef[];
  ahead: CardRef[];
  above: CardRef[];
  below: CardRef[];
}

/** A single card drawn into one spread position (always upright). */
export interface DrawnCard {
  position_index: number;
  position_key: string;
  position_label_zh: string;
  position_meaning: string;
  row: number;
  col: number;

  card_id: string;
  number: number;
  name: string;
  name_zh: string;
  /** +1 积极 | 0 中性 | -1 消极. */
  polarity: number;
  /** 积极 | 中性 | 消极. */
  polarity_label: string;
  keywords: string[];
  essence: string;
  meaning: string;
  as_modifier: string;
  is_significator: boolean;
}

/** Reading provenance — engine, corpus version, source and the method note. */
export interface LenormandProvenance {
  engine: string;
  content_version: string;
  source: string;
  note: string;
}

/** Complete Lenormand reading produced by the backend engine. */
export interface LenormandReading {
  spread_id: string;
  spread_name_zh: string;
  spread_name_en: string;
  layout: LenormandLayout;
  description: string;
  question: string | null;

  cards: DrawnCard[];
  drawn_ids: string[];
  combinations: Combination[];
  significator: SignificatorInfo | null;
  synthesis: string;

  positive_count: number;
  neutral_count: number;
  negative_count: number;

  rng: string;
  engine: string;
  provenance: LenormandProvenance;
}
