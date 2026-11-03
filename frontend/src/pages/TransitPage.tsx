import { useState } from 'react';

import { CrossAspectList } from '../components/transit/CrossAspectList';
import { MovingPointTable } from '../components/transit/MovingPointTable';
import { TransitBiWheel } from '../components/transit/TransitBiWheel';
import { Icon } from '../components/ui/Icon';
import { InputBar } from '../components/ui/InputBar';
import type { BirthInputValues } from '../components/ui/InputBar';
import { ChineseDateField } from '../components/ui/DateTimeField';
import { SelectMenu } from '../components/ui/SelectMenu';
import { LabeledField } from '../components/ui/LabeledField';
import { ResultCard } from '../components/ui/ResultCard';
import { PlainSectionList } from '../components/ui/PlainSectionList';
import { VerdictCard } from '../components/ui/VerdictCard';
import { SegmentedControl } from '../components/ui/SegmentedControl';
import { useTransit } from '../hooks/useTransit';
import { useProfileFill } from '../hooks/useProfileFill';
import { useI18n } from '../i18n/context';
import { aspectStyle } from '../lib/astro';
import { TRANSIT_MODES, formatAgeYears, modeConfig, modeData } from '../lib/transit';
import type { TransitMode } from '../lib/transit';
import type { ProgressionBlock, SolarArcBlock, TransitChart, TransitRequest } from '../types/transit';

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

/** Today's date as ISO `yyyy-mm-dd`, the default projection target. */
function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

/**
 * Transit & progression page (行运次限推运).
 *
 * The console collects the same Gregorian birth data plus location as the natal
 * chart, and adds a target date. On submit the pyswisseph engine layers three
 * predictive techniques over the embedded real natal chart; a segmented control
 * switches the bi-wheel's outer ring (and its ephemeris/aspect tables) between
 * transits, secondary progressions and solar arc. Every position and aspect is
 * computed — nothing is invented at runtime (PRD no-mock rule).
 */
export function TransitPage() {
  const { t } = useI18n();
  const [houseSystem, setHouseSystem] = useState('P');
  const [utcOffset, setUtcOffset] = useState('');
  const [targetDate, setTargetDate] = useState<string>(todayISO);
  const profile = useProfileFill();
  const transit = useTransit();

  function handleSubmit(values: BirthInputValues): void {
    const request: TransitRequest = {
      birth_date: values.birth_date,
      birth_time: values.birth_time,
      city: values.city,
      latitude: values.latitude,
      longitude: values.longitude,
      house_system: houseSystem,
      utc_offset_hours: utcOffset === '' ? undefined : Number(utcOffset),
      target_date: targetDate || todayISO(),
    };
    transit.mutate(request);
  }

  return (
    <div className="mx-auto flex w-full max-w-[1536px] flex-col gap-6 px-gutter py-8">
      <InputBar
        title="行运次限推运"
        badge="瑞士星历"
        subtitle="在本命盘之上叠加三层动态时间轴：外行星过境（行运）、一日当一年（次限推运）与太阳弧推进。指定目标日期，即看移动层诸星落入本命何宫、对本命所成之相位。示例：2000-01-01 12:00 · 格林尼治 (51.4769, -0.0005) · UTC 0 · 目标日任选。"
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
        submitLabel={transit.isPending ? '推演行运中…' : '即刻推演行运'}
        pending={transit.isPending}
        onSubmit={handleSubmit}
        footerSlot={
          <div className="flex flex-wrap items-center gap-x-5 gap-y-1 rounded-element border border-rim-soft bg-surface px-3 py-2 text-xs text-ink-muted">
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-gold" />
              {t('行运取目标日正午世界时（12:00 UT）')}
            </span>
            <span>{t('次限依「一日当一年」推进本命；太阳弧约每年推进 1°。')}</span>
            <span className="text-gold-soft">{t('目标日期不得早于出生日期。')}</span>
          </div>
        }
      >
        <LabeledField label="目标日期 / TARGET DATE">
          <ChineseDateField
            value={targetDate}
            onChange={setTargetDate}
            minYear={1900}
            maxYear={new Date().getFullYear() + 30}
            ariaLabel={t('目标')}
          />
        </LabeledField>
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

      {transit.error ? (
        <div className="flex items-start gap-2 rounded-element border border-wuxing-fire/40 bg-wuxing-fire/10 px-4 py-3 text-sm text-ink">
          <Icon name="alert" size={18} className="mt-0.5 shrink-0 text-wuxing-fire" />
          <span>{transit.error.message}</span>
        </div>
      ) : null}

      {transit.isPending && !transit.data ? (
        <p className="label-caps text-ink-muted">{t('正在依瑞士星历叠加行运、次限与太阳弧…')}</p>
      ) : null}

      {transit.data ? <TransitResults chart={transit.data} /> : null}

      {profile.editor}
    </div>
  );
}

