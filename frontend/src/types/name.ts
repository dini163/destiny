/**
 * 姓名学五格剖象契约，镜像 `backend/app/schemas/name.py`。
 *
 * 可空即 `T | null`：引擎算不出的字段一律 null，页面对应区块整块不渲染（spec 决策八）。
 * `grids` 的固定序（天→人→地→外→总）由后端保证，前端不再排序。
 */

import type { ProvenanceTable } from './common';
import type { ScoreValue } from './scoring';

/** 设计稿印出的四档吉凶，无第五种取值。 */
export type NameFortune = '大吉' | '吉' | '半吉' | '凶';

export type NameGridKey = 'tian' | 'ren' | 'di' | 'wai' | 'zong';

export interface NameReading {
  pinyin: string;
  tone_number: number;
  tone_name: string;
}

export interface NameChar {
  /** 用户输入的字形。 */
  char: string;
  /** 实际用来计笔画的正体字形。 */
  resolved: string;
  simplified: string[];
  kangxi_strokes: number | null;
  radical_no: number | null;
  residual_strokes: number | null;
  radical_char: string | null;
  radical_strokes: number | null;
  readings: NameReading[];
  stroke_source: string | null;
}

export interface NameGrid {
  key: NameGridKey;
  label: string;
  /** 算式，如 `16+8`；缺笔画的一侧显示为 `?`。 */
  formula: string;
  value: number | null;
  number: number | null;
  fortune: NameFortune | null;
  /** 奇阳偶阴（推导量）。 */
  yinyang: string | null;
  /** 尾数定五行（推导量）。 */
  wuxing: string | null;
  pattern_name: string | null;
  verdict: string | null;
  source: string;
  /** 该格白话段：开篇句 + 数理转述，两行以 `\n` 分隔（引擎装配，前端不拼句）。 */
  plain: string;
}

export interface SancaiElements {
  tian: string;
  ren: string;
  di: string;
}

export interface SancaiPair {
  pair: string;
  relation: string;
  verdict: string;
  source: string;
}

export interface Sancai {
  elements: SancaiElements;
  pairs: SancaiPair[];
  tier: string;
  plain: string;
}

export interface CorpusProvenance {
  unicode_version: string;
  corpus_date: string;
  size: number;
  source: string;
}

export interface NameInput {
  surname: string;
  given: string;
  resolved_traditional: string;
  modality: string;
  modality_formula: string;
}

export interface NameProvenance {
  corpus: CorpusProvenance;
  tables: ProvenanceTable[];
}

export interface NameAnalysis {
  input: NameInput;
  chars: NameChar[];
  grids: NameGrid[];
  sancai: Sancai | null;
  score: ScoreValue | null;
  /** 响应级白话总论：顺/注意两侧重排，末尾落综合档位（算不出分时不出档位句）。 */
  plain_summary: string;
  warnings: string[];
  provenance: NameProvenance;
}

export interface NameAnalyzeRequest {
  surname: string;
  given: string;
  /** 简体字 → 指定正体字。 */
  variants?: Record<string, string> | null;
}
