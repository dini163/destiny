import { useState } from 'react';

import { DashaTimeline } from '../components/vedic/DashaTimeline';
import { GrahaTable } from '../components/vedic/GrahaTable';
import { NorthIndianChart } from '../components/vedic/NorthIndianChart';
import { SouthIndianChart } from '../components/vedic/SouthIndianChart';
import { Icon } from '../components/ui/Icon';
import { InputBar } from '../components/ui/InputBar';
import type { BirthInputValues } from '../components/ui/InputBar';
import { ChineseDateField } from '../components/ui/DateTimeField';
import { LabeledField } from '../components/ui/LabeledField';
import { ResultCard } from '../components/ui/ResultCard';
import { PlainSectionList } from '../components/ui/PlainSectionList';
import { SegmentedControl } from '../components/ui/SegmentedControl';
import { VerdictCard } from '../components/ui/VerdictCard';
import { useVedic } from '../hooks/useVedic';
import { useProfileFill } from '../hooks/useProfileFill';
import { CHART_STYLES } from '../lib/vedic';
import type { ChartStyle } from '../lib/vedic';
import type { VedicChart, VedicNatalRequest } from '../types/vedic';

/** Today's date as ISO `yyyy-mm-dd`, the default target for the live dasha. */
function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

/**
 * Vedic astrology page (吠陀占星 / Jyotish).
 *
 * The console collects Gregorian birth data plus location and a target date. On submit
 * the pyswisseph engine computes a sidereal chart under the Lahiri ayanamsa: the nine
 * grahas, whole-sign houses from the Lagna, the 27 nakshatras and the 120-year
 * Vimshottari dasha timeline. A segmented control switches between the South- and
 * North-Indian chart conventions. Every value is computed — nothing is invented at
 * runtime (PRD no-mock rule).
 */
export function VedicPage() {
  const [utcOffset, setUtcOffset] = useState('');
  const [targetDate, setTargetDate] = useState<string>(todayISO);
  const profile = useProfileFill();
  const vedic = useVedic();

  function handleSubmit(values: BirthInputValues): void {
    const request: VedicNatalRequest = {
      birth_date: values.birth_date,
      birth_time: values.birth_time,
      city: values.city,
      latitude: values.latitude,
      longitude: values.longitude,
      utc_offset_hours: utcOffset === '' ? undefined : Number(utcOffset),
      target_date: targetDate || todayISO(),
    };
    vedic.mutate(request);
  }

  return (
    <div className="mx-auto flex w-full max-w-[1536px] flex-col gap-6 px-gutter py-8">
      <InputBar
        title="吠陀占星 · 乔蒂什"
        badge="恒星黄道"
        subtitle="以拉希里（Lahiri / Chitrapaksha）岁差校正的恒星黄道排盘：九曜（Navagraha，含罗睺计都）、自上升起算的整宫制、二十七星宿（Nakshatra），并依月宿推排一百二十年的 Vimshottari 大运时间轴。示例：2000-01-01 12:00 · 格林尼治 (51.4769, -0.0005) · UTC 0。"
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
        submitLabel={vedic.isPending ? '恒星排盘中…' : '即刻排定星盘'}
        pending={vedic.isPending}
        onSubmit={handleSubmit}
        footerSlot={
          <div className="flex flex-wrap items-center gap-x-5 gap-y-1 rounded-element border border-rim-soft bg-surface px-3 py-2 text-xs text-ink-muted">
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-gold" />
              恒星黄道 = 回归黄道 − 岁差（Ayanamsa）
            </span>
            <span>整宫制自上升点起算第一宫；月宿决定 Vimshottari 起运。</span>
            <span className="text-gold-soft">目标日期用于标记现行大运。</span>
          </div>
        }
      >
        <LabeledField label="目标日期 / TARGET DATE">
          <ChineseDateField
            value={targetDate}
            onChange={setTargetDate}
            minYear={1900}
            maxYear={new Date().getFullYear() + 30}
            ariaLabel="目标"
          />
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

      {vedic.error ? (
        <div className="flex items-start gap-2 rounded-element border border-wuxing-fire/40 bg-wuxing-fire/10 px-4 py-3 text-sm text-ink">
          <Icon name="alert" size={18} className="mt-0.5 shrink-0 text-wuxing-fire" />
          <span>{vedic.error.message}</span>
        </div>
      ) : null}

      {vedic.isPending && !vedic.data ? (
        <p className="label-caps text-ink-muted">正在依拉希里岁差推排恒星盘、星宿与 Vimshottari 大运…</p>
      ) : null}

      {vedic.data ? <VedicResults chart={vedic.data} /> : null}

      {profile.editor}
    </div>
  );
}

