import type { ReactNode } from 'react';

import { wuxingChip } from '../../lib/wuxing';
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
 * The ring fills to `strength_ratio` (support ÷ total). Everything shown — level,
 * support/drain scores, favourable (喜用神) and unfavourable (忌神) elements and the
 * summary — is the engine's deterministic analysis; no interpretive copy is invented.
 */
export function StrengthDial({ analysis }: StrengthDialProps) {
  const ratio = Math.min(1, Math.max(0, analysis.strength_ratio));
  const offset = RING_CIRCUMFERENCE * (1 - ratio);
  const percent = Math.round(ratio * 100);

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
            <span className="numeric mt-0.5 text-xs text-ink-muted">{percent}/100</span>
          </div>
        </div>

        <dl className="flex flex-1 flex-col gap-1.5 text-sm">
          <StatRow label="日元">
            <span className="text-gold">
              {analysis.day_master}（{analysis.day_master_element}）
            </span>
          </StatRow>
          <StatRow label="扶助分">
            <span className="numeric">{analysis.support_score.toFixed(1)}</span>
          </StatRow>
          <StatRow label="克泄分">
            <span className="numeric">{analysis.drain_score.toFixed(1)}</span>
          </StatRow>
          <StatRow label="定格">{LEVEL_LABEL[analysis.level] ?? analysis.level}</StatRow>
        </dl>
      </div>

      <div className="flex flex-col gap-2">
        <ElementTags label="喜用神" tone="favorable" elements={analysis.favorable_elements} />
        <ElementTags label="忌仇神" tone="unfavorable" elements={analysis.unfavorable_elements} />
      </div>

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

/** A row of five-element tags for the favourable / unfavourable elements. */
function ElementTags({
  label,
  tone,
  elements,
}: {
  label: string;
  tone: 'favorable' | 'unfavorable';
  elements: string[];
}) {
  const dot = tone === 'favorable' ? 'bg-wuxing-wood' : 'bg-wuxing-fire';
  return (
    <div className="flex items-center justify-between gap-2 rounded-element bg-[#0e111a] px-3 py-2">
      <span className="flex items-center gap-1.5 text-sm text-ink">
        <span className={`h-2 w-2 shrink-0 rounded-full ${dot}`} />
        {label}
      </span>
      <span className="flex flex-wrap items-center justify-end gap-1.5">
        {elements.length > 0 ? (
          elements.map((element) => (
            <span
              key={element}
              className={`rounded-element px-2 py-0.5 text-xs font-medium ${wuxingChip(element)}`}
            >
              {element}
            </span>
          ))
        ) : (
          <span className="text-xs text-ink-muted">—</span>
        )}
      </span>
    </div>
  );
}
