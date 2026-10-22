/**
 * 紫微斗数 (Zi Wei Dou Shu) API types mirroring `backend/app/schemas/ziwei.py`.
 * snake_case is preserved end-to-end.
 */

import type { BirthInput, Gender, PlainSection, ProvenanceTable, Verdict } from './common';

/** Input for a 紫微斗数 chart; `gender` is required (fixes the 大限 direction). */
export interface ZiweiRequest extends BirthInput {
  gender: Gender;
  apply_true_solar_time?: boolean;
  name?: string | null;
}

/** One star seated in a palace, with any 四化 mark it carries. */
export interface StarPlacement {
  name: string;
  /** 主星 | 吉 | 煞 | 禄马. */
  kind: string;
  element: string;
  /** 阴 / 阳 (主星 only). */
  yin_yang?: string | null;
  /** 紫微系 / 天府系 (主星 only). */
  group?: string | null;
  /** 星情 keyword (主星 only). */
  nature?: string | null;
  /** 化禄 / 化权 / 化科 / 化忌 when marked. */
  sihua?: string | null;
}

/** One of the twelve 地支 palaces, ordered by 地支 index (子=0 … 亥=11). */
export interface Palace {
  index: number;
  zhi: string;
  gan: string;
  ganzhi: string;
  name: string;
  is_ming: boolean;
  is_shen: boolean;
  /** 大限 age range seated here, e.g. `3-12`. */
  dayun?: string | null;
  stars: StarPlacement[];
  plain: string;
}

/** The 生年干 四化 assignments. */
export interface SiHuaInfo {
  year_gan: string;
  lu: string;
  quan: string;
  ke: string;
  ji: string;
}

/** Chart provenance — engine, corpus version and the 四化 school note. */
export interface ZiweiProvenance {
  engine: string;
  content_version: string;
  source: string;
  school_note: string;
  tables: ProvenanceTable[];
}

/** Complete 紫微斗数 chart produced by the backend engine. */
export interface ZiweiChart {
  name: string | null;
  gender: string;
  calendar: string;
  standard_datetime: string;
  true_solar_time: string | null;
  tst_applied: boolean;
  tst_offset_minutes: number | null;
  longitude: number;

  lunar_date: string;
  lunar_year_ganzhi: string;
  lunar_month: number;
  lunar_day: number;
  lunar_leap: boolean;
  time_zhi: string;

  ming_gong_zhi: string;
  ming_gong_ganzhi: string;
  ming_gong_nayin: string;
  shen_gong_zhi: string;
  shen_gong_name: string;
  wuxing_ju: string;
  wuxing_ju_number: number;
  ming_zhu: string;
  shen_zhu: string;
  ziwei_zhi: string;
  tianfu_zhi: string;

  palaces: Palace[];
  sihua: SiHuaInfo;
  /** 全盘白话：全盘气象、命宫与三方四正、运限与四化三节。 */
  plain: PlainSection[];

  /** 结论卡片：档位 + 星级 + 结论句 + 分项要点 + 一句建议（verdict-card spec §1）。 */
  verdict: Verdict;

  dayun_direction: string;
  dayun_start_age: number;

  engine: string;
  provenance: ZiweiProvenance;
}
