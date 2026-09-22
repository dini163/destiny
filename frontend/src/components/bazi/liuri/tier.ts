/** 顺 / 平 / 滞 三档的文字色：流日矩阵与流时十二格共用同一张色标。 */
const TIER_CLASS: Record<string, string> = {
  顺: 'text-wuxing-wood',
  平: 'text-ink-muted',
  滞: 'text-wuxing-fire',
};

/** 未知档位回落到正文色：账本换了词而页面不炸，是这一处兜底的唯一用途。 */
export function tierClass(tier: string): string {
  return TIER_CLASS[tier] ?? 'text-ink';
}
