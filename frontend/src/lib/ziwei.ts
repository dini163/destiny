/**
 * 紫微斗数 presentation helpers.
 *
 * The backend returns the real chart (十二宫 with their 干支, seated stars, 四化 and
 * 大限 ranges). These maps supply *presentation only* — the classical 4×4 grid cell
 * for each 地支, star-kind colours and 四化 badge tones — so nothing interpretive is
 * invented on the client. Class strings are written out in full for Tailwind's scanner.
 */

import type { CSSProperties } from 'react';

import { GENDER_LABEL } from './gender';

/** Grid position (1-based col/row) of each 地支 in the classical 紫微 square. */
export interface GridCell {
  col: number;
  row: number;
}

/**
 * The 4×4 board: the twelve 地支 rim the square in fixed positions and the centre
 * 2×2 holds the chart summary.
 *
 * ```
 * 巳 午 未 申      row 1
 * 辰    酉         row 2
 * 卯    戌         row 3
 * 寅 丑 子 亥      row 4
 * ```
 */
export const PALACE_GRID: Record<number, GridCell> = {
  5: { col: 1, row: 1 }, // 巳
  6: { col: 2, row: 1 }, // 午
  7: { col: 3, row: 1 }, // 未
  8: { col: 4, row: 1 }, // 申
  4: { col: 1, row: 2 }, // 辰
  9: { col: 4, row: 2 }, // 酉
  3: { col: 1, row: 3 }, // 卯
  10: { col: 4, row: 3 }, // 戌
  2: { col: 1, row: 4 }, // 寅
  1: { col: 2, row: 4 }, // 丑
  0: { col: 3, row: 4 }, // 子
  11: { col: 4, row: 4 }, // 亥
};

/** CSS grid style for a palace cell, keyed by its 地支 index. */
export function palaceGridStyle(index: number): CSSProperties {
  const cell = PALACE_GRID[index] ?? { col: 1, row: 1 };
  return { gridColumn: cell.col, gridRow: cell.row };
}

/** CSS grid style spanning the centre 2×2 for the chart summary. */
export const CENTER_STYLE: CSSProperties = {
  gridColumn: '2 / 4',
  gridRow: '2 / 4',
};

// --- Star kind colours ------------------------------------------------------

/** Star-name colour by kind (主星 gilded, 吉 jade, 煞 crimson, 禄马 azure). */
export function starKindClass(kind: string): string {
  switch (kind) {
    case '主星':
      return 'text-gold-bright';
    case '吉':
      return 'text-wuxing-wood';
    case '煞':
      return 'text-wuxing-fire';
    case '禄马':
      return 'text-wuxing-water';
    default:
      return 'text-ink-variant';
  }
}

// --- 四化 badge tones -------------------------------------------------------

/** Tinted badge classes for a 四化 mark (禄金/权橙/科蓝/忌赤). */
export function sihuaClass(sihua: string): string {
  switch (sihua) {
    case '化禄':
      return 'bg-gold/20 text-gold-bright';
    case '化权':
      return 'bg-wuxing-earth/20 text-wuxing-earth';
    case '化科':
      return 'bg-wuxing-water/20 text-wuxing-water';
    case '化忌':
      return 'bg-wuxing-fire/20 text-wuxing-fire';
    default:
      return 'bg-surface text-ink-muted';
  }
}

/** One-character 四化 abbreviation for the compact cell badge (禄/权/科/忌). */
export function sihuaShort(sihua: string): string {
  return sihua.replace('化', '');
}

// --- Misc labels ------------------------------------------------------------

/** Chinese label for the chart gender, glossed with the sex it denotes. */
export function genderLabel(gender: string): string {
  return gender === 'male'
    ? GENDER_LABEL.male
    : gender === 'female'
      ? GENDER_LABEL.female
      : gender;
}

/** Chinese label for the supplied calendar. */
export function calendarLabel(calendar: string): string {
  return calendar === 'lunar' ? '农历' : '公历';
}
