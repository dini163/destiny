import { useI18n } from '../../../i18n/context';
import { tierClass } from '../liuri/tier';
import type { TransitHourCell } from '../../../types/baziLiushi';

/**
 * 峰值备忘录：那一格为什么高（或低）。
 *
 * 「较本日 ±N 分」是这一格与 `day_score` 的差，也就是它自己那几行 `shi.` 的合计 ——
 * 两个数都在响应里，这里只做一次减法，不引入第二套分值口径。
 *
 * `hour_hits` 为空时说的是另一件事：这一格的分不是时辰给的，是日头给的。这句话必须
 * 存在，否则读者会以为空列表 = 页面漏了。
 */
export function LiushiPeakNote({ cell, dayValue }: { cell: TransitHourCell; dayValue: number }) {
  const { t } = useI18n();
  const gap = Math.round((cell.value - dayValue) * 10) / 10;
  return (
    <div className="flex flex-col gap-2 rounded-element border border-rim bg-[var(--field-bg)] px-4 py-3">
      <span className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <span className="font-display text-lg text-gold-soft">{cell.ganzhi}</span>
        <span className="numeric text-xs text-ink-muted">
          {cell.start_clock}–{cell.end_clock}
        </span>
        <span className={`numeric text-sm ${tierClass(cell.tier)}`}>
          {t('{{v}} 分 · {{tier}}', { v: cell.value, tier: t(cell.tier) })}
        </span>
        <span className="numeric text-xs text-ink-variant">
          {t('较本日 {{gap}} 分', { gap: gap >= 0 ? `+${gap}` : `${gap}` })}
        </span>
      </span>
      <span className="text-xs text-ink-muted">{t('日主临时支·{{s}}', { s: t(cell.qi_strength) })}</span>
      {cell.hour_hits.length === 0 ? (
        <p className="text-sm leading-relaxed text-ink-variant">
          {t('时段本身没有加账 —— 这一格的分值来自日头那三段（流年、流月、流日）。')}
        </p>
      ) : (
        <ul className="flex flex-col gap-1">
          {cell.hour_hits.map((hit) => (
            <li key={hit.key} className="flex items-baseline justify-between gap-3 text-sm">
              <span className="text-ink-variant">{t(hit.label)}</span>
              <span
                className={`numeric ${hit.delta >= 0 ? 'text-wuxing-wood' : 'text-wuxing-fire'}`}
              >
                {hit.delta > 0 ? `+${hit.delta}` : hit.delta}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
