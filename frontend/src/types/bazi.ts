/**
 * BaZi (八字) API types mirroring `backend/app/schemas/bazi.py`.
 *
 * snake_case is preserved end-to-end so the frontend consumes chart responses
 * without a mapping layer.
 */
import type { BirthInput, CalendarType, Gender, ProvenanceTable } from './common';
import type { ScoreValue } from './scoring';

/** Which of the four pillars a {@link BaziPillar} represents. */
export type PillarPosition = 'year' | 'month' | 'day' | 'hour';

/** Day-master strength classification. */
export type StrengthLevel = 'weak' | 'balanced' | 'strong';

/** Luck-pillar (大运) direction; null when gender is not supplied. */
export type DayunDirection = 'forward' | 'backward';

/** Input for a BaZi natal chart. Gender is required (fixes 大运顺逆). */
export interface BaziNatalRequest extends BirthInput {
  gender: Gender;
  /** Correct standard time to True Solar Time before charting (default true). */
  apply_true_solar_time?: boolean;
  /** Display-only label, echoed back unchanged. */
  name?: string | null;
  /** Cutoff for the current luck pillar; defaults to the server date. */
  reference_date?: string | null;
}

/** One of the four pillars (year / month / day / hour). */
export interface BaziPillar {
  position: PillarPosition;
  /** Chinese pillar label, e.g. 年柱. */
  label: string;
  /** Full pillar, e.g. 戊辰. */
  ganzhi: string;
  /** Heavenly stem, e.g. 戊. */
  gan: string;
  /** Earthly branch, e.g. 辰. */
  zhi: string;
  gan_element: string;
  zhi_element: string;
  /** Nayin (纳音), e.g. 大林木. */
  nayin: string;
  /** Branch hidden stems (藏干). */
  hidden_stems: string[];
  hidden_stem_elements: string[];
  /** Ten-god of the stem relative to the day master. */
  shishen_gan: string;
  /** Ten-gods of the hidden stems. */
  shishen_zhi: string[];
  /** Twelve life-stages (地势/十二长生). */
  di_shi: string;
  /** Sexagenary decade (旬). */
  xun: string;
  /** Void branches of the decade (空亡). */
  xun_kong: string;
}

/** Five-element presence: a headcount and a weighted strength score. */
export interface WuxingScore {
  element: string;
  count: number;
  score: number;
}

/** Deterministic day-master strength and useful-god analysis. */
export interface DayMasterAnalysis {
  day_master: string;
  day_master_element: string;
  /** Three-factor ledger behind `level`; open it to see the arithmetic. */
  strength: ScoreValue;
  /** Score sits within `BORDERLINE_BAND` (3.0) of a band cut (spec §6.4). */
  borderline: boolean;
  level: StrengthLevel;
  /** Chinese label, e.g. 身弱. */
  label: string;
  favorable_elements: string[];
  unfavorable_elements: string[];
  summary: string;
}

/** A single luck-pillar (大运) step; index 0 is the pre-luck childhood span. */
export interface DayunStep {
  index: number;
  /** Luck pillar, empty for the childhood span. */
  ganzhi: string;
  start_age: number;
  end_age: number;
  start_year: number;
  end_year: number;
  xun: string;
  xun_kong: string;
  is_current: boolean;
}

/** A single annual-fortune (流年) year within the current luck pillar. */
export interface LiunianYear {
  year: number;
  age: number;
  ganzhi: string;
}

/** Dimension names in output order; 婚姻 is absent when the chart has no gender. */
export type DimensionName = '事业' | '财运' | '婚姻' | '健康' | '学业' | '人际';

/** Which side of a pillar a shensha hit landed on. */
export type CharacterSide = 'gan' | 'zhi' | 'pillar';

export interface ShenShaMatch {
  /** `year | month | day | hour | extra<n>`: extra slots are 大运/流年 pillars. */
  position: string;
  character: string;
  at: CharacterSide;
}

export interface ShenShaEntry {
  name: string;
  quality: '吉' | '凶' | '中性';
  /** What the lookup is anchored to, e.g. 申子辰局. */
  checked_from: string;
  matches: ShenShaMatch[];
  meaning: string;
  source: string;
}

