import type { TrueSolarTimeParams } from '../../api/meta';
import { useTrueSolarTime } from '../../hooks/useTrueSolarTime';
import { Icon } from './Icon';

interface TrueSolarTimeBadgeProps {
  /** ISO date (yyyy-mm-dd), or null when incomplete. */
  date: string | null;
  /** HH:MM local standard time, or null when incomplete. */
  time: string | null;
  /** Longitude in degrees east, or null when unresolved. */
  longitude: number | null;
}

/** Format a signed minute offset as e.g. `−77m 50s`. */
function formatOffset(minutes: number): string {
  const sign = minutes < 0 ? '−' : '+';
  const total = Math.abs(minutes);
  const mins = Math.floor(total);
  const secs = Math.round((total - mins) * 60);
  return `${sign}${mins}m ${secs.toString().padStart(2, '0')}s`;
}

/**
 * True Solar Time calibration banner (PRD §7).
 *
 * With a complete date/time/longitude it previews the standard-time → true-solar-time
 * correction from `/meta/true-solar-time`, including the longitude + equation-of-time
 * offset. Until then it shows a neutral hint so the console stays uncluttered.
 */
export function TrueSolarTimeBadge({ date, time, longitude }: TrueSolarTimeBadgeProps) {
  const params: TrueSolarTimeParams | null =
    date && time && longitude != null ? { date, time, longitude } : null;
  const { data, isFetching, isError } = useTrueSolarTime(params);

  if (params === null) {
    return (
      <p className="flex items-center gap-2 rounded-element border border-rim-soft bg-[#0e111a] px-3 py-2 text-sm text-ink-muted">
        <Icon name="sun" size={16} className="shrink-0 text-gold-muted" />
        填写出生日期、时间并定位后，此处按经度与均时差显示真太阳时校准。
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-3 rounded-element border border-rim bg-[#0e111a] px-4 py-3 md:flex-row md:items-center md:justify-between">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gold/10 text-gold">
          <Icon name="sun" size={18} />
        </span>
        <div className="flex flex-col">
          <span className="label-caps text-gold">真太阳时校准定盘 · TRUE SOLAR TIME</span>
          {data ? (
            <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm">
              <span className="text-ink-muted">标准时</span>
              <span className="numeric text-ink">{data.standard_time}</span>
              <Icon name="arrowRight" size={16} className="text-ink-muted" />
              <span className="text-gold">真太阳时</span>
              <span className="numeric font-semibold text-gold-bright">{data.true_solar_time}</span>
            </div>
          ) : (
            <span className="mt-1 text-sm text-ink-muted">
              {isFetching ? '正在按经度与均时差推算…' : isError ? '真太阳时服务暂不可用。' : '等待计算…'}
            </span>
          )}
        </div>
      </div>
      {data ? (
        <span className="numeric shrink-0 self-start rounded-element border border-rim bg-surface px-2.5 py-1 text-xs text-gold-soft md:self-auto">
          经度 {data.longitude.toFixed(2)}°E · 校正 {formatOffset(data.offset_minutes)}
        </span>
      ) : null}
    </div>
  );
}
