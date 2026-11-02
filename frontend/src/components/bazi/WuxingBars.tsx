import { wuxingBg, wuxingLabelEn, wuxingText } from '../../lib/wuxing';
import type { WuxingScore } from '../../types/bazi';

interface WuxingBarsProps {
  /** Five-element scores in the engine's 木火土金水 order. */
  scores: WuxingScore[];
  /** Elements absent from the eight characters. */
  missing: string[];
}

/**
 * Five-element quantitative distribution (五行能量量化分布).
 *
 * Bar length is proportional to each element's weighted score (which folds in hidden
 * stems); the headcount among the eight primary characters is shown alongside. Every
 * value comes straight from the engine — sorted heaviest-first purely for legibility.
 */
export function WuxingBars({ scores, missing }: WuxingBarsProps) {
  const total = scores.reduce((sum, item) => sum + item.score, 0);
  const ordered = [...scores].sort((a, b) => b.score - a.score);

  return (
    <div className="flex flex-col gap-3">
      {ordered.map((item) => {
        const percent = total > 0 ? Math.round((item.score / total) * 100) : 0;
        return (
          <div key={item.element} className="flex flex-col gap-1">
            <div className="flex items-center justify-between text-sm">
              <span className={`font-medium ${wuxingText(item.element)}`}>
                {item.element}
                <span className="ml-1 text-xs text-ink-muted">{wuxingLabelEn(item.element)}</span>
              </span>
              <span className="numeric text-xs text-ink-muted">
                {item.count} 见 · {percent}%
              </span>
            </div>
            <div className="h-2.5 w-full overflow-hidden rounded-full bg-[var(--field-bg)]">
              <div
                className={`h-full rounded-full ${wuxingBg(item.element)}`}
                style={{ width: `${percent}%` }}
                title={`加权分 ${item.score.toFixed(2)}`}
              />
            </div>
          </div>
        );
      })}

      <p className="mt-1 flex items-center gap-2 rounded-element border border-rim-soft bg-[var(--field-bg)] px-3 py-2 text-xs text-ink-variant">
        <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-gold" />
        {missing.length > 0 ? `五行缺：${missing.join('、')}` : '五行俱全，无明显偏枯。'}
      </p>
    </div>
  );
}