/** The full overlay composition, with the technique switch driving every panel. */
function TransitResults({ chart }: { chart: TransitChart }) {
  const { t } = useI18n();
  const [mode, setMode] = useState<TransitMode>('transit');
  const { positions, aspects } = modeData(chart, mode);
  const config = modeConfig(mode);

  return (
    <>
      <SummaryStrip chart={chart} />

      <VerdictCard verdict={chart.verdict} />

      <div className="panel-raised flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-col gap-1.5">
          <span className="label-caps">{t('推运层 / TECHNIQUE')}</span>
          <SegmentedControl<TransitMode>
            ariaLabel="推运层"
            options={TRANSIT_MODES.map((m) => ({ value: m.id, label: m.label }))}
            value={mode}
            onChange={setMode}
          />
        </div>
        <p className="max-w-md text-sm leading-relaxed text-ink-muted">{t(config.blurb)}</p>
      </div>

      <div className="grid grid-cols-1 items-start gap-6 xl:grid-cols-12">
        <div className="flex flex-col gap-6 xl:col-span-7">
          <ResultCard
            title="行运双轮盘"
            icon="compass"
            actions={<span className="label-caps text-gold-soft">{t('{{short}}叠加本命', { short: t(config.short) })}</span>}
            elevated
          >
            <div className="relative mx-auto aspect-square w-full max-w-[620px]">
              <TransitBiWheel natal={chart.natal} positions={positions} aspects={aspects} />
            </div>
            <WheelLegend />
          </ResultCard>

          <ResultCard
            title="移动层对本命相位"
            icon="sparkle"
            actions={<span className="label-caps text-ink-muted">{t('{{count}} 条 · 按容许度排序', { count: aspects.length })}</span>}
            elevated
          >
            <CrossAspectList aspects={aspects} />
          </ResultCard>
        </div>

        <div className="flex flex-col gap-6 xl:col-span-5">
          <ResultCard
            title={t('{{short}}行星位置', { short: t(config.short) })}
            icon="gauge"
            actions={<span className="label-caps text-ink-muted">{t('落本命十二宫')}</span>}
            elevated
          >
            <MovingPointTable points={positions} />
          </ResultCard>

          <ProgressionCard progression={chart.progression} />
          <SolarArcCard solarArc={chart.solar_arc} />
        </div>
      </div>

      <ResultCard
        title="白话详解"
        icon="sparkle"
        actions={<span className="label-caps text-ink-muted">{t('五段 · 逐条转述已算出的相位与标志位')}</span>}
        elevated
      >
        <PlainSectionList sections={chart.plain} />
      </ResultCard>
    </>
  );
}

/** Headline strip: the target date, natal trinity and the two arc/age markers. */
function SummaryStrip({ chart }: { chart: TransitChart }) {
  const { t } = useI18n();
  const natal = chart.natal;
  return (
    <div className="panel flex flex-col gap-4 p-5 sm:p-6">
      <div className="flex flex-col gap-1">
        <span className="label-caps">{t('行运推运 · TRANSIT OVERLAY')}</span>
        <span className="font-display text-2xl font-bold tracking-wide text-gold-bright text-glow-gold sm:text-3xl">
          {t('目标日 {{date}}', { date: chart.target_date })}
        </span>
      </div>
      <div className="gold-rule" />
      <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-ink-variant">
        <span>
          {t('本命：')}<span className="text-ink">{t('日{{sun}} · 月{{moon}} · 升{{asc}}', { sun: natal.sun_sign_zh, moon: natal.moon_sign_zh, asc: natal.ascendant_sign_zh })}</span>
        </span>
        <span>
          {t('当地生时：')}<span className="numeric text-ink">{natal.local_datetime}</span>
        </span>
        <span>
          {t('周岁：')}<span className="numeric text-gold-soft">{formatAgeYears(chart.progression.age_years)}</span>
        </span>
        <span>
          {t('太阳弧：')}<span className="numeric text-gold-soft">{chart.solar_arc.arc_text}</span>
        </span>
        <span>
          {t('次限推运日：')}<span className="numeric text-ink">{chart.progression.progressed_date}</span>
        </span>
      </div>
    </div>
  );
}

