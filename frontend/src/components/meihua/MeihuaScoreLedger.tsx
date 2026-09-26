import type { MeihuaCast } from '../../types/meihua';
import { deltaText, scoreBarClass, verdictText } from '../../lib/meihua';
import { formatStepDelta } from '../../lib/scoring';

interface MeihuaScoreLedgerProps {
  /** The complete cast — supplies the 吉凶指数, its factor ledger and the 综合断语. */
  cast: MeihuaCast;
}

/**
 * The 吉凶指数 ledger (梅花易数 quantified verdict).
 *
 * Shows the 0‑100 index, a banded bar, every signed factor that produced it
 * (体用生克 / 卦气旺衰 / 互卦 / 变卦) and the engine's 综合断语. The arithmetic is
 * exposed rather than hidden, matching the project's "show the working" ethos;
 * all labels, details and deltas are the backend's own.
 */
export function MeihuaScoreLedger({ cast }: MeihuaScoreLedgerProps) {
  const { score, verdict, score_factors, summary } = cast;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-2">
        <div className="flex items-end justify-between gap-3">
          <div className="flex flex-col">
            <span className="label-caps">吉凶指数 · FORTUNE INDEX</span>
            <div className="flex items-baseline gap-2">
              <span className="numeric text-4xl font-bold leading-none text-gold-bright">{score}</span>
              <span className="numeric text-sm text-ink-muted">/ 100</span>
            </div>
          </div>
          <span className={`font-display text-xl font-semibold ${verdictText(verdict)}`}>{verdict}</span>
        </div>

        <div className="h-2 w-full overflow-hidden rounded-full bg-[#0e111a] ring-1 ring-inset ring-rim">
          <div className={`h-2 rounded-full ${scoreBarClass(score)}`} style={{ width: `${score}%` }} />
        </div>
      </div>

      <ul className="flex flex-col gap-1.5">
        {score_factors.map((factor) => (
          <li
            key={factor.label}
            className="flex items-start gap-3 rounded-element border border-rim-soft bg-surface/50 px-3 py-2"
          >
            <div className="flex min-w-0 flex-1 flex-col">
              <span className="text-xs font-semibold text-ink">{factor.label}</span>
              <span className="text-[11px] leading-snug text-ink-muted">{factor.detail}</span>
            </div>
            <span className={`numeric shrink-0 text-sm font-semibold ${deltaText(factor.delta)}`}>
              {formatStepDelta(factor.delta)}
            </span>
          </li>
        ))}
      </ul>

      <div className="gold-rule" />

      <p className="font-display text-sm leading-relaxed text-ink-variant">
        <span className="label-caps mr-2 align-middle">综合断语</span>
        {summary}
      </p>
    </div>
  );
}
