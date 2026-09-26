/**
 * 奇门遁甲 (Qi Men Dun Jia) presentation helpers.
 *
 * The backend returns the real board (九星 / 八门 / 八神 / 天地盘干, each with its
 * 五行·吉凶·类象). These maps supply *presentation only* — element colours, 吉凶
 * tones, 三奇/六仪 tinting and grid placement — so nothing interpretive is invented
 * on the client. Colour strings are written out in full so Tailwind's scanner keeps them.
 */

import type { CSSProperties } from 'react';

// --- 五行 element tone ------------------------------------------------------

/** Text colour for a 五行 element (木火土金水). */
export function elementText(element: string): string {
  switch (element) {
    case '木':
      return 'text-wuxing-wood';
    case '火':
      return 'text-wuxing-fire';
    case '土':
      return 'text-wuxing-earth';
    case '金':
      return 'text-wuxing-metal';
    case '水':
      return 'text-wuxing-water';
    default:
      return 'text-ink-muted';
  }
}

/** Small square/dot fill for a 五行 element. */
export function elementDot(element: string): string {
  switch (element) {
    case '木':
      return 'bg-wuxing-wood';
    case '火':
      return 'bg-wuxing-fire';
    case '土':
      return 'bg-wuxing-earth';
    case '金':
      return 'bg-wuxing-metal';
    case '水':
      return 'bg-wuxing-water';
    default:
      return 'bg-ink-muted';
  }
}

// --- 吉凶 tone (九星 / 八门 / 八神) -----------------------------------------

/** Text colour for a 吉 | 凶 | 中平 luck label. */
export function luckText(luck: string): string {
  if (luck === '吉') return 'text-gold-bright';
  if (luck === '凶') return 'text-wuxing-fire';
  return 'text-ink-muted'; // 中平
}

/** Tinted chip classes for a 吉 | 凶 | 中平 luck label. */
export function luckChip(luck: string): string {
  if (luck === '吉') return 'bg-gold/15 text-gold-bright';
  if (luck === '凶') return 'bg-wuxing-fire/15 text-wuxing-fire';
  return 'bg-surface-raised text-ink-muted'; // 中平
}

// --- 三奇六仪 干 tinting ----------------------------------------------------

const THREE_QI = new Set(['乙', '丙', '丁']);

/** 三奇 | 六仪 — the two families of the 遁甲 plate. */
export function ganKind(gan: string): '三奇' | '六仪' {
  return THREE_QI.has(gan) ? '三奇' : '六仪';
}

/** Text colour for a 天干: 三奇 in bright gold, 六仪 in muted parchment. */
export function ganText(gan: string): string {
  return THREE_QI.has(gan) ? 'text-gold-bright' : 'text-ink-variant';
}

// --- 洛书九宫 grid placement (南上北下) -------------------------------------

/** CSS grid placement for a palace cell from its 0-based row/col. */
export function palacePlacement(row: number, col: number): CSSProperties {
  return { gridRowStart: row + 1, gridColumnStart: col + 1 };
}
