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
import { PlainSectionList } from '../components/ui/PlainSectionList';
import { SelectMenu } from '../components/ui/SelectMenu';
import { ObservatoryLoading } from '../components/ui/ObservatoryLoading';
import { ResultCard } from '../components/ui/ResultCard';
import { VerdictCard } from '../components/ui/VerdictCard';
import { aspectStyle } from '../lib/astro';
import { useWesternNatal } from '../hooks/useWesternNatal';
import { useProfileFill } from '../hooks/useProfileFill';
import { useI18n } from '../i18n/context';
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
 * (`useWesternNatal`) and rendered from real positions only. The trailing 白话详解 block
 * transposes those same computed facts into sentences curated in
 * `content/western_plain*.py` — self-authored, one row per fact,
 * nothing generated on request (Plan F spec §8). The mockup's invented transit
 * predictions are still omitted: this page shows the natal chart only.
 */
export function WesternNatalPage() {
  const { t } = useI18n();
  const [houseSystem, setHouseSystem] = useState('P');
  const [utcOffset, setUtcOffset] = useState('');
  const profile = useProfileFill();
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
        badge="瑞士星历"
        subtitle="精确计算本命四轴（ASC/MC/DES/IC）与十大主星落座落宫、主要相位容许度及元素形态分布。示例：2000-01-01 12:00 · 格林尼治 (51.4769, -0.0005) · UTC 0。"
        requireLatitude
        preset={profile.preset}
        profilePicker={profile.picker}
        onSaveProfile={(values) =>
          profile.openSave({
            birth_date: values.birth_date,
            birth_time: values.birth_time,
            calendar: values.calendar,
            city: values.city,
            latitude: values.latitude,
            longitude: values.longitude,
          })
        }
        submitLabel={western.isPending ? '重构星历中…' : '即刻重构星历'}
        pending={western.isPending}
        onSubmit={handleSubmit}
        footerSlot={
          <div className="flex flex-wrap items-center gap-x-5 gap-y-1 rounded-element border border-rim-soft bg-surface px-3 py-2 text-xs text-ink-muted">
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-gold" />
              {t('黄道基准：热带黄道 (Tropical)')}
            </span>
            <span>{t('时区留空时按出生经度推算 UTC 偏移（每 15° ≈ 1 小时）。')}</span>
            <span className="text-gold-soft">{t('ASC 极敏感：约每 4 分钟误差 ≈ 1° 上升点。')}</span>
          </div>
        }
      >
        <LabeledField label="分宫制 / HOUSE SYSTEM">
          <SelectMenu
            variant="field"
            value={houseSystem}
            onChange={(next) => setHouseSystem(next)}
            ariaLabel={t('分宫制')}
            options={HOUSE_SYSTEM_OPTIONS.map((opt) => ({ value: opt.value, label: t(opt.label) }))}
          />
        </LabeledField>
        <LabeledField label="时区 / UTC OFFSET" hint={<span className="text-ink-muted">{t('小时')}</span>}>
          <div className="flex items-center gap-2 rounded-element border border-rim bg-[var(--field-bg)] px-3 py-2 transition focus-within:border-rim-strong">
            <Icon name="clock" size={16} className="shrink-0 text-ink-muted" />
            <input
              type="number"
              min={-14}
              max={14}
              step={0.5}
              value={utcOffset}
              onChange={(event) => setUtcOffset(event.target.value)}
              placeholder={t('自动（按经度）')}
              className="numeric w-full bg-transparent text-sm text-ink outline-none placeholder:text-ink-muted"
              aria-label={t('UTC 时区偏移（小时）')}
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
        <ObservatoryLoading message={t('正在依瑞士星历重构本命天球…')} />
      ) : null}

      {western.data ? <WesternResults chart={western.data} /> : null}

      {profile.editor}
    </div>
  );
}