/** The full composition: headline trinity, the chart-style switch, tables and dasha. */
function VedicResults({ chart }: { chart: VedicChart }) {
  const [style, setStyle] = useState<ChartStyle>('south');

  return (
    <>
      <SummaryStrip chart={chart} />

      <VerdictCard verdict={chart.verdict} />

      <div className="panel-raised flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-col gap-1.5">
          <span className="label-caps">排盘制式 / CHART STYLE</span>
          <SegmentedControl<ChartStyle>
            ariaLabel="排盘制式"
            options={CHART_STYLES.map((s) => ({ value: s.value, label: s.label }))}
            value={style}
            onChange={setStyle}
          />
        </div>
        <p className="max-w-md text-sm leading-relaxed text-ink-muted">
          {style === 'south'
            ? '南印盘：十二星座固定落位，自白羊起顺时针排列，宫位随上升点推移。'
            : '北印盘：十二宫固定落位，第一宫恒居顶部中央，星座编号随上升点轮转。'}
        </p>
      </div>

      <div className="grid grid-cols-1 items-start gap-6 xl:grid-cols-12">
        <ResultCard
          className="xl:col-span-5"
          title={style === 'south' ? '南印本命盘' : '北印本命盘'}
          eyebrow={style === 'south' ? 'SOUTH INDIAN RASHI' : 'NORTH INDIAN RASHI'}
          icon="compass"
          actions={
            <span className="label-caps text-gold-soft">
              上升 {chart.lagna_sign_zh} · 整宫制
            </span>
          }
          elevated
        >
          {style === 'south' ? <SouthIndianChart chart={chart} /> : <NorthIndianChart chart={chart} />}
        </ResultCard>

        <ResultCard
          className="xl:col-span-7"
          title="九曜星历表"
          eyebrow="NAVAGRAHA EPHEMERIS"
          icon="gauge"
          actions={<span className="label-caps text-ink-muted">恒星黄道 · 含星宿</span>}
          elevated
        >
          <GrahaTable chart={chart} />
        </ResultCard>
      </div>

      <ResultCard
        title="Vimshottari 大运时间轴"
        eyebrow="DASHA TIMELINE · 120 YEARS"
        icon="timeline"
        actions={
          <span className="label-caps text-ink-muted">
            自月宿 {chart.vimshottari.birth_nakshatra_zh} 起算
          </span>
        }
        elevated
      >
        <DashaTimeline vimshottari={chart.vimshottari} />
      </ResultCard>

      <ResultCard
        title="白话详解"
        eyebrow="PLAIN READING"
        icon="sparkle"
        actions={<span className="label-caps text-ink-muted">四段 · 逐条转述已算出的落座、落宫、宿与主事星</span>}
        elevated
      >
        <PlainSectionList sections={chart.plain} />
      </ResultCard>
    </>
  );
}

/** Headline strip: the Lagna, the Moon's sign/nakshatra, ayanamsa and current dasha. */
function SummaryStrip({ chart }: { chart: VedicChart }) {
  const current = chart.vimshottari.current;
  return (
    <div className="panel flex flex-col gap-4 p-5 sm:p-6">
      <div className="flex flex-col gap-1">
        <span className="label-caps">吠陀本命 · SIDEREAL NATAL</span>
        <span className="font-display text-2xl font-bold tracking-wide text-gold-bright text-glow-gold sm:text-3xl">
          上升 {chart.lagna_sign_glyph} {chart.lagna_sign_zh}
          <span className="numeric ml-2 text-base font-normal text-ink-variant">
            {chart.lagna_degree_text}
          </span>
        </span>
      </div>
      <div className="gold-rule" />
      <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-ink-variant">
        <span>
          月亮：<span className="text-ink">{chart.moon_sign_zh}</span> ·{' '}
          <span className="text-ink">{chart.moon_nakshatra_zh}</span>
          <span className="numeric text-ink-muted"> 第{chart.moon_pada}足</span>
        </span>
        <span>
          月宿主星：<span className="text-ink">{chart.moon_nakshatra_lord_zh}</span>
        </span>
        <span>
          当地生时：<span className="numeric text-ink">{chart.local_datetime}</span>
        </span>
        <span>
          岁差：<span className="numeric text-gold-soft">{chart.ayanamsa.toFixed(4)}°</span>
          <span className="text-ink-muted"> {chart.ayanamsa_name}</span>
        </span>
        {current ? (
          <span>
            现行大运：<span className="text-gold-bright">{current.mahadasha_lord_zh}</span>
            {current.antardasha_lord_zh ? (
              <>
                {' '}· 小运 <span className="text-gold-soft">{current.antardasha_lord_zh}</span>
              </>
            ) : null}
          </span>
        ) : null}
      </div>
    </div>
  );
}
