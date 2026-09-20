import { useState } from 'react';

import { AspectMatrix } from '../components/western/AspectMatrix';
import { AstroWheel } from '../components/western/AstroWheel';
import { BigThree } from '../components/western/BigThree';
import { ElementBalance } from '../components/western/ElementBalance';
import { HouseTable } from '../components/western/HouseTable';
import { PlanetTable } from '../components/western/PlanetTable';
import { Icon } from '../components/ui/Icon';
import { InputBar } from '../components/ui/InputBar';
import type { BirthInputValues } from '../components/ui/InputBar';
import { LabeledField } from '../components/ui/LabeledField';
import { ResultCard } from '../components/ui/ResultCard';
import { aspectStyle } from '../lib/astro';
import { useWesternNatal } from '../hooks/useWesternNatal';
import type { WesternChart, WesternNatalRequest } from '../types/western';

/** House systems the backend engine accepts (Swiss Ephemeris codes). */
const HOUSE_SYSTEM_OPTIONS: ReadonlyArray<{ value: string; label: string }> = [
  { value: 'P', label: '普拉西度 Placidus' },
  { value: 'K', label: '科赫 Koch' },
  { value: 'R', label: '雷吉奥蒙塔努斯 Regiomontanus' },
  { value: 'E', label: '等宫制 Equal' },
  { value: 'W', label: '全星座 Whole Sign' },
];

/** The five major aspects, for the wheel's colour legend. */
const ASPECT_LEGEND: ReadonlyArray<{ type: string; angle: string }> = [
  { type: 'conjunction', angle: '0°' },
  { type: 'sextile', angle: '60°' },
  { type: 'square', angle: '90°' },
  { type: 'trine', angle: '120°' },
  { type: 'opposition', angle: '180°' },
];

/**
 * Western natal-chart page (本命星盘).
 *
 * The input console collects Gregorian birth data plus a location (latitude is
 * required — houses and the ascendant depend on it) and an optional house system
 * and UTC offset. On submit the chart is computed by the pyswisseph engine
 * (`useWesternNatal`) and rendered from real positions only: the astro-wheel, the
 * ephemeris, aspects, houses and element/modality balance. Transit predictions and
 * archetype readings from the mockup are omitted (PRD no-mock rule).
 */