/** The full chart composition rendered once a real result is available. */
function WesternResults({ chart }: { chart: WesternChart }) {
  return (
    <>
      <ChartSummary chart={chart} />

      <VerdictCard verdict={chart.verdict} />

      <div className="grid grid-cols-1 items-start gap-6 xl:grid-cols-12">
        <div className="flex flex-col gap-6 xl:col-span-7">
          <ResultCard
            title="天球黄道命盘轮图"
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

          <ResultCard title="元素与形态分布" icon="seal" elevated>
            <ElementBalance elementBalance={chart.element_balance} modalityBalance={chart.modality_balance} />
          </ResultCard>

          <ResultCard title="十二宫头" icon="timeline" elevated>
            <HouseTable houses={chart.houses} />
          </ResultCard>
        </div>

        <div className="flex flex-col gap-6 xl:col-span-5">
          <ResultCard title="本命三巨头核心图腾" icon="sun" elevated>
            <BigThree planets={chart.planets} axes={chart.axes} />
          </ResultCard>

          <ResultCard title="十大主星与交点" icon="gauge" elevated>
            <PlanetTable planets={chart.planets} nodes={chart.nodes} />
          </ResultCard>

          <ResultCard title="关键相位网格" icon="sparkle" elevated>
            <AspectMatrix planets={chart.planets} aspects={chart.aspects} />
          </ResultCard>
        </div>
      </div>

      <ResultCard title="白话详解" icon="sparkle" elevated>
        <PlainSectionList sections={chart.plain} />
      </ResultCard>
    </>
  );
}

/** Headline strip: the trinity signs plus the chart's provenance metadata. */
function ChartSummary({ chart }: { chart: WesternChart }) {
  const { t } = useI18n();
  const houseLabel =
    HOUSE_SYSTEM_OPTIONS.find((option) => option.value === chart.house_system)?.label ?? chart.house_system;
  const offset = chart.utc_offset_hours;
  const offsetText = `UTC${offset >= 0 ? '+' : ''}${offset}`;
  const offsetSource = chart.utc_offset_source === 'explicit' ? t('显式输入') : t('经度推算');

  return (
    <div className="panel flex flex-col gap-4 p-5 sm:p-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <span className="label-caps">{t('本命星盘 · NATAL CHART')}</span>
          <span className="font-display text-2xl font-bold tracking-wide text-gold-bright text-glow-gold sm:text-3xl">
            {t('日{{sun}} · 月{{moon}} · 升{{asc}}', {
              sun: chart.sun_sign_zh,
              moon: chart.moon_sign_zh,
              asc: chart.ascendant_sign_zh,
            })}
          </span>
        </div>
      </div>
      <div className="gold-rule" />
      <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-ink-variant">
        <span>
          {t('当地时：')}<span className="numeric text-ink">{chart.local_datetime}</span>
        </span>
        <span>
          {t('世界时：')}<span className="numeric text-ink">{chart.utc_datetime}</span>
        </span>
        <span>
          {t('儒略日：')}<span className="numeric text-ink">{chart.julian_day}</span>
        </span>
        <span>
          {t('坐标：')}<span className="numeric text-ink">{chart.latitude.toFixed(3)}, {chart.longitude.toFixed(3)}</span>
        </span>
        <span className="text-gold-soft">
          {t('时区 {{offset}}（{{source}}）', { offset: offsetText, source: offsetSource })}
        </span>
        <span>
          {t('分宫制：')}<span className="text-ink">{t(houseLabel)}</span>
        </span>
      </div>
    </div>
  );
}

/** Colour legend for the aspect chords drawn inside the wheel. */
function AspectLegend() {
  const { t } = useI18n();
  return (
    <div className="mt-4 flex flex-wrap items-center justify-center gap-x-4 gap-y-2 border-t border-rim-soft pt-3">
      <span className="label-caps text-ink-muted">{t('相位图例 / ASPECTS')}</span>
      {ASPECT_LEGEND.map((item) => {
        const style = aspectStyle(item.type);
        return (
          <span key={item.type} className="flex items-center gap-1.5 text-xs text-ink-variant">
            <span className="h-0.5 w-4 rounded-full" style={{ backgroundColor: style.color }} />
            {t(style.label)} {item.angle}
          </span>
        );
      })}
    </div>
  );
}
