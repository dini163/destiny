import type { ReactNode } from 'react';

import { useApiHealth } from '../../hooks/useApiHealth';
import { useNow } from '../../hooks/useNow';
import { useTrueSolarTime } from '../../hooks/useTrueSolarTime';
import { beijingTime } from '../../lib/beijingTime';
import { Icon } from '../ui/Icon';

/** The standard meridian for Beijing Time (UTC+8), used for the live TST broadcast. */
const REFERENCE_LONGITUDE = 120;

/** Format a signed equation-of-time offset in minutes as e.g. `+3.42 分钟`. */
function formatOffset(minutes: number): string {
  const sign = minutes >= 0 ? '+' : '−';
  return `${sign}${Math.abs(minutes).toFixed(2)} 分钟`;
}

/**
 * The live astronomical time broadcast (今日天文授时).
 *
 * Everything shown is real: a ticking Beijing clock from the client's own time,
 * the True Solar Time and equation-of-time E(t) computed by the backend's
 * pyswisseph engine for the current minute at the 120°E standard meridian, and the
 * computation API's live health. The mockup's 岁次干支 / 月相 / 行星落座 / 黄历宜忌
 * pillars are deliberately omitted — the engine does not compute them yet, and the
 * no-mock rule forbids inventing them; the footnote says so plainly.
 */
export function DailyTimePanel() {
  const now = useNow(1000);
  const { date, minute, clock } = beijingTime(now);
  const trueSolarTime = useTrueSolarTime({
    date,
    time: minute,
    longitude: REFERENCE_LONGITUDE,
  });
  const health = useApiHealth();

  const healthy = health.data?.status === 'ok';

  return (
    <div className="panel-raised flex h-full flex-col gap-5 p-6">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2 shrink-0">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-gold opacity-70" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-gold-bright" />
          </span>
          <span className="label-caps text-gold">今日天文授时 · 真太阳时校准</span>
        </div>
        <Icon name="sun" size={20} className="shrink-0 text-gold" />
      </div>

      <div className="flex flex-col gap-1">
        <span className="numeric text-4xl font-semibold text-ink tabular-nums">{clock}</span>
        <span className="label-caps">北京时间 · {date} · 东经 {REFERENCE_LONGITUDE}° 标准时</span>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <Metric
          label="真太阳时 TST"
          value={trueSolarTime.data ? shortTime(trueSolarTime.data.true_solar_time) : '…'}
          sub="视太阳时（含均时差）"
          accent="text-gold-bright"
        />
        <Metric
          label="均时差 E(t)"
          value={trueSolarTime.data ? formatOffset(trueSolarTime.data.offset_minutes) : '…'}
          sub="轨道偏心率 + 赤纬修正"
        />
        <Metric
          label="标准时基准"
          value={trueSolarTime.data ? shortTime(trueSolarTime.data.standard_time) : '…'}
          sub={`经度 ${REFERENCE_LONGITUDE}°E`}
        />
        <Metric
          label="计算引擎"
          value={
            <span className="flex items-center gap-2">
              <span
                className={`h-2 w-2 rounded-full ${
                  health.isLoading ? 'bg-ink-muted' : healthy ? 'bg-wuxing-wood' : 'bg-wuxing-fire'
                }`}
              />
              {health.isLoading ? '探测中' : healthy ? '在线' : '不可达'}
            </span>
          }
          sub={health.data?.service ?? '后端计算 API'}
        />
      </div>

      <p className="mt-auto flex items-start gap-2 rounded-element border border-rim-soft bg-surface px-3 py-2 text-[11px] leading-relaxed text-ink-muted">
        <Icon name="sparkle" size={14} className="mt-0.5 shrink-0 text-gold" />
        <span>
          真太阳时与均时差由后端 pyswisseph 依当前时刻实时演算，每分钟自动校准。月相、行星落座与黄历宜忌等完整天象播报将随后续星历接口上线——当前绝不虚构。
        </span>
      </p>
    </div>
  );
}

/** Extract the `HH:MM` portion of a backend `YYYY-MM-DD HH:MM` timestamp. */
function shortTime(timestamp: string): string {
  const time = timestamp.split(' ')[1];
  return time ? time.slice(0, 5) : timestamp;
}

/** One labelled readout in the broadcast grid. */
function Metric({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: ReactNode;
  sub?: string;
  accent?: string;
}) {
  return (
    <div className="flex flex-col gap-1 rounded-element border border-rim-soft bg-surface p-3">
      <span className="label-caps">{label}</span>
      <span className={`numeric font-display text-base ${accent ?? 'text-ink'}`}>{value}</span>
      {sub ? <span className="text-[11px] leading-snug text-ink-muted">{sub}</span> : null}
    </div>
  );
}
