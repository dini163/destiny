import type { TransitDayCell } from '../../../types/baziLiuri';
import { tierClass } from './tier';

/** 「馀事勿取」在库给的 `yi` 里时，它是"今日诸事不宜"的唯一信号 —— 排第一且永不被截掉。 */
const FALL_BACK_YI = '馀事勿取';
const PREVIEW_COUNT = 2;

/** 决策 6：它占位但不让位。它排第一，其余按库序补到 2 条为止。 */
function yiPreview(yi: string[]): string[] {
  const head = yi.includes(FALL_BACK_YI) ? [FALL_BACK_YI] : [];
  const rest = yi.filter((item) => item !== FALL_BACK_YI);
  return [...head, ...rest].slice(0, PREVIEW_COUNT);
}

/**
 * 矩阵里的一格：公历月日 + 干支、农历日、吉凶度与档位、宜忌各 2 条预览。
 *
 * 分数与档位是服务端三段账本读出来的两个数，这里不重算；宜忌是外部历法库的历注，
 * 与分数不同源，所以同格并列而不合并。整格是一个按钮：点它 = 把该日交回页面重发一次
 * 请求，今日与聚焦两态都由父级比日期后传下来，本组件不含任何状态。
 */
export function LiuriDayCell({
  cell,
  isToday,
  isFocused,
  onSelect,
}: {
  cell: TransitDayCell;
  isToday: boolean;
  isFocused: boolean;
  onSelect: (solarDate: string) => void;
}) {
  const yi = yiPreview(cell.almanac.yi);
  const ji = cell.almanac.ji.slice(0, PREVIEW_COUNT);
  return (
    <button
      type="button"
      onClick={() => onSelect(cell.solar_date)}
      aria-pressed={isFocused}
      className={`flex flex-col gap-1.5 rounded-element border p-3 text-left transition hover:border-rim-strong ${
        isFocused
          ? 'border-gold bg-gold/10'
          : isToday
            ? 'border-rim-strong bg-[#0e111a]'
            : 'border-rim bg-[#0e111a]'
      }`}
    >
      <span className="flex items-baseline justify-between gap-1">
        <span className="numeric text-xs text-ink-muted">{cell.solar_date.slice(5)}</span>
        <span className="font-display text-sm text-gold-soft">{cell.ganzhi}</span>
      </span>
      <span className="flex items-baseline justify-between gap-1">
        <span className="text-xs text-ink-variant">{cell.lunar_day}</span>
        {isToday ? <span className="label-caps text-gold">今日</span> : null}
      </span>
      <span className="flex items-baseline gap-1.5">
        <span className={`numeric text-lg ${tierClass(cell.tier)}`}>
          {Math.round(cell.value)}
        </span>
        <span className={`label-caps ${tierClass(cell.tier)}`}>{cell.tier}</span>
      </span>
      <YiJiLine prefix="宜" items={yi} total={cell.almanac.yi.length} />
      <YiJiLine prefix="忌" items={ji} total={cell.almanac.ji.length} />
    </button>
  );
}

/** 预览 2 条，全量在聚焦卡；`+N` 说的是"还有 N 条"，不是"还有别的宜忌类别"。 */
function YiJiLine({ prefix, items, total }: { prefix: string; items: string[]; total: number }) {
  return (
    <span className="flex flex-wrap items-baseline gap-1 text-xs leading-snug">
      <span className="label-caps text-ink-muted">{prefix}</span>
      {items.length === 0 ? (
        <span className="text-ink-muted">—</span>
      ) : (
        items.map((item) => <span key={item} className="text-ink-variant">{item}</span>)
      )}
      {total > items.length ? <span className="numeric text-ink-muted">+{total - items.length}</span> : null}
    </span>
  );
}
