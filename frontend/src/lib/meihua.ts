/**
 * 梅花易数 (Plum Blossom) presentation helpers.
 *
 * The backend returns the real derivation (起卦数, 本/互/变卦, 体用生克, 卦气旺衰,
 * 吉凶指数 ledger). These maps supply *presentation only* — method labels, verdict
 * tones and score-band colours — so nothing interpretive is invented on the client.
 * Colour strings are written out in full so Tailwind's scanner keeps them.
 */

import type { MeihuaMethod } from '../types/meihua';

// --- 起卦方法 ---------------------------------------------------------------

/** A selectable raising method with a short factual hint. */
export interface MeihuaMethodOption {
  value: MeihuaMethod;
  label: string;
  hint: string;
}

/** The two 起卦法 the engine supports (see `app.engines.meihua`). */
export const MEIHUA_METHODS: readonly MeihuaMethodOption[] = [
  {
    value: 'time',
    label: '年月日时',
    hint: '以起卦农历「年支序＋月＋日」取上卦、「再加时辰序」取下卦与动爻，先天卦数（乾一兑二离三震四巽五坎六艮七坤八）。',
  },
  {
    value: 'number',
    label: '报数起卦',
    hint: '报一至三个正整数：一数加时辰取上下卦与动爻；两数分取上下卦、合计取动爻；三数首二取上下卦、总数取动爻。',
  },
];

/** Chinese label for a raising method, echoing the raw value when unknown. */
export function meihuaMethodLabel(method: MeihuaMethod | string): string {
  return MEIHUA_METHODS.find((option) => option.value === method)?.label ?? String(method);
}

// --- 吉凶 verdict tone ------------------------------------------------------

/** Verdicts the engine can return, best → worst. */
const FAVOURABLE = new Set(['上吉', '吉', '小吉']);
const UNFAVOURABLE = new Set(['小凶', '凶']);

/** Text colour class for a 综合吉凶 verdict label. */
export function verdictText(verdict: string): string {
  if (FAVOURABLE.has(verdict)) return 'text-gold-bright';
  if (UNFAVOURABLE.has(verdict)) return 'text-wuxing-fire';
  return 'text-ink-variant';
}

/** Tinted chip classes for a 体用生克 verdict (大吉/吉/小吉/小凶/大凶). */
export function relationChip(verdict: string): string {
  if (verdict === '大吉' || verdict === '吉') return 'bg-gold/15 text-gold-bright';
  if (verdict === '小吉') return 'bg-wuxing-wood/15 text-wuxing-wood';
  if (verdict === '小凶') return 'bg-wuxing-earth/15 text-wuxing-earth';
  return 'bg-wuxing-fire/15 text-wuxing-fire'; // 大凶
}

// --- 吉凶指数 band ----------------------------------------------------------

/** Bar-fill class for the 0-100 吉凶指数, banded by favourability. */
export function scoreBarClass(score: number): string {
  if (score >= 70) return 'bg-gold-bright';
  if (score >= 55) return 'bg-wuxing-wood';
  if (score >= 45) return 'bg-ink-muted';
  if (score >= 30) return 'bg-wuxing-earth';
  return 'bg-wuxing-fire';
}

/** Signed-delta colour for a ledger factor (positive gold, negative fire, zero muted). */
export function deltaText(delta: number): string {
  if (delta > 0) return 'text-gold-bright';
  if (delta < 0) return 'text-wuxing-fire';
  return 'text-ink-muted';
}

// --- Positions --------------------------------------------------------------

/** 初爻…上爻, indexed by (position − 1). */
const POSITION_ZH = ['初爻', '二爻', '三爻', '四爻', '五爻', '上爻'] as const;

/** Chinese name for a line position 1-6 (bottom to top). */
export function movingPositionLabel(position: number): string {
  return POSITION_ZH[position - 1] ?? `${position} 爻`;
}
