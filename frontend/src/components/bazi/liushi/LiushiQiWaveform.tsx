import { HOUR_BRANCHES, type TransitHourCell } from '../../../types/baziLiushi';
import { tierClass } from '../liuri/tier';

const WIDTH = 24;
const HEIGHT = 120;

/** 分值 → 纵坐标：0 分在底、100 分在顶，线性，不做任何缩放或平滑。 */
function yOf(value: number): number {
  return HEIGHT - (value / 100) * HEIGHT;
}

/**
 * 真气波形：十二格的阶梯折线。
 *
 * **阶梯不插值。** 每格一段水平线、格与格之间一道竖线接成台阶 —— 一请求只有 12 个
 * 采样点，把两点之间画成斜的等于宣称"这两个时辰之间有测过"（spec §5.5）。
 *
 * 基线是 `day_score.value`（十二格共同的那半份账），它画在 SVG 之外：一条绝对定位的
 * 虚线 `border-t`，因为 `preserveAspectRatio="none"` 之下任何 SVG 内的线都会跟着拉伸。
 * 同理，峰值那颗点与十二个支名都用 HTML 摆，SVG 里只留折线本身。
 *
 * 纵轴上没有第二把尺：`qi_strength` 只是标签，它不进这张图（决策 3）。
 */
export function LiushiQiWaveform({
  hours,
  baseline,
  peakIndex,
}: {
  hours: TransitHourCell[];
  baseline: number;
  peakIndex: number;
}) {
  const step = WIDTH / 12;
  const segments = hours.map(
    (cell, index) => `M${index * step},${yOf(cell.value)} L${(index + 1) * step},${yOf(cell.value)}`,
  );
  const links = hours.slice(1).map((cell, offset) => {
    const index = offset + 1;
    return `M${index * step},${yOf(hours[offset].value)} L${index * step},${yOf(cell.value)}`;
  });
  const peak = hours[peakIndex];
  return (
    <div className="flex flex-col gap-2">
      <div className="relative h-[120px] w-full rounded-element border border-rim bg-[#0e111a]">
        <div
          className="pointer-events-none absolute inset-x-0 border-t border-dashed border-gold/40"
          style={{ bottom: `${baseline}%` }}
        />
        <svg
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          preserveAspectRatio="none"
          className="absolute inset-0 h-full w-full"
          aria-hidden
        >
          {[...segments, ...links].map((path) => (
            <path
              key={path}
              d={path}
              fill="none"
              stroke="#d4af37"
              strokeWidth={1.5}
              strokeLinecap="round"
              vectorEffect="non-scaling-stroke"
            />
          ))}
        </svg>
        <span
          className="absolute h-2 w-2 -translate-x-1/2 translate-y-1/2 rounded-full bg-gold"
          style={{
            left: `${((peakIndex * step + step / 2) / WIDTH) * 100}%`,
            bottom: `${peak.value}%`,
          }}
          title={`${peak.ganzhi}·${Math.round(peak.value)}`}
        />
      </div>
      <div className="grid grid-cols-12 gap-1">
        {hours.map((cell) => (
          <span
            key={cell.zhi}
            className={`text-center label-caps ${cell.index === peakIndex ? 'text-gold' : tierClass(cell.tier)}`}
          >
            {HOUR_BRANCHES[cell.index]}
          </span>
        ))}
      </div>
      <span className="text-[11px] text-ink-muted">
        虚线 = 本日气数 {Math.round(baseline)}；纵轴只有吉凶度一把尺，阶梯为实测十二点，未插值。
      </span>
    </div>
  );
}