export interface RelationPair {
  kind: string;
  /** `year | month | day | hour | extra<n>`. */
  pillar_a: string;
  pillar_b: string;
  character_a: string;
  character_b: string;
  strength: '紧临' | '隔位' | '远位';
  /** 合化目标, never an already-transformed result (spec §6.3). */
  transforming_element: string | null;
  reading: string;
  source: string;
}

export interface BranchMember {
  pillar: string;
  branch: string;
  ten_god: string;
}

export interface BranchGroup {
  kind: '三合' | '半合' | '三会';
  element: string;
  members: BranchMember[];
  is_complete: boolean;
  reading: string;
  source: string;
}

export interface GeJu {
  name: string;
  from_pillar: string;
  ten_god: string;
  is_success: boolean;
  /** Whole sentences taken verbatim from the corpus, in pillar order. */
  notes: string[];
  source: string;
}

export interface HiddenStemWeight {
  position: PillarPosition;
  branch: string;
  stem: string;
  role: '本气' | '中气' | '余气';
  weight: number;
  ten_god: string;
  source: string;
}

export interface YongshenMethod {
  method: '扶抑' | '通关' | '调候';
  /** Machine key of the branch taken — recorded even when the method stays silent. */
  fired_rule: string;
  chosen_elements: string[];
  already_present: boolean;
  source: string;
}

export interface YongshenConflict {
  element: string;
  suppressed_by: string;
  reason: string;
  source: string;
}

export interface Yongshen {
  favorable_elements: string[];
  unfavorable_elements: string[];
  methods: YongshenMethod[];
  conflict: YongshenConflict | null;
}

export interface TenGodReading {
  ten_god: string;
  count: number;
  /** e.g. `month.gan`, `day.zhi(癸)`. */
  positions: string[];
  meaning: string;
  six_relation: string | null;
  source: string;
}

export interface DayunDetail {
  index: number;
  ganzhi: string;
  start_age: number;
  end_age: number;
  relations: RelationPair[];
}

export interface Provenance {
  /** ISO date; the cutoff that decided `dayun_current`, echoed back by the API. */
  reference_date: string;
  engine: string;
  tables: ProvenanceTable[];
}

export interface DimensionReading {
  dimension: DimensionName;
  score: ScoreValue;
  strengths: string[];
  cautions: string[];
  /** Fired rules' `reading` joined by 「；」— no sentence is composed in the frontend. */
  narrative: string;
  source: string;
}

export interface BaziInterpretation {
  six_dimensions: DimensionReading[];
  summary: string;
}

/** Complete BaZi natal chart produced by the backend engine. */
export interface BaziChart {
  /** Name supplied with the request, echoed back untouched. */
  name?: string | null;
  /** Civil standard-time input, e.g. `1988-02-15 23:30`. */
  standard_datetime: string;
  calendar: CalendarType;
  /** True Solar Time used for charting, if applied. */
  true_solar_time: string | null;
  tst_applied: boolean;
  tst_offset_minutes: number | null;
  longitude: number;
  /** Lunar-calendar date, e.g. 一九八七年腊月廿八. */
  lunar_date: string;

  /** Space-joined four pillars, e.g. `戊辰 甲寅 庚子 丁亥`. */
  four_pillars: string;
  pillars: BaziPillar[];
  zodiac: string;
  day_master: string;
  day_master_element: string;
  ming_gong: string;
  ming_gong_nayin: string;
  tai_yuan: string;
  tai_yuan_nayin: string;

  /** Five-element scores in 木火土金水 order. */
  wuxing: WuxingScore[];
  missing_elements: string[];
  analysis: DayMasterAnalysis;

  dayun_direction: DayunDirection | null;
  dayun_start_solar: string | null;
  dayun: DayunStep[];
  current_liunian: LiunianYear[];

  /** Interpretation breakdown — optional here because 流月/合婚 share the chart type. */
  geju?: GeJu | null;
  yongshen?: Yongshen | null;
  shensha?: ShenShaEntry[];
  ten_god_readings?: TenGodReading[];
  relations?: RelationPair[];
  branch_groups?: BranchGroup[];
  hidden_stem_ledger?: HiddenStemWeight[];
  dayun_current?: DayunDetail | null;
  interpretation?: BaziInterpretation | null;
  provenance?: Provenance | null;

  engine: string;
}
