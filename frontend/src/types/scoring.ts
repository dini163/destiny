/**
 * Score ledger mirroring `backend/app/schemas/scoring.py`.
 *
 * `factors[0]` is the base row (its `rule` ends with `.base`); the invariant
 * `sum(delta) === value` holds for every ledger the API returns, clamping
 * included, so a rating can always be opened and checked.
 */
export interface ScoreFactor {
  /** Machine-readable rule key, e.g. `strength.dedi.share` or `career.officer.present`. */
  rule: string;
  /** Short Chinese name, e.g. 得地. */
  label: string;
  delta: number;
  /** Book citation, or an explicit 模型参数 / 本系统纲要 declaration. */
  source: string;
}

export interface ScoreValue {
  value: number;
  /** Chinese tier label, e.g. 身弱 or 顺. */
  tier: string;
  factors: ScoreFactor[];
}
