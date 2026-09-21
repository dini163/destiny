import { useState } from 'react';

import { Icon } from './Icon';
import { SourceNote } from './SourceNote';
import type { ScoreValue } from '../../types/scoring';

interface ScoreLedgerProps {
  /** Engine score *with* its factor rows; a bare number is not accepted anywhere. */
  score: ScoreValue;
  label: string;
}

/**
 * Renders a rating together with the arithmetic behind it.
 *
 * The bar and the printed number both come from `score.value`; the expandable
 * table lists `score.factors` verbatim, in engine order. This is the only place
 * the app prints a percentage (spec §8.1).
 */
export function ScoreLedger({ score, label }: ScoreLedgerProps) {
  const [open, setOpen] = useState(false);
  const percent = Math.min(100, Math.max(0, score.value));

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-sm text-ink">{label}</span>
        <span className="flex items-baseline gap-2">
          <span className="numeric text-sm text-gold-bright">{score.value.toFixed(1)}</span>
          <span className="label-caps text-ink-muted">{score.tier}</span>
        </span>
      </div>

      <div className="h-1.5 overflow-hidden rounded-full bg-surface-raised" role="presentation">
        <div className="h-full rounded-full bg-gold" style={{ width: `${percent}%` }} />
      </div>

      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        aria-expanded={open}
        className="label-caps flex items-center gap-1 self-start text-ink-muted hover:text-gold-soft"
      >
        <Icon name="chevronDown" size={12} className={open ? 'rotate-180' : undefined} />
        {open ? '收起赋分账本' : '展开赋分账本'}
      </button>

      {open ? (
        <table className="w-full text-xs">
          <caption className="sr-only">{`${label}的赋分账本`}</caption>
          <tbody>
            {score.factors.map((factor, index) => (
              <tr key={factor.rule} className="border-t border-rim">
                <th scope="row" className="py-1.5 pr-2 text-left font-normal text-ink-variant">
                  {factor.label}
                </th>
                <td className="numeric px-2 py-1.5 text-right text-ink">
                  {formatDelta(factor.delta, index === 0)}
                </td>
                <td className="py-1.5 pl-2 text-right">
                  <SourceNote source={factor.source} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </div>
  );
}

/** The base row is a plain amount; the increments carry their sign. */
function formatDelta(delta: number, is_base: boolean): string {
  const text = Math.abs(delta).toFixed(1);
  if (is_base) return text;
  return delta < 0 ? `-${text}` : `+${text}`;
}
