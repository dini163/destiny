import { LiuriDayCell } from './LiuriDayCell';
import type { TransitDayCell } from '../../../types/baziLiuri';

/** 表头写死中文两字，7 列 = 周一到周日，与 `cell.weekday`（0 = 周一）同序。 */
const WEEKDAY_HEAD = ['一', '二', '三', '四', '五', '六', '日'];

/**
 * 全月逐日矩阵：7 列日历全息网格（PRD §6.1.2）。
 *
 * 前导空格数取 `days[0].weekday` —— 服务端给的那个数。前端排一次 `new Date()` 的
 * 星期就是第二条真值来源，时区一偏整列错位。段长实测 29—32 天，所以最多 6 行
 * （6 格前导 + 32 天 = 38 格）；不显示行号，行号无信息。窄屏横向滚动而不是折成
 * 4 列：折列会破坏星期对齐，而星期对齐是这张表唯一的坐标轴（spec §11.5）。
 */
export function LiuriMatrix({
  days,
  referenceDate,
  focusDate,
  onSelect,
}: {
  days: TransitDayCell[];
  referenceDate: string;
  focusDate: string | null;
  onSelect: (solarDate: string) => void;
}) {
  if (days.length === 0) {
    return null;
  }
  return (
    <div className="-mx-gutter overflow-x-auto px-gutter">
      <div className="min-w-[760px]">
        <div className="mb-2 grid grid-cols-7 gap-2">
          {WEEKDAY_HEAD.map((head) => (
            <span key={head} className="label-caps text-center text-ink-muted">
              {head}
            </span>
          ))}
        </div>
        <div className="grid grid-cols-7 gap-2">
          {Array.from({ length: days[0].weekday }, (_, index) => (
            <span key={`pad-${index}`} aria-hidden />
          ))}
          {days.map((cell) => (
            <LiuriDayCell
              key={cell.solar_date}
              cell={cell}
              isToday={cell.solar_date === referenceDate}
              isFocused={cell.solar_date === focusDate}
              onSelect={onSelect}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
