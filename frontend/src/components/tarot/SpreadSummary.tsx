import type { TarotSpreadResponse } from '../../types/tarot';

interface SpreadSummaryProps {
  /** The completed draw. */
  spread: TarotSpreadResponse;
}

/**
 * Headline strip for a completed draw.
 *
 * Shows the real spread identity (bilingual name + description), echoes the
 * reader's question when one was given, and tallies the emphasis counts the
 * engine derives from the actual cards (major-arcana and reversals). Nothing
 * here is estimated — every figure comes from the response.
 */
export function SpreadSummary({ spread }: SpreadSummaryProps) {
  const total = spread.cards.length;
  const minor = total - spread.major_arcana_count;

  return (
    <div className="panel flex flex-col gap-4 p-5 sm:p-6">
      <div className="flex flex-col gap-1">
        <span className="label-caps">牌阵 · {spread.spread_name}</span>
        <span className="font-display text-2xl font-bold tracking-wide text-gold-bright text-glow-gold sm:text-3xl">
          {spread.spread_name_zh}
        </span>
        <p className="max-w-3xl text-sm leading-relaxed text-ink-muted">{spread.spread_description_zh}</p>
        <p className="text-xs leading-relaxed text-ink-muted">{spread.spread_description}</p>
      </div>

      {spread.question ? (
        <div className="flex items-start gap-2 rounded-element border border-rim-soft bg-surface px-3 py-2 text-sm">
          <span className="label-caps shrink-0 pt-0.5">求问</span>
          <span className="text-ink-variant">{spread.question}</span>
        </div>
      ) : null}

      <div className="gold-rule" />

      <div className="flex flex-wrap gap-x-6 gap-y-3">
        <Stat label="总牌数" value={total} />
        <Stat label="大阿卡纳" value={spread.major_arcana_count} dot="#F5D77F" />
        <Stat label="小阿卡纳" value={minor} dot="#818CF8" />
        <Stat label="逆位" value={spread.reversed_count} dot={spread.reversed_count > 0 ? '#F43F5E' : undefined} />
        <div className="flex flex-col gap-0.5">
          <span className="label-caps">正逆位</span>
          <span className="text-sm text-ink">{spread.allow_reversed ? '启用（正/逆位）' : '仅正位'}</span>
        </div>
      </div>
    </div>
  );
}

/** One emphasis tally with an optional colour dot. */
function Stat({ label, value, dot }: { label: string; value: number; dot?: string }) {
  return (
    <div className="flex items-center gap-2">
      {dot ? <span className="h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: dot }} /> : null}
      <span className="label-caps">{label}</span>
      <span className="numeric text-lg font-semibold text-ink">{value}</span>
    </div>
  );
}
