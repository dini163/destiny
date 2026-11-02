import { tierClass } from '../liuri/tier';
import type { TransitHourCell } from '../../../types/baziLiushi';

/** 格里最多铺开两条命中，其余以 `+N` 交代：十二格并排，宽度是唯一稀缺资源。 */
const PREVIEW_COUNT = 2;

/**
 * 十二格之一：支 + 钟面起、时柱、分值与档位、日主临时支、时段命中预览。
 *
 * 分值与档位是服务端四段账本读出的两个数，这里不重算；`qi_strength` 是描述不是分数，
 * 所以它排在分值之下而不是之色。整格是一个按钮：点它 = 把这一支交回页面重发一次请求，
 * 峰值与聚焦两态都由父级算好后传下来，本组件不含任何状态。
 */
export function LiushiHourCell({
  cell,
  isPeak,
  isFocused,
  onSelect,
}: {
  cell: TransitHourCell;
  isPeak: boolean;
  isFocused: boolean;
  onSelect: (zhi: string) => void;
}) {
  const color = tierClass(cell.tier);
  const hits = cell.hour_hits.slice(0, PREVIEW_COUNT);
  return (
    <button
      type="button"
      onClick={() => onSelect(cell.zhi)}
      aria-pressed={isFocused}
      className={`flex flex-col gap-1.5 rounded-element border p-3 text-left transition hover:border-rim-strong ${
        isFocused
          ? 'border-gold bg-gold/10'
          : isPeak
            ? 'border-rim-strong bg-[var(--field-bg)]'
            : 'border-rim bg-[var(--field-bg)]'
      }`}
    >
      <span className="flex items-baseline justify-between gap-1">
        <span className="font-display text-base text-gold-soft">{cell.zhi}</span>
        <span className="numeric text-[11px] text-ink-muted">{cell.start_clock}</span>
      </span>
      <span className="flex items-baseline justify-between gap-1">
        <span className="numeric text-xs text-ink-variant">{cell.ganzhi}</span>
        {isPeak ? <span className="label-caps text-gold">峰值</span> : null}
      </span>
      <span className="flex items-baseline gap-1.5">
        <span className={`numeric text-lg ${color}`}>{Math.round(cell.value)}</span>
        <span className={`label-caps ${color}`}>{cell.tier}</span>
      </span>
      <span className="text-[11px] leading-snug text-ink-muted">日主临时支·{cell.qi_strength}</span>
      {hits.length === 0 ? (
        <span className="label-caps text-ink-muted">时段无账</span>
      ) : (
        <span className="flex flex-col gap-0.5 text-[11px] leading-snug">
          {hits.map((hit) => (
            <span key={hit.key} className="truncate text-ink-variant">
              {hit.label}
              <span className={`numeric ml-1 ${hit.delta >= 0 ? 'text-wuxing-wood' : 'text-wuxing-fire'}`}>
                {hit.delta > 0 ? `+${hit.delta}` : hit.delta}
              </span>
            </span>
          ))}
          {cell.hour_hits.length > hits.length ? (
            <span className="numeric text-ink-muted">+{cell.hour_hits.length - hits.length}</span>
          ) : null}
        </span>
      )}
    </button>
  );
}