/** Secondary-progression highlights: the progressed Moon and angles. */
function ProgressionCard({ progression }: { progression: ProgressionBlock }) {
  const { t } = useI18n();
  return (
    <ResultCard title="次限推运要点" icon="clock" elevated>
      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm">
          <span className="flex items-center gap-2 rounded-element border border-rim-soft bg-surface/60 px-3 py-1.5">
            <span className="text-ink-muted">{t('推运太阴')}</span>
            <span className="font-display text-base text-gold-bright">{progression.moon_sign_zh}</span>
            <span className="text-ink-muted">{t('落本命第 {{n}} 宫', { n: progression.moon_natal_house })}</span>
          </span>
          <span className="numeric text-xs text-ink-muted">{formatAgeYears(progression.age_years)} · {t('一日当一年')}</span>
        </div>
        <div className="grid grid-cols-2 gap-2">
          {progression.angles.map((angle) => (
            <div key={angle.name} className="flex flex-col gap-0.5 rounded-element border border-rim-soft bg-surface/60 px-3 py-2">
              <span className="label-caps text-ink-muted">
                {angle.name === 'ASC' ? t('推运上升') : t('推运天顶')} · {angle.name}
              </span>
              <span className="text-sm text-ink">
                {angle.sign_zh} <span className="numeric text-ink-variant">{angle.degree_text}</span>
              </span>
            </div>
          ))}
        </div>
        <p className="text-xs leading-relaxed text-ink-muted">
          {t('次限盘以出生后第 N 日的天象应第 N 年（{{date}}）。切换到「次限」层可在双轮盘与相位表中查看推运行星对本命的全部相位。', { date: progression.progressed_date })}
        </p>
      </div>
    </ResultCard>
  );
}

/** Solar-arc highlights: the directed arc and how to read it. */
function SolarArcCard({ solarArc }: { solarArc: SolarArcBlock }) {
  const { t } = useI18n();
  return (
    <ResultCard title="太阳弧推进" icon="sun" elevated>
      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-3 rounded-element border border-rim-soft bg-surface/60 px-3 py-2">
          <span className="text-ink-muted">{t('推进弧')}</span>
          <span className="font-display text-2xl text-gold-bright text-glow-gold">{solarArc.arc_text}</span>
          <span className="numeric text-xs text-ink-muted">({solarArc.arc_degrees.toFixed(2)}°)</span>
        </div>
        <p className="text-xs leading-relaxed text-ink-muted">
          {t('太阳弧把本命每一颗星往前推同一段弧度，相位表列的是推后之星与本命的关系，读的时候要连着前两层一起看。切换到「太阳弧」层可在双轮盘与相位表中查看推进星对本命的相位。')}
        </p>
      </div>
    </ResultCard>
  );
}

/** Legend: what the two rings mean plus the aspect chord colours. */
function WheelLegend() {
  const { t } = useI18n();
  return (
    <div className="mt-4 flex flex-col gap-2 border-t border-rim-soft pt-3">
      <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1 text-xs text-ink-variant">
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-3 w-3 rounded-full border-2 border-gold" />
          {t('外圈：移动层（带金环）')}
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-3 w-3 rounded-full border-2 border-ink-muted" />
          {t('内圈：本命盘（NATAL）')}
        </span>
        <span className="text-ink-muted">{t('连线为移动层对本命之相位')}</span>
      </div>
      <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1">
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
    </div>
  );
}
