import type { ReactNode } from 'react';

import { ScoreLedger } from './ScoreLedger';
import type { DayMasterAnalysis } from '../../types/bazi';

/** Bilingual labels for the deterministic strength classification. */
const LEVEL_LABEL: Record<string, string> = {
  weak: 'Weak · 身弱',
  balanced: 'Balanced · 中和',
  strong: 'Strong · 身强',
};

const RING_RADIUS = 42;
const RING_CIRCUMFERENCE = 2 * Math.PI * RING_RADIUS;

interface StrengthDialProps {
  analysis: DayMasterAnalysis;
}

/**
 * Day-master strength dial (命局核心判定).
 *
 * The ring, the figure in its centre and the expandable ledger underneath all
 * read the same `strength` ScoreValue, so the arc length can be traced back to
 * the 得令/得地/得势 rows. 喜用/忌仇 are not repeated here: `YongshenPanel` shows
 * them together with the three methods that produced them (Task 15 注 2).
 */
export function StrengthDial({ analysis }: StrengthDialProps) {
  const score = analysis.strength;
  const offset = RING_CIRCUMFERENCE * (1 - Math.min(1, Math.max(0, score.value / 100)));

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-5">
        <div className="relative h-32 w-32 shrink-0">
          <svg viewBox="0 0 100 100" className="h-full w-full -rotate-90">
            <circle
              cx="50"
              cy="50"
              r={RING_RADIUS}
              fill="none"
              strokeWidth="8"
              stroke="currentColor"
              className="text-gold/10"
            />
            <circle
              cx="50"
              cy="50"
              r={RING_RADIUS}
              fill="none"
              strokeWidth="8"
              strokeLinecap="round"
              stroke="currentColor"
              className="text-gold"
              strokeDasharray={RING_CIRCUMFERENCE}
              strokeDashoffset={offset}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
            <span className="font-display text-2xl font-bold text-gold-bright">{analysis.label}</span>
            <span className="numeric mt-0.5 text-xs text-ink-muted">
              {score.value.toFixed(1)}/100
            </span>
          </div>
        </div>

        <dl className="flex flex-1 flex-col gap-1.5 text-sm">
          <StatRow label="日元">
            <span className="text-gold">
              {analysis.day_master}（{analysis.day_master_element}）
            </span>
          </StatRow>
          <StatRow label="定格">{LEVEL_LABEL[analysis.level] ?? analysis.level}</StatRow>
        </dl>
      </div>

      <ScoreLedger score={score} label="强弱三因子合计（得令 / 得地 / 得势）" />

      <p className="rounded-element border border-rim-soft bg-[#0e111a] p-3 text-sm leading-relaxed text-ink-variant">
        {analysis.summary}
      </p>
    </div>
  );
}

/** A caption/value line in the dial's statistics column. */
function StatRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-2">
      <dt className="text-ink-muted">{label}</dt>
      <dd className="text-ink">{children}</dd>
    </div>
  );
}
