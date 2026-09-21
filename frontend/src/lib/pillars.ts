/**
 * Chinese captions for the pillar-slot keys the API emits.
 *
 * `year | month | day | hour` are the four natal pillars; `extra<n>` slots are
 * 大运/流年 pillars scanned alongside them (神煞落点、伏吟反吟的对柱). The raw key
 * stays available to callers that want it in a `title`, so the caption never
 * becomes the only trace back to the response.
 */
const PILLAR_LABEL: Record<string, string> = {
  year: '年',
  month: '月',
  day: '日',
  hour: '时',
};

export function pillarLabel(position: string): string {
  return PILLAR_LABEL[position] ?? '运';
}

/**
 * Full pillar caption for readers: 年柱 / 月柱 / 日柱 / 时柱.
 *
 * `extra<n>` slots have no palace of their own — they are the 大运/流年 pillars the
 * engine scans against the four — so they caption as 运 rather than a fifth 柱.
 */
export function pillarColumnLabel(position: string): string {
  const head = PILLAR_LABEL[position];
  return head ? `${head}柱` : '运';
}
