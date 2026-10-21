/**
 * 卡巴拉生命之树 (Kabbalah Tree of Life) API types mirroring
 * `backend/app/schemas/kabbalah.py`. snake_case is preserved end-to-end.
 *
 * Kabbalah is a fixed reference map (not a random draw): `GET /kabbalah/tree`
 * returns the whole Tree; `POST /kabbalah/gematria` folds an optional word onto it.
 */

import type { PlainSection, ProvenanceTable } from './common';

/** One of the three columns of the Tree (慈悲 / 严厉 / 平衡). */
export interface PillarInfo {
  id: string;
  name_zh: string;
  name_en: string;
  /** right | left | middle (as viewed). */
  side: string;
  virtue: string;
}

/** A single emanation (原质), positioned for rendering. */
export interface SephirahNode {
  /** 1-10; 0 marks the hidden Daath. */
  number: number;
  id: string;
  name_hebrew: string;
  name: string;
  name_zh: string;
  meaning: string;
  /** 逐条对应 `meaning` 的白话转述，必填（spec §9：缺白话即视为伪造响应）。 */
  plain_meaning: string;
  keywords: string[];
  pillar: string;
  pillar_name_zh: string;
  world: string;
  world_name_zh: string;
  sphere: string;
  /** King-Scale hex, adapted for the dark ground. */
  color: string;
  archangel: string;
  divine_name: string;
  /** Normalised 0-1 horizontal position. */
  x: number;
  /** Normalised 0-1 vertical position (0 = crown). */
  y: number;
  /** True for Daath, the veiled node. */
  is_hidden: boolean;
}

/** One of the 22 paths joining two Sephiroth (a Hebrew letter + Tarot trump). */
export interface PathNode {
  /** Golden Dawn path number 11-32. */
  number: number;
  id: string;
  from_sephirah: number;
  to_sephirah: number;
  from_name_zh: string;
  to_name_zh: string;
  letter: string;
  letter_name: string;
  letter_zh: string;
  letter_value: number;
  tarot: string;
  tarot_zh: string;
  /** Golden Dawn numeral (力量 VIII / 正义 XI). */
  tarot_numeral: string;
  correspondence: string;
  meaning: string;
  /** 逐条对应 `meaning` 的白话转述，必填（spec §9：缺白话即视为伪造响应）。 */
  plain_meaning: string;
}

/** Provenance — engine, corpus version, source and the method note. */
export interface KabbalahProvenance {
  engine: string;
  content_version: string;
  source: string;
  note: string;
  tables: ProvenanceTable[];
}

/** The complete Tree of Life, served by `GET /kabbalah/tree`. */
export interface KabbalahTree {
  pillars: PillarInfo[];
  worlds: string[];
  sephiroth: SephirahNode[];
  daath: SephirahNode | null;
  paths: PathNode[];
  sephirah_count: number;
  path_count: number;
  /** 页级整体白话（批次二 spec §5–§7）；顺序与节名由后端定，前端不补算也不改写。 */
  plain: PlainSection[];
  provenance: KabbalahProvenance;
}

/** Input for the gematria fold. */
export interface GematriaRequest {
  text: string;
}

/** One Latin letter's contribution to the gematria total. */
export interface LetterValue {
  letter: string;
  /** A=1 … Z=26. */
  ordinal: number;
  /** A=1 … I=9, J=1 … R=9, S=1 … Z=9. */
  reduction: number;
}

/** A word's numerical essence folded onto the fixed Tree. */
export interface GematriaReading {
  text: string;
  normalized: string;
  breakdown: LetterValue[];
  english_ordinal: number;
  english_reduction: number;
  digital_root: number;
  sephirah: SephirahNode;
  path: PathNode;
  synthesis: string;
  provenance: KabbalahProvenance;
}
