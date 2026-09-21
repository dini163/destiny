import type { TransitYear } from '../../../types/baziTransit';

interface TransitYearTableProps {
  years: TransitYear[];
  /** 已展开十二节气月的那一年；未请求聚焦年时为 null。 */
  focusYear: number | null;
  /** 点行即请这一年下钻；再点当前年则由页面收回。 */
  onFocus: (year: number) => void;
}

/**
 * 流年表：一年一行，行本身就是下钻的按钮。
 *
 * 分数条与档位都取自 `score`，条宽只是把 `value` 画出来（`value` 已在 0—100 内，
 * 由后端截断并记进账本），前端不做任何归一化或二次评级。命中族 chips 取 `fired`
 * 里出现过的族，顺序即首次命中顺序，与展开后的断语清单同序。
 */
export function TransitYearTable({ years, focusYear, onFocus }: TransitYearTableProps) {
  return (
    <ul className="flex flex-col gap-2">
      {years.map((year) => (
        <li key={year.year}>
          <button
            type="button"
            onClick={() => onFocus(year.year)}
            aria-pressed={year.year === focusYear}
            className={`flex w-full flex-wrap items-center gap-x-4 gap-y-2 rounded-element border px-4 py-3 text-left transition ${
              year.year === focusYear
                ? 'border-gold/60 bg-gold/10'
                : 'border-rim bg-[#0e111a] hover:border-rim-strong'
            }`}
          >
            <span className="flex w-14 shrink-0 flex-col">
              <span className="numeric text-base text-ink">{year.year}</span>
              <span className="label-caps text-ink-muted">虚{year.age}</span>
            </span>

            <span className="flex w-24 shrink-0 flex-col">
              <span className="font-display text-base text-gold-soft">{year.pillar.ganzhi}</span>
              <span className="label-caps text-ink-muted">{year.ten_god.god}</span>
            </span>

            <span className="flex min-w-[9rem] flex-1 flex-col gap-1">
              <span className="flex items-baseline justify-between gap-2">
                <span className="label-caps text-ink-muted">{year.dayun_ganzhi ?? '未起运'}</span>
                <span className="flex items-baseline gap-2">
                  <span className="numeric text-sm text-gold-bright">{year.score.value.toFixed(1)}</span>
                  <span className="label-caps text-ink">{year.score.tier}</span>
                </span>
              </span>
              <ScoreBar value={year.score.value} />
            </span>

            <span className="flex flex-wrap items-center justify-end gap-1">
              {familiesOf(year).map((family) => (
                <span
                  key={family}
                  className="label-caps normal-case rounded-element border border-rim-strong px-1.5 py-0.5 text-ink-muted"
                >
                  {family}
                </span>
              ))}
            </span>
          </button>
        </li>
      ))}
    </ul>
  );
}

/** 命中族，按首次出现去重；机器键直出，与断语清单的中文族名对照即可。 */
function familiesOf(year: TransitYear): string[] {
  const seen: string[] = [];
  for (const row of year.fired) if (!seen.includes(row.family)) seen.push(row.family);
  return seen;
}

/** The engine's own 0—100 figure, drawn as a bar. */
function ScoreBar({ value }: { value: number }) {
  return (
    <span className="block h-1.5 overflow-hidden rounded-full bg-surface-raised" role="presentation">
      <span className="block h-full rounded-full bg-gold" style={{ width: `${value}%` }} />
    </span>
  );
}
