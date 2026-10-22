/**
 * Zhouyi / Liuyao (周易六爻) API types mirroring `backend/app/schemas/zhouyi.py`.
 * snake_case is preserved end-to-end.
 */

import type { PlainSection, ProvenanceTable, Verdict } from './common';

/** How the hexagram is cast. */
export type CastMethod = 'three_coin' | 'manual' | 'time';

/** Line polarity. */
export type YinYang = 'yin' | 'yang';

/**
 * Input for a Zhouyi cast.
 *
 * `manual_coins` is required only for the `manual` method: six throws, each a list
 * of three coin faces where a face is `3` (字背/阳) or `2` (阴), so each throw sums
 * to 6/7/8/9. `cast_time` defaults to now on the backend.
 */
export interface ZhouyiCastRequest {
  method?: CastMethod;
  manual_coins?: number[][] | null;
  question?: string | null;
  /** Cast moment, ISO `yyyy-mm-ddTHH:mm:ss`; defaults to now when omitted. */
  cast_time?: string | null;
}

/** One dressed line (爻) of the primary hexagram, bottom-to-top. */
export interface ZhouyiLine {
  /** Line position 1-6, bottom to top. */
  position: number;
  /** Coin-sum value: 6 old yin, 7 young yang, 8 young yin, 9 old yang. */
  value: number;
  yin_yang: YinYang;
  /** Line glyph: ⚊ (yang) or ⚋ (yin). */
  symbol: string;
  /** Whether this line is a moving line (动爻). */
  moving: boolean;
  /** 纳甲 heavenly stem. */
  stem: string;
  /** 纳甲 earthly branch. */
  branch: string;
  branch_element: string;
  /** 六亲 relative to the palace element: 父母/兄弟/子孙/妻财/官鬼. */
  liuqin: string;
  /** 六神 assigned from the day stem. */
  liushen: string;
  /** Whether this is the 世 (self) line. */
  is_shi: boolean;
  /** Whether this is the 应 (response) line. */
  is_ying: boolean;
  /** 爻题 — classical line title, e.g. 初九 / 六二 / 上六. */
  yao_name: string;
  /** 爻辞 — the classical line statement of the primary hexagram. */
  yao_ci: string;
  /** 爻辞的白话今译，逐键取自 `content/zhouyi_plain.py`。 */
  plain_yao_ci: string;
}

/** Structural identity of a hexagram plus its classical 卦辞. */
export interface HexagramInfo {
  /** King Wen sequence number 1-64. */
  number: number;
  /** Short name, e.g. 屯. */
  name_zh: string;
  /** Trigram-encoded name, e.g. 水雷屯. */
  full_name_zh: string;
  pinyin: string;
  name_en: string;
  /** Unicode hexagram glyph, e.g. ䷂. */
  symbol: string;
  /** Six lines bottom-to-top, 1=yang 0=yin. */
  lines: number[];
  /** Lower (inner) trigram key. */
  lower: string;
  lower_name_zh: string;
  lower_nature_zh: string;
  /** Upper (outer) trigram key. */
  upper: string;
  upper_name_zh: string;
  upper_nature_zh: string;
  /** Palace trigram key (八宫). */
  palace: string;
  /** Palace name, e.g. 坎宫. */
  palace_name_zh: string;
  /** Five-element governing 六亲. */
  palace_element: string;
  /** 本宫/一世…五世/游魂/归魂. */
  generation: string;
  /** 世 line position 1-6. */
  shi: number;
  /** 应 line position 1-6. */
  ying: number;
  /** 卦辞 — the classical hexagram judgment. */
  gua_ci: string;
  /** 卦辞的白话今译。 */
  plain_gua_ci: string;
  /** 用九/用六 line (乾/坤 only); null for the other 62 hexagrams. */
  yong_ci: string | null;
  /** 用九/用六的今译；其余 62 卦为 null 是忠实的缺席（丁组 spec §5）。 */
  plain_yong_ci: string | null;
}

/**
 * 出处块，镜像 `backend/app/schemas/zhouyi.py` 的 `ZhouyiProvenance`。
 *
 * `engine`（恒 `lunar-python`）是**历法事实**的来源，与顶层 `engine`（本端点推导器名
 * `liuyao-najia`）同名不同职——两个键都在响应里，别在页面上把它们混成一句话。
 */
export interface ZhouyiProvenance {
  engine: string;
  content_version: string;
  tables: ProvenanceTable[];
}

/** Complete Zhouyi cast produced by the backend engine. */
export interface ZhouyiCast {
  method: CastMethod;
  question: string | null;
  /** Cast moment used, e.g. `2024-05-15 10:30`. */
  cast_time: string;
  /** Day pillar (日柱) that fixes the 六神. */
  day_ganzhi: string;

  /** 本卦 — the primary hexagram as cast. */
  ben: HexagramInfo;
  /** 变卦 — after moving lines change; null if none move. */
  bian: HexagramInfo | null;
  /** 互卦 — the nuclear hexagram from lines 2-3-4 / 3-4-5. */
  hu: HexagramInfo;

  /** 整卦白话：本卦总论一段；有动爻时再给变卦去向一段。 */
  plain: PlainSection[];

  /** Moving-line positions (1-6, bottom-to-top). */
  moving_positions: number[];
  /** The six dressed lines of the primary hexagram. */
  lines: ZhouyiLine[];

  /** 综合结论卡片：卦辞与动爻爻辞断辞词频净值折算的五档结论。 */
  verdict: Verdict;

  provenance: ZhouyiProvenance;

  rng: string;
  engine: string;
}
