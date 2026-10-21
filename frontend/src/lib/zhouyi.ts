/**
 * Zhouyi / Liuyao (周易六爻) presentation helpers shared by the divination page.
 *
 * The backend returns the real cast: line values (6/7/8/9), najia stem/branch,
 * 六亲, 六神, 世应, moving flags and the classical 卦辞/爻辞. These maps supply
 * *presentation only* — line-value semantics, 六神 colours, method labels and
 * position names — so nothing interpretive (用神/伏神/神煞, which the engine does
 * not compute) is invented on the client. Colour strings are written out in full
 * so Tailwind's scanner keeps them and SVG/CSS strokes stay stable.
 */

import type { CastMethod } from '../types/zhouyi';

// --- Line value semantics (三枚铜钱) ----------------------------------------

/** What a coin-sum line value means, and how it is marked on the chart. */
export interface LineValueMeta {
  /** Classical name: 老阴 / 少阳 / 少阴 / 老阳. */
  name: string;
  /** Moving-line marker: ○ for old yang, × for old yin; null when static. */
  mark: string | null;
  /** Whether this value is a moving line (动爻). */
  moving: boolean;
}

const LINE_VALUE_META: Record<number, LineValueMeta> = {
  6: { name: '老阴', mark: '×', moving: true },
  7: { name: '少阳', mark: null, moving: false },
  8: { name: '少阴', mark: null, moving: false },
  9: { name: '老阳', mark: '○', moving: true },
};

/** Semantics for a line value (6/7/8/9), with a neutral fallback. */
export function lineValueMeta(value: number): LineValueMeta {
  return LINE_VALUE_META[value] ?? { name: String(value), mark: null, moving: false };
}

// --- Casting methods --------------------------------------------------------

/** A selectable casting method with a short factual hint. */
export interface CastMethodOption {
  value: CastMethod;
  label: string;
  hint: string;
}

/**
 * The three casting methods the engine supports (see `app.engines.zhouyi`).
 * Hints describe the real algorithm, not invented flavour.
 */
export const CAST_METHODS: readonly CastMethodOption[] = [
  { value: 'three_coin', label: '铜钱摇卦', hint: '三枚铜钱六掷，由权威算法真实模拟，字(2)/背(3) 定点成爻。' },
  { value: 'manual', label: '手动录入', hint: '自行录入六掷铜钱正背（字=2、背=3），每掷三枚，复现古法摇卦。' },
  { value: 'time', label: '梅花时间', hint: '梅花易数：以起卦农历年、月、日、时数取上下卦与动爻。' },
];

/** Chinese label for a cast method, echoing the raw value when unknown. */
export function methodLabel(method: CastMethod | string): string {
  return CAST_METHODS.find((option) => option.value === method)?.label ?? String(method);
}

// --- Positions --------------------------------------------------------------

/** 初爻…上爻, indexed by (position - 1). */
const POSITION_ZH = ['初爻', '二爻', '三爻', '四爻', '五爻', '上爻'] as const;

/** Chinese name for a line position 1-6 (bottom to top). */
export function positionLabel(position: number): string {
  return POSITION_ZH[position - 1] ?? `${position} 爻`;
}

// --- 六神 (six spirits) ------------------------------------------------------

/** Traditional colour association for each of the six 六神. */
const LIUSHEN_COLOR: Record<string, string> = {
  青龙: '#2DD4BF',
  朱雀: '#F43F5E',
  勾陈: '#EAB308',
  螣蛇: '#A855F7',
  白虎: '#E2E2EB',
  玄武: '#38BDF8',
};

/** Accent colour for a 六神 name, with a neutral fallback. */
export function liushenColor(name: string): string {
  return LIUSHEN_COLOR[name] ?? '#948C79';
}

// --- Coins (manual method) ---------------------------------------------------

/** A coin face: 2 = 字 (阴面), 3 = 背 (阳面). */
export type CoinFace = 2 | 3;

/** Chinese label for a coin face. */
export function coinLabel(face: number): string {
  return face === 3 ? '背' : '字';
}

/** A neutral starting throw (one 背 + two 字 = 7, young yang) for the editor. */
export function defaultThrow(): CoinFace[] {
  return [3, 2, 2];
}

/** Six throws of three coins, the manual method's input shape. */
export function defaultManualCoins(): CoinFace[][] {
  return Array.from({ length: 6 }, () => defaultThrow());
}
