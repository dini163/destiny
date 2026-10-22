/**
 * Tarot (塔罗) API types mirroring `backend/app/schemas/tarot.py`.
 * snake_case is preserved end-to-end.
 */

import type { ProvenanceTable, Verdict } from './common';

/** Minor-arcana suit; null for major arcana. */
export type TarotSuit = 'wands' | 'cups' | 'swords' | 'pentacles';

/** Court rank; null for majors and pip cards. */
export type TarotRank = 'Page' | 'Knight' | 'Queen' | 'King';

/** Elemental dignity of a minor card; null for majors. */
export type TarotElement = 'fire' | 'water' | 'air' | 'earth';

/** Whether a drawn card landed upright or reversed. */
export type CardOrientation = 'upright' | 'reversed';

/** Which arcana a card belongs to. */
export type Arcana = 'major' | 'minor';

/** 出处块，镜像 `schemas/tarot.py:TarotProvenance`。 */
export interface TarotProvenance {
  engine: string;
  content_version: string;
  source: string;
  note: string;
  tables: ProvenanceTable[];
}

/**
 * Input for a tarot spread draw. `spread_id` selects a layout: `single`,
 * `three_card`, `celtic_cross`, `relationship`, `career` or `decision`.
 */
export interface TarotSpreadRequest {
  spread_id: string;
  /** Whether cards may land reversed (default true). */
  allow_reversed?: boolean;
  question?: string | null;
}

/** A single card drawn into one spread position. */
export interface DrawnCard {
  /** Zero-based order of the position in the spread. */
  position_index: number;
  /** Stable position identifier, e.g. `past`. */
  position_key: string;
  position_label: string;
  position_label_zh: string;
  /** What this position reveals. */
  position_meaning: string;
  /** What this position reveals, in Chinese. */
  position_meaning_zh: string;

  /** Deck card id, e.g. `major-00` or `wands-07`. */
  card_id: string;
  name: string;
  name_zh: string;
  arcana: Arcana;
  /** Major 0-21; minor 1-14 (11-14 are court). */
  number: number;
  suit: TarotSuit | null;
  rank: TarotRank | null;
  element: TarotElement | null;
  orientation: CardOrientation;
  /** Keywords for the drawn orientation. */
  keywords: string[];
  /** Chinese keywords for the drawn orientation. */
  keywords_zh: string[];
  /** Interpretation text for the drawn orientation. */
  meaning: string;
  /** Interpretation text in Chinese for the drawn orientation. */
  meaning_zh: string;
}

/** Complete tarot spread produced by the backend engine. */
export interface TarotSpreadResponse {
  spread_id: string;
  spread_name: string;
  spread_name_zh: string;
  spread_description: string;
  spread_description_zh: string;
  question: string | null;

  /** Cards in spread-position order. */
  cards: DrawnCard[];
  /** Card ids in draw order (unique within the spread). */
  drawn_ids: string[];
  allow_reversed: boolean;
  /** A reading connecting the drawn cards and positions. */
  synthesis: string;

  major_arcana_count: number;
  reversed_count: number;

  /** 综合结论卡片：档位/星级由已抽牌极性计数确定性聚合（verdict-card spec §1）。 */
  verdict: Verdict;

  provenance: TarotProvenance;

  /** Randomness source: Python secrets (CSPRNG). */
  rng: string;
  engine: string;
}
