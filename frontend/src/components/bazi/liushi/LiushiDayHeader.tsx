import { useState } from 'react';
import { Link } from 'react-router-dom';

import { useI18n } from '../../../i18n/context';
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
  const { t } = useI18n();
  if (value === null || value === undefined || value === '') return null;
  return (
    <span className="flex items-baseline gap-1 text-xs">
      <span className="label-caps text-ink-muted">{t(label)}</span>
      <span className="numeric text-ink">{value}</span>
    </span>
  );
}

/**
 * 页头：这一天的年月日段回显 + 上钻一条 + 换日三键 + 日头那三段账与历注。
 *
 * 它把"十二格是从哪一天摊出来的"说清楚：`{year_ganzhi}年 {month_ganzhi}月 · {day_ganzhi}日`
 * 一整串都取自响应，前端不重算月界（决策 9）。宜忌走 `yiPreview`，与流日矩阵格同一口径
 * —— 两处两种截法会让读者以为它们在说不同的事。
 *
 * `liuriHref` 由页面拼好交进来（生辰只在页面上有，与聚焦卡那条下钻链接同一分工）：
 * 这三页只有向下的一条线，没有回头路可走的话，读者只能靠浏览器后退。
 *
 * 「本日命中」默认折起：十二格与波形才是这一页的主角，日头那十行摊开会把它们推到下屏。
 */
export function LiushiDayHeader({
  result,
  busy,
  liuriHref,
  onShift,
}: {
  result: BaziLiushiResult;
  busy: boolean;
  liuriHref?: string;
  onShift: (direction: ShiftDirection) => void;
}) {
  const [open, setOpen] = useState(false);
  const { t } = useI18n();
  const yi = yiPreview(result.day_almanac.yi);
  return (
    <ResultCard
      title={t('{{year}}年 {{month}}月 · {{day}}日', {
        year: result.year_ganzhi,
        month: result.month_ganzhi,
        day: result.day_ganzhi,
      })}
      icon="sun"
      actions={
        <span className="flex items-center gap-2">
          {liuriHref ? (
            <Link
              to={liuriHref}
              className="label-caps rounded-element border border-rim px-2 py-1 text-gold-soft transition hover:border-rim-strong"
            >
              {t('回流日矩阵')}
            </Link>
          ) : null}
          {DAY_SHIFT_ACTIONS.map((action) => (
            <button
              key={action.direction}
              type="button"
              onClick={() => onShift(action.direction)}
              disabled={busy}
              className="rounded-element border border-rim px-2.5 py-1 text-xs text-ink-variant transition hover:border-rim-strong disabled:opacity-50"
            >
              {t(action.label)}
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
        <Fact label="大运" value={result.dayun_ganzhi ?? t('未起运')} />
        <Fact label="虚岁" value={result.year_age} />
        <Fact label="本日气数" value={t('{{v}} · {{tier}}', { v: result.day_score.value, tier: t(result.day_score.tier) })} />
      </div>

      <p className="text-xs leading-relaxed text-ink-muted">
        {t('本日历注：宜')} {yi.map((entry) => t(entry)).join(t('、'))}
        {result.day_almanac.yi.length > yi.length ? ` ${t('等 {{n}} 条', { n: result.day_almanac.yi.length })}` : ''}；{t('忌')}
        {' '}
        {result.day_almanac.ji.length === 0 ? '—' : result.day_almanac.ji.map((entry) => t(entry)).join(t('、'))}。{t('历注取自外部历法库，是「日」粒度内容，不参与上面任何一分账，也不下挂到时辰。')}
      </p>

      <div className="gold-rule" />

      <button
        type="button"
        onClick={() => setOpen((next) => !next)}
        className="self-start label-caps text-ink-muted transition hover:text-ink"
      >
        {open ? t('收起本日命中') : t('展开本日命中（{{n}} 条）', { n: result.day_fired.length })}
      </button>
      {open ? <TransitFiredList rows={result.day_fired} /> : null}
    </ResultCard>
  );
}
