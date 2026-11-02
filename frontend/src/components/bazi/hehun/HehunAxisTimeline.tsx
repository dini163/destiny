import { Link } from 'react-router-dom';

import { tierClass } from '../liuri/tier';
import { Icon } from '../../ui/Icon';
import { SegmentedControl } from '../../ui/SegmentedControl';
import { GENDER_SHORT, annotateGenderTerms } from '../../../lib/gender';
import type { HehunAxis, HehunAxisRow, HehunAxisSegment, HehunSide } from '../../../types/baziHehun';

/** 轴长档位。`default` = 交回服务端按 §9.3 决定（两造的窗口不同，页面算不出缺省）。 */
const YEARS_OPTIONS: ReadonlyArray<{ value: string; label: string }> = [
  { value: 'default', label: '默认' },
  { value: '5', label: '5 年' },
  { value: '21', label: '21 年' },
  { value: '30', label: '30 年' },
];

const SYNC_CAPTION: Record<string, string> = {
  同频: 'text-wuxing-wood',
  半同步: 'text-ink-muted',
  背离: 'text-wuxing-fire',
};

interface HehunAxisTimelineProps {
  axis: HehunAxis;
  /** 在途：换轴长与换窗时留住上一份轴，但控件要显出"这一次正在算"（决策 11）。 */
  busy: boolean;
  /** `null` = 当前用的是服务端缺省轴。 */
  axisYears: number | null;
  /** 一造某一年的岁运链接；`lastRequest` 还没落定时为 `null`，那一处就不渲染链接。 */
  hrefFor: ((side: HehunSide, year: number) => string) | null;
  onYearsChange: (value: string) => void;
  /** -1 = 上一窗，1 = 下一窗（步长 = 当前窗口的年数，所以两窗恰好相接不重叠）。 */
  onShift: (direction: -1 | 1) => void;
}

/**
 * 同频演进轴：大运边界切段，段内逐年两造并置（spec §7.3、设计稿的时间轴卡片）。
 *
 * 一段一张卡、卡上逐行一年。分数与档位是岁运年表同一条装配路径给的（§10.5），所以每行
 * 带两个下钻链接：`hrefFor('male', 2029)` 落到岁运页并聚焦那一年 —— 轴是简表，明细在
 * 那一页，两造各自的下钻因此必须分列，不能合成一个"看这一年"。
 *
 * 段的 `label` 取自响应：那是两造各自第几步大运的并置事实，页面只补男女注记、不重排，
 * 否则就会把「乾（男）·第 4 运 戊午」写成别的什么。`dayun === null` 标「童限」，
 * 那是起运前的段，不是缺数据。
 *
 * 控件（轴长与上一窗/下一窗）在卡头：这一页只有它是轴的意志。窗口越界是**设计要给的**
 * 结果 —— 从缺省轴点两次「上一窗」即触出 `hehun_axis_out_of_range`，那五个 `context`
 * 键因此是可到达的（走查 Step 6 用得上）。
 */
export function HehunAxisTimeline({
  axis,
  busy,
  axisYears,
  hrefFor,
  onYearsChange,
  onShift,
}: HehunAxisTimelineProps) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <SegmentedControl
          ariaLabel="轴长"
          options={YEARS_OPTIONS}
          value={axisYears === null ? 'default' : String(axisYears)}
          onChange={onYearsChange}
        />
        <button
          type="button"
          disabled={busy}
          onClick={() => onShift(-1)}
          className="btn-ghost"
        >
          上一窗
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => onShift(1)}
          className="btn-ghost"
        >
          下一窗
        </button>
        <span className="label-caps text-ink-muted">
          {axis.start_year}—{axis.end_year} · {axis.rows.length}年
          {busy ? ' · 推演中' : ''}
        </span>
      </div>

      {axis.segments.map((segment) => (
        <SegmentBlock
          key={`${segment.start_year}-${segment.end_year}`}
          segment={segment}
          axis={axis}
          hrefFor={hrefFor}
        />
      ))}
    </div>
  );
}

function SegmentBlock({
  segment,
  axis,
  hrefFor,
}: {
  segment: HehunAxisSegment;
  axis: HehunAxis;
  hrefFor: ((side: HehunSide, year: number) => string) | null;
}) {
  const rows = axis.rows.filter(
    (row) => row.year >= segment.start_year && row.year <= segment.end_year,
  );
  return (
    <div className="flex flex-col gap-2 rounded-card border border-rim bg-[var(--field-bg)] p-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <span className="text-sm text-ink">{annotateGenderTerms(segment.label)}</span>
        <span className="numeric text-xs text-ink-muted">
          {segment.start_year}—{segment.end_year}
        </span>
      </div>
      {/* 与对冲矩阵同一条窄屏纪律：表自己撑最小宽、外层横向滚，于是 420 px 上滚的是
          这一段而不是整页 —— 整页一滚，卡头的轴长与上一窗/下一窗就跟着滚出视野，而它们
          恰恰是读者滚到某一年之后最想再点的东西。 */}
      <div className="overflow-x-auto">
        <table className="w-full min-w-[40rem] text-xs">
          <caption className="sr-only">
            {`${annotateGenderTerms(segment.label)} 内的逐年双造分数`}
          </caption>
          <thead>
            <tr className="text-left text-ink-muted">
              <th scope="col" className="font-normal">
                流年
              </th>
              <th scope="col" className="font-normal">
                {GENDER_SHORT.male}
              </th>
              <th scope="col" className="font-normal">
                {GENDER_SHORT.female}
              </th>
              <th scope="col" className="text-right font-normal">
                分差
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <AxisRowBlock key={row.year} row={row} hrefFor={hrefFor} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function AxisRowBlock({
  row,
  hrefFor,
}: {
  row: HehunAxisRow;
  hrefFor: ((side: HehunSide, year: number) => string) | null;
}) {
  return (
    <tr className="border-t border-rim align-top">
      <th scope="row" className="py-2 pr-2 text-left font-normal">
        <span className="numeric text-ink">{row.year}</span>
        <span className="numeric ml-1 text-ink-muted">{row.ganzhi}</span>
        <span className={`label-caps ml-2 ${SYNC_CAPTION[row.sync] ?? 'text-ink'}`}>{row.sync}</span>
      </th>
      <td className="py-2 pr-2">
        <SideCell side="male" row={row} hrefFor={hrefFor} />
      </td>
      <td className="py-2 pr-2">
        <SideCell side="female" row={row} hrefFor={hrefFor} />
      </td>
      <td className="numeric py-2 text-right text-ink">{row.gap.toFixed(1)}</td>
    </tr>
  );
}

function SideCell({
  side,
  row,
  hrefFor,
}: {
  side: HehunSide;
  row: HehunAxisRow;
  hrefFor: ((side: HehunSide, year: number) => string) | null;
}) {
  const cell = side === 'male' ? row.male : row.female;
  return (
    <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
      <span className="numeric text-ink">{cell.value.toFixed(1)}</span>
      <span className={`label-caps ${tierClass(cell.tier)}`}>{cell.tier}</span>
      <span className="numeric text-ink-muted">
        {cell.dayun ?? '童限'}
        {cell.dayun === null ? `（${cell.dayun_start_age} 岁起）` : ''}
      </span>
      {hrefFor ? (
        <Link to={hrefFor(side, row.year)} className="label-caps text-gold-soft hover:text-gold-bright">
          <Icon name="arrowRight" size={12} className="inline" />
          {side === 'male' ? `${GENDER_SHORT.male}岁运` : `${GENDER_SHORT.female}岁运`}
        </Link>
      ) : null}
    </div>
  );
}
