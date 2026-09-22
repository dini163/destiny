import { LiushiHourCell } from './LiushiHourCell';
import type { TransitHourCell } from '../../../types/baziLiushi';

/**
 * 梯次谱：十二格按地支序并排的一行。
 *
 * 12 列固定，不做响应式折行 —— 折了就不是"一日的走势"，而是一列互不相干的卡片。
 * 窄屏靠 `overflow-x-auto` + 负 `mx-gutter` 出血到边，两端各留满 `px-gutter`，
 * 与流日矩阵同一件做法（切片 3 实测：11 列时整卡在窄屏被挤到 96px 以下，字都叠了）。
 */
export function LiushiHourLadder({
  hours,
  peakIndex,
  focusZhi,
  onSelect,
}: {
  hours: TransitHourCell[];
  peakIndex: number;
  focusZhi: string | null;
  onSelect: (zhi: string) => void;
}) {
  return (
    <div className="-mx-gutter overflow-x-auto px-gutter pb-1">
      <div className="grid min-w-[900px] grid-cols-12 gap-2">
        {hours.map((cell) => (
          <LiushiHourCell
            key={cell.zhi}
            cell={cell}
            isPeak={cell.index === peakIndex}
            isFocused={cell.zhi === focusZhi}
            onSelect={onSelect}
          />
        ))}
      </div>
    </div>
  );
}
