import { useState } from 'react';
import { Link } from 'react-router-dom';

import { Icon } from '../../ui/Icon';
import { ResultCard } from '../../ui/ResultCard';
import { TransitFiredList } from '../transit/TransitFiredList';
import type { BaziLiuriResult } from '../../../types/baziLiuri';

/**
 * 段切换的三个意图：-1 = 上一段（`month_start − 1 天`），0 = 今日，1 = 下一段
 * （`month_end + 1 天`）。本组件只发意图、不算日期 —— 日期加减留在页面上做，
 * 所以这一份意图类型由页面 import 过去，两边共用同一个枚举。
 */
export type ShiftDirection = -1 | 0 | 1;

const SHIFT_ACTIONS: ReadonlyArray<{ direction: ShiftDirection; label: string }> = [
  { direction: -1, label: '上一段' },
  { direction: 0, label: '今日' },
  { direction: 1, label: '下一段' },
];

/**
 * 段头：这一页唯一"此刻在哪"的一行 —— 哪个流年、哪段节气月、起止于哪两日、
 * 虚岁几何、走哪步大运，以及整段共用的那一个段基准。
 *
 * 一切字段都取自响应的段回显，本页不重排月界也不重算节气（决策 9）。段基准是
 * 年段 + 月段两段账本之和，与岁运页同段月卡逐字同源，所以这里只给分数与可展开的
 * 命中详单，不给第二个"综合评定"。造向与生辰不在这里出现：那是输入区与命局条的
 * 一份事实，摆两遍就有两份可能互相打架。
 */
export function LiuriSegmentHeader({
  result,
  busy,
  transitHref,
  onShift,
}: {
  result: BaziLiuriResult;
  busy: boolean;
  /** 回该年岁运的上钻链接，由页面拼好交进来（本页组件一律自己不碰生辰，决定 10）。 */
  transitHref?: string;
  onShift: (direction: ShiftDirection) => void;
}) {
  const [open, setOpen] = useState(false);
  return (
    <ResultCard
      eyebrow="DAILY SEGMENT"
      title={`${result.year_ganzhi}年 ${result.month_ganzhi}月`}
      icon="calendar"
      actions={
        <span className="flex items-center gap-2">
          {transitHref ? (
            <Link
              to={transitHref}
              className="label-caps rounded-element border border-rim px-2 py-1 text-gold-soft transition hover:border-rim-strong"
            >
              回岁运流年
            </Link>
          ) : null}
          {SHIFT_ACTIONS.map((action) => (
            <button
              key={action.direction}
              type="button"
              disabled={busy}
              onClick={() => onShift(action.direction)}
              className="label-caps rounded-element border border-rim px-3 py-1.5 transition hover:border-rim-strong hover:text-gold-soft disabled:cursor-not-allowed disabled:opacity-40"
            >
              {action.label}
            </button>
          ))}
        </span>
      }
    >
      <div className="flex flex-wrap items-baseline gap-x-6 gap-y-2 text-xs">
        <Fact label="月名" value={`${result.month_in_chinese}月`} />
        <Fact label="起讫" value={`${result.month_start_solar} ~ ${result.month_end_solar}`} />
        <Fact label="流年" value={`${result.year} 年 · 虚岁 ${result.year_age}`} />
        <Fact
          label="大运"
          value={
            result.dayun_ganzhi
              ? `第 ${result.dayun_index} 运 ${result.dayun_ganzhi}`
              : `第 ${result.dayun_index} 段（未起运）`
          }
        />
        <Fact
          label="段基准"
          value={`${result.month_score.value.toFixed(1)} ${result.month_score.tier}`}
        />
        <Fact label="逐日" value={`${result.days.length} 格`} />
      </div>

      <div className="flex flex-col gap-3">
        <button
          type="button"
          onClick={() => setOpen((prev) => !prev)}
          aria-expanded={open}
          className="label-caps flex items-center gap-1 self-start text-ink-muted hover:text-gold-soft"
        >
          <Icon name="chevronDown" size={12} className={open ? 'rotate-180' : undefined} />
          {open ? '收起本段命中' : `展开本段命中 ${result.month_fired.length} 行`}
        </button>
        {open ? <TransitFiredList rows={result.month_fired} /> : null}
      </div>
    </ResultCard>
  );
}

/** One caption/value pair in the segment line. */
function Fact({ label, value }: { label: string; value: string }) {
  return (
    <span className="flex items-baseline gap-1.5">
      <span className="label-caps text-ink-muted">{label}</span>
      <span className="numeric text-ink">{value}</span>
    </span>
  );
}