export function WesternNatalPage() {
  const [houseSystem, setHouseSystem] = useState('P');
  const [utcOffset, setUtcOffset] = useState('');
  const western = useWesternNatal();

  function handleSubmit(values: BirthInputValues): void {
    const request: WesternNatalRequest = {
      birth_date: values.birth_date,
      birth_time: values.birth_time,
      city: values.city,
      latitude: values.latitude,
      longitude: values.longitude,
      house_system: houseSystem,
      utc_offset_hours: utcOffset === '' ? undefined : Number(utcOffset),
    };
    western.mutate(request);
  }

  return (
    <div className="mx-auto flex w-full max-w-[1536px] flex-col gap-6 px-gutter py-8">
      <InputBar
        title="本命星盘与时空推运"
        badge="pyswisseph 瑞士星历"
        subtitle="精确计算本命四轴（ASC/MC/DES/IC）与十大主星落座落宫、主要相位容许度及元素形态分布。示例：2000-01-01 12:00 · 格林尼治 (51.4769, -0.0005) · UTC 0。"
        requireLatitude
        submitLabel={western.isPending ? '重构星历中…' : '即刻重构星历'}
        pending={western.isPending}
        onSubmit={handleSubmit}
        footerSlot={
          <div className="flex flex-wrap items-center gap-x-5 gap-y-1 rounded-element border border-rim-soft bg-surface px-3 py-2 text-xs text-ink-muted">
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-gold" />
              黄道基准：热带黄道 (Tropical)
            </span>
            <span>时区留空时按出生经度推算 UTC 偏移（每 15° ≈ 1 小时）。</span>
            <span className="text-gold-soft">ASC 极敏感：约每 4 分钟误差 ≈ 1° 上升点。</span>
          </div>
        }
      >
        <LabeledField label="分宫制 / HOUSE SYSTEM">
          <select
            value={houseSystem}
            onChange={(event) => setHouseSystem(event.target.value)}
            className="w-full rounded-element border border-rim bg-[#0e111a] px-3 py-2 text-sm text-ink outline-none transition focus:border-rim-strong"
            aria-label="分宫制"
          >
            {HOUSE_SYSTEM_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </LabeledField>
        <LabeledField label="时区 / UTC OFFSET" hint={<span className="text-ink-muted">小时</span>}>
          <div className="flex items-center gap-2 rounded-element border border-rim bg-[#0e111a] px-3 py-2 transition focus-within:border-rim-strong">
            <Icon name="clock" size={16} className="shrink-0 text-ink-muted" />
            <input
              type="number"
              min={-14}
              max={14}
              step={0.5}
              value={utcOffset}
              onChange={(event) => setUtcOffset(event.target.value)}
              placeholder="自动（按经度）"
              className="numeric w-full bg-transparent text-sm text-ink outline-none placeholder:text-ink-muted"
              aria-label="UTC 时区偏移（小时）"
            />
          </div>
        </LabeledField>
      </InputBar>

      {western.error ? (
        <div className="flex items-start gap-2 rounded-element border border-wuxing-fire/40 bg-wuxing-fire/10 px-4 py-3 text-sm text-ink">
          <Icon name="alert" size={18} className="mt-0.5 shrink-0 text-wuxing-fire" />
          <span>{western.error.message}</span>
        </div>
      ) : null}

      {western.isPending && !western.data ? (
        <p className="label-caps text-ink-muted">正在依瑞士星历重构本命天球…</p>
      ) : null}

      {western.data ? <WesternResults chart={western.data} /> : null}
    </div>
  );
}

/** The full chart composition rendered once a real result is available. */
function WesternResults({ chart }: { chart: WesternChart }) {
  return (
    <>
      <ChartSummary chart={chart} />

      <div className="grid grid-cols-1 items-start gap-6 xl:grid-cols-12">
        <div className="flex flex-col gap-6 xl:col-span-7">
          <ResultCard
            title="天球黄道命盘轮图"
            eyebrow="NATAL ASTRO WHEEL"
            icon="compass"
            actions={<span className="label-caps text-ink-muted">{chart.house_system} · {chart.zodiac}</span>}
            elevated
          >
            <div className="relative mx-auto aspect-square w-full max-w-[620px]">
              <AstroWheel
                planets={chart.planets}
                axes={chart.axes}
                houses={chart.houses}
                aspects={chart.aspects}
              />
            </div>
            <AspectLegend />
          </ResultCard>

          <ResultCard title="元素与形态分布" eyebrow="BALANCE" icon="seal" elevated>
            <ElementBalance elementBalance={chart.element_balance} modalityBalance={chart.modality_balance} />
          </ResultCard>

          <ResultCard title="十二宫头" eyebrow="HOUSE CUSPS" icon="timeline" elevated>
            <HouseTable houses={chart.houses} />
          </ResultCard>
        </div>

        <div className="flex flex-col gap-6 xl:col-span-5">
          <ResultCard title="本命三巨头核心图腾" eyebrow="NATAL TRINITY" icon="sun" elevated>
            <BigThree planets={chart.planets} axes={chart.axes} />
          </ResultCard>

          <ResultCard title="十大主星与交点" eyebrow="EPHEMERIS TABLE" icon="gauge" elevated>
            <PlanetTable planets={chart.planets} nodes={chart.nodes} />
          </ResultCard>

          <ResultCard title="关键相位网格" eyebrow="MAJOR ASPECTS" icon="sparkle" elevated>
            <AspectMatrix planets={chart.planets} aspects={chart.aspects} />
          </ResultCard>
        </div>
      </div>

      <Provenance chart={chart} />
    </>
  );
}

/** Headline strip: the trinity signs plus the chart's provenance metadata. */
function ChartSummary({ chart }: { chart: WesternChart }) {
  const houseLabel =
    HOUSE_SYSTEM_OPTIONS.find((option) => option.value === chart.house_system)?.label ?? chart.house_system;
  const offset = chart.utc_offset_hours;
  const offsetText = `UTC${offset >= 0 ? '+' : ''}${offset}`;
  const offsetSource = chart.utc_offset_source === 'explicit' ? '显式输入' : '经度推算';

  return (
    <div className="panel flex flex-col gap-4 p-5 sm:p-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <span className="label-caps">本命星盘 · NATAL CHART</span>
          <span className="font-display text-2xl font-bold tracking-wide text-gold-bright text-glow-gold sm:text-3xl">
            日{chart.sun_sign_zh} · 月{chart.moon_sign_zh} · 升{chart.ascendant_sign_zh}
          </span>
        </div>
      </div>
      <div className="gold-rule" />
      <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-ink-variant">
        <span>
          当地时：<span className="numeric text-ink">{chart.local_datetime}</span>
        </span>
        <span>
          世界时：<span className="numeric text-ink">{chart.utc_datetime}</span>
        </span>
        <span>
          儒略日：<span className="numeric text-ink">{chart.julian_day}</span>
        </span>
        <span>
          坐标：<span className="numeric text-ink">{chart.latitude.toFixed(3)}, {chart.longitude.toFixed(3)}</span>
        </span>
        <span className="text-gold-soft">
          时区 {offsetText}（{offsetSource}）
        </span>
        <span>
          分宫制：<span className="text-ink">{houseLabel}</span>
        </span>
      </div>
    </div>
  );
}

/** Colour legend for the aspect chords drawn inside the wheel. */
function AspectLegend() {
  return (
    <div className="mt-4 flex flex-wrap items-center justify-center gap-x-4 gap-y-2 border-t border-rim-soft pt-3">
      <span className="label-caps text-ink-muted">相位图例 / ASPECTS</span>
      {ASPECT_LEGEND.map((item) => {
        const style = aspectStyle(item.type);
        return (
          <span key={item.type} className="flex items-center gap-1.5 text-xs text-ink-variant">
            <span className="h-0.5 w-4 rounded-full" style={{ backgroundColor: style.color }} />
            {style.label} {item.angle}
          </span>
        );
      })}
    </div>
  );
}

/** Methodology + provenance note anchored to the real ephemeris engine. */
function Provenance({ chart }: { chart: WesternChart }) {
  const offsetSource = chart.utc_offset_source === 'explicit' ? '显式时区' : '按经度推算的理论时区';
  return (
    <div className="panel flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-start gap-3">
        <Icon name="seal" size={22} className="mt-0.5 shrink-0 text-gold" />
        <div className="flex flex-col gap-1">
          <span className="font-display text-base text-ink">天文算法与星历溯源</span>
          <p className="max-w-3xl text-sm leading-relaxed text-ink-muted">
            行星黄经、四轴与宫头均由 <span className="text-gold-soft">{chart.engine}</span>{' '}
            瑞士星历实时计算（{chart.zodiac === 'tropical' ? '热带黄道' : chart.zodiac}），分宫制为{' '}
            <span className="text-gold-soft">{chart.house_system}</span>，世界时以{offsetSource}
            换算。相位按经典容许度检测，未作主观吉凶演绎，星盘仅供文化参考。
          </p>
        </div>
      </div>
      <span className="label-caps shrink-0 text-ink-muted">ENGINE · {chart.engine}</span>
    </div>
  );
}
