/**
 * BaZi (八字) API types mirroring `backend/app/schemas/bazi.py`.
 *
 * snake_case is preserved end-to-end so the frontend consumes chart responses
 * without a mapping layer.
 */
import type { BirthInput, CalendarType, Gender } from './common';

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
  support_score: number;
  drain_score: number;
  /** support / (support + drain), in [0, 1]. */
  strength_ratio: number;
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

/** Complete BaZi natal chart produced by the backend engine. */
export interface BaziChart {
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

  engine: string;
}
