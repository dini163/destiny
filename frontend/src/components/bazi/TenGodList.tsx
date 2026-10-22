import type { TenGodReading } from '../../types/bazi';
import { pillarSlotLabel } from '../../lib/pillars';

/** 十神清点：命局出现的每个十神一条，落点与释义都来自后端。 */
export function TenGodList({ readings }: { readings: TenGodReading[] }) {
  if (readings.length === 0) return null;
  return (
    <ul className="flex flex-wrap gap-2">
      {readings.map((reading) => (
        <li
          key={reading.ten_god}
          className="flex items-center gap-2 rounded-element border border-rim bg-[#0e111a] px-2.5 py-1.5 text-xs"
          title={`${reading.meaning}｜${reading.source}`}
        >
          <span className="text-ink">{reading.ten_god}</span>
          <span className="numeric text-gold-soft">{reading.count}</span>
          <span className="text-ink-muted">{reading.positions.map(pillarSlotLabel).join('、')}</span>
        </li>
      ))}
    </ul>
  );
}
