import { useState } from 'react';

import { yiPreview } from '../liuri/LiuriDayCell';
import type { ShiftDirection } from '../liuri/LiuriSegmentHeader';
import { TransitFiredList } from '../transit/TransitFiredList';
import { ResultCard } from '../../ui/ResultCard';
import type { BaziLiushiResult } from '../../../types/baziLiushi';

const WEEKDAY_HEAD = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'] as const;

/**
 * 换日三键。不共用 `LiuriSegmentHeader` 那份 `SHIFT_ACTIONS`：它的文案是「上一段 /
 * 今日 / 下一段」，说的是节气月段，而这里的三个键挪的是一天 —— 同一段代码在两个页面上
 * 指两种粒度，读的人只会以为其中一处是笔误。
 */
const DAY_SHIFT_ACTIONS: ReadonlyArray<{ direction: ShiftDirection; label: string }> = [
  { direction: -1, label: '上一日' },
  { direction: 0, label: '今日' },
  { direction: 1, label: '下一日' },
];

/** 一条事实：标签 + 值。缺值即整条不渲染，不留 `undefined` 在页面上。 */
function Fact({ label, value }: { label: string; value: string | number | null | undefined }) {
  if (value === null || value === undefined || value === '') return null;
  return (
    <span className="flex items-baseline gap-1 text-xs">
      <span className="label-caps text-ink-muted">{label}</span>
      <span className="numeric text-ink">{value}</span>
    </span>
  );
}

/**
 * 页头：这一天的年月日段回显 + 换日三键 + 日头那三段账与历注。
 *
 * 它把"十二格是从哪一天摊出来的"说清楚：`{year_ganzhi}年 {month_ganzhi}月 · {day_ganzhi}日`
 * 一整串都取自响应，前端不重算月界（决策 9）。宜忌走 `yiPreview`，与流日矩阵格同一口径
 * —— 两处两种截法会让读者以为它们在说不同的事。
 *
 * 「本日命中」默认折起：十二格与波形才是这一页的主角，日头那十行摊开会把它们推到下屏。
 */
export function LiushiDayHeader({
  result,
  busy,
  onShift,
}: {
  result: BaziLiushiResult;
  busy: boolean;
  onShift: (direction: ShiftDirection) => void;
}) {
  const [open, setOpen] = useState(false);
  const yi = yiPreview(result.day_almanac.yi);
  return (
    <ResultCard
      eyebrow="HOURS OF A DAY"
      title={`${result.year_ganzhi}年 ${result.month_ganzhi}月 · ${result.day_ganzhi}日`}
      icon="sun"
      actions={
        <span className="flex items-center gap-2">
          {DAY_SHIFT_ACTIONS.map((action) => (
            <button
              key={action.direction}
              type="button"
              onClick={() => onShift(action.direction)}
              disabled={busy}
              className="rounded-element border border-rim px-2.5 py-1 text-xs text-ink-variant transition hover:border-rim-strong disabled:opacity-50"
            >
              {action.label}
            </button>
          ))}
        </span>
      }
    >
      <div className="flex flex-wrap items-baseline gap-x-5 gap-y-2">
        <Fact label="公历" value={result.solar_date} />
        <Fact label="星期" value={WEEKDAY_HEAD[result.weekday]} />
        <Fact label="农历" value={result.lunar_day} />
        <Fact label="节气月段" value={`${result.month_start_solar} ~ ${result.month_end_solar}`} />
        <Fact label="大运" value={result.dayun_ganzhi ?? '未起运'} />
        <Fact label="虚岁" value={result.year_age} />
        <Fact label="本日气数" value={`${result.day_score.value} · ${result.day_score.tier}`} />
      </div>

      <p className="text-xs leading-relaxed text-ink-muted">
        本日历注：宜 {yi.join('、')}
        {result.day_almanac.yi.length > yi.length ? ` 等 ${result.day_almanac.yi.length} 条` : ''}；忌{' '}
        {result.day_almanac.ji.length === 0 ? '—' : result.day_almanac.ji.join('、')}。历注取自外部历法库，
        是「日」粒度内容，不参与上面任何一分账，也不下挂到时辰。
      </p>

      <div className="gold-rule" />

      <button
        type="button"
        onClick={() => setOpen((next) => !next)}
        className="self-start label-caps text-ink-muted transition hover:text-ink"
      >
        {open ? '收起本日命中' : `展开本日命中（${result.day_fired.length} 条）`}
      </button>
      {open ? <TransitFiredList rows={result.day_fired} /> : null}
    </ResultCard>
  );
}
