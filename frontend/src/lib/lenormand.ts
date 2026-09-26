/**
 * 雷诺曼 (Lenormand) presentation helpers.
 *
 * The backend returns the real draw (cards, combinations, significator, synthesis).
 * These maps supply *presentation only* — the spread picker, the significator picker
 * and polarity colours — so nothing interpretive is invented on the client. Colour
 * strings are written out in full so Tailwind's scanner keeps them.
 */

import type { SignificatorChoice } from '../types/lenormand';

// --- Spread picker ----------------------------------------------------------

/** A selectable spread with a short factual hint and its card count. */
export interface SpreadOption {
  value: string;
  label: string;
  /** Card count, shown as a numeric chip. */
  size: number;
  hint: string;
}

/** The five layouts the engine supports (see `app.engines.lenormand`). */
export const SPREAD_OPTIONS: readonly SpreadOption[] = [
  { value: 'single', label: '单张牌', size: 1, hint: '一张牌作即时聚焦的提点，或对某问题的一句话回答。' },
  { value: 'three_card', label: '三张线性', size: 3, hint: '三张读成一句话：主词 → 修饰 → 结果，最经典的线性组合。' },
  { value: 'five_card', label: '五行线阵', size: 5, hint: '五张成一条时间线，中央为核心现状，左右为过去与未来。' },
  { value: 'nine_card', label: '九宫阵', size: 9, hint: '三乘三方阵，中心为核心，四正四隅为环绕的影响。' },
  { value: 'grand_tableau', label: '大桌全景', size: 36, hint: '三十六张尽数铺开，以指示牌为中心作全景式命运俯瞰。' },
];

/** Label for a spread id, echoing the raw value when unknown. */
export function spreadLabel(spreadId: string): string {
  return SPREAD_OPTIONS.find((option) => option.value === spreadId)?.label ?? spreadId;
}

// --- Significator picker ----------------------------------------------------

/** A selectable 指示牌 choice. */
export interface SignificatorOption {
  value: SignificatorChoice;
  label: string;
}

/** The querent's 指示牌 selector: none, 男人(28) or 女人(29). */
export const SIGNIFICATOR_OPTIONS: readonly SignificatorOption[] = [
  { value: 'none', label: '不指定' },
  { value: 'male', label: '男 · 男人28' },
  { value: 'female', label: '女 · 女人29' },
];

/** Map the UI choice to the request value (none → null). */
export function significatorRequestValue(choice: SignificatorChoice): string | null {
  return choice === 'none' ? null : choice;
}

// --- Polarity tone (积极 / 中性 / 消极) -------------------------------------

/** Text colour for a card polarity (+1 / 0 / -1). */
export function polarityText(polarity: number): string {
  if (polarity > 0) return 'text-gold-bright';
  if (polarity < 0) return 'text-wuxing-fire';
  return 'text-ink-muted';
}

/** Accent hex used for the card numeral + border tint, keyed by polarity. */
export function polarityAccent(polarity: number): string {
  if (polarity > 0) return '#F5D77F'; // gold-bright
  if (polarity < 0) return '#F43F5E'; // wuxing-fire
  return '#948C79'; // ink-muted
}

/** Tinted chip classes for a polarity label. */
export function polarityChip(polarity: number): string {
  if (polarity > 0) return 'bg-gold/15 text-gold-bright';
  if (polarity < 0) return 'bg-wuxing-fire/15 text-wuxing-fire';
  return 'bg-surface-raised text-ink-muted';
}
