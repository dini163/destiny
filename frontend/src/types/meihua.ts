/**
 * 梅花易数 (Plum Blossom Numerology) API types mirroring `backend/app/schemas/meihua.py`.
 * snake_case is preserved end-to-end.
 */
import type { ProvenanceTable, Verdict } from './common';

/** How the hexagram is raised (起卦法). */
export type MeihuaMethod = 'time' | 'number';

/** Input for a 梅花易数 cast. `numbers` is required only for the `number` method. */
export interface MeihuaCastRequest {
  method?: MeihuaMethod;
  /** Number method only: one to three positive integers (报数). */
  numbers?: number[] | null;
  question?: string | null;
  /** Cast moment, ISO `yyyy-mm-ddTHH:mm:ss`; defaults to now when omitted. */
  cast_time?: string | null;
}

/** The transparent 起卦 arithmetic that produced the hexagram. */
export interface MeihuaDerivation {
  /** 先天卦数 of the upper (外) trigram, 1-8. */
  upper_number: number;
  /** 先天卦数 of the lower (内) trigram, 1-8. */
  lower_number: number;
  /** Moving-line position 1-6, bottom to top. */
  moving_position: number;
  /** Human-readable derivation formula. */
  formula: string;
  /** The lunar/number inputs used, echoed for auditability. */
  inputs: string;
}

/** One trigram of a hexagram with its 五行 and 象. */
export interface MeihuaTrigram {
  key: string;
  name_zh: string;
  symbol: string;
  nature_zh: string;
  element: string;
  /** lower | upper (内卦 / 外卦). */
  position: 'lower' | 'upper';
}

/** Structural identity of a hexagram plus its classical 卦辞. */
export interface MeihuaHexagram {
  number: number;
  name_zh: string;
  full_name_zh: string;
  symbol: string;
  /** Six lines bottom-to-top, 1=yang 0=yin. */
  lines: number[];
  lower: MeihuaTrigram;
  upper: MeihuaTrigram;
  gua_ci: string;
}

/** The 体卦 or 用卦: its trigram, 万物类象 and 卦气旺衰 state. */
export interface TiYongParty {
  /** ti | yong (体 / 用). */
  role: 'ti' | 'yong';
  trigram: MeihuaTrigram;
  /** 八卦万物类象 one-line summary (《说卦传》). */
  leixiang: string;
  /** 旺相休囚死 state under the 月令. */
  wangshuai: string;
  wangshuai_text: string;
}

/** The primary 体用生克 relation and its judgement. */
export interface TiYongVerdict {
  relation: string;
  relation_zh: string;
  /** 大吉 / 吉 / 小吉 / 小凶 / 大凶. */
  verdict: string;
  /** Ordinal rank, +2 (best) … −2 (worst). */
  grade: number;
  text: string;
}

/** The 卦气 (seasonal strength) context derived from the 月令. */
export interface WangshuaiInfo {
  month_zhi: string;
  season_zh: string;
  commanding_element: string;
}

/** One line of the 吉凶指数 ledger. */
export interface ScoreFactor {
  label: string;
  detail: string;
  delta: number;
}

/** 出处块：镜像 `schemas/meihua.py:MeihuaProvenance`。 */
export interface MeihuaProvenance {
  engine: string;
  /** 起卦与卦气的算式口径原文，读者拿它能核对响应里的数。 */
  method: string;
  /** 本端点真读到的五张语料表，不多不少。 */
  tables: ProvenanceTable[];
}

/** Complete 梅花易数 cast produced by the backend engine. */
export interface MeihuaCast {
  method: MeihuaMethod;
  question: string | null;
  cast_time: string;
  derivation: MeihuaDerivation;

  /** 本卦 — the primary hexagram as raised. */
  ben: MeihuaHexagram;
  /** 互卦 — nuclear hexagram, the 事之中段. */
  hu: MeihuaHexagram;
  /** 变卦 — after the moving line changes, the 事之归宿. */
  bian: MeihuaHexagram;
  moving_position: number;

  ti: TiYongParty;
  yong: TiYongParty;
  tiyong: TiYongVerdict;
  wangshuai: WangshuaiInfo;

  hu_analysis: string;
  bian_analysis: string;

  /** 吉凶指数 0-100 (higher = more favourable). */
  score: number;
  score_factors: ScoreFactor[];
  /** 综合结论卡片：档位词 + 星级 + 结论句 + 四本账分项 + 建议。 */
  verdict: Verdict;
  summary: string;
  /** 白话总论：体用 + 两侧取象与卦气 + 档位收尾，行间以 \n 分段。 */
  plain_summary: string;
  provenance: MeihuaProvenance;

  engine: string;
}
