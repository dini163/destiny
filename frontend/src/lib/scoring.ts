/**
 * Score-delta printing shared by every ledger and fired list.
 *
 * Deltas are engine numbers; the app prints them in exactly two shapes, and
 * which one is in play is decided by the engine's own granularity, not by the
 * page. Both shapes live here so the column a reader compares across systems
 * has one place to change (`conventions.test.ts` 不变式 5).
 */

/**
 * Ledger shape: one decimal, explicit sign — `-2.5` / `+8.0`.
 *
 * `isBase` marks a ledger's base row, the amount everything else is added to;
 * it carries a magnitude, not a direction, so it prints unsigned.
 */
export function formatDelta(delta: number, isBase = false): string {
  const text = Math.abs(delta).toFixed(1);
  if (isBase) return text;
  return delta < 0 ? `-${text}` : `+${text}`;
}

/**
 * 梅花 rank shape: whole steps only (the 吉凶指数 moves in ±1…±8), so no decimal
 * noise and a true minus glyph on the way down; zero is a plain `0`, not `+0`.
 */
export function formatStepDelta(delta: number): string {
  if (delta > 0) return `+${delta}`;
  if (delta < 0) return `−${Math.abs(delta)}`;
  return '0';
}
