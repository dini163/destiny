import { useState } from 'react';

import { DayunTimeline } from '../components/bazi/DayunTimeline';
import { PillarCard } from '../components/bazi/PillarCard';
import { StrengthDial } from '../components/bazi/StrengthDial';
import { WuxingBars } from '../components/bazi/WuxingBars';
import { Icon } from '../components/ui/Icon';
import { InputBar } from '../components/ui/InputBar';
import type { BirthInputValues } from '../components/ui/InputBar';
import { LabeledField } from '../components/ui/LabeledField';
import { ResultCard } from '../components/ui/ResultCard';
import { SegmentedControl } from '../components/ui/SegmentedControl';
import { useBaziNatal } from '../hooks/useBaziNatal';
import type { BaziChart, BaziNatalRequest } from '../types/bazi';
import type { Gender } from '../types/common';

const GENDER_OPTIONS: ReadonlyArray<{ value: Gender; label: string }> = [
  { value: 'male', label: '乾造' },
  { value: 'female', label: '坤造' },
];

/**
 * BaZi natal chart page (四柱推命).
 *
 * The input console collects birth data; on submit the chart is computed by the
 * backend (`useBaziNatal`) and rendered from real engine output only — four pillars,
 * day-master strength, five-element distribution and the luck-pillar axis. Nothing is
 * fabricated on the client (PRD no-mock rule).
 */
export function BaziNatalPage() {
  const [gender, setGender] = useState<Gender>('male');
  const [applyTrueSolarTime, setApplyTrueSolarTime] = useState(true);
  const bazi = useBaziNatal();

  function handleSubmit(values: BirthInputValues): void {
    const request: BaziNatalRequest = {
      ...values,
      gender,
      apply_true_solar_time: applyTrueSolarTime,
    };
    bazi.mutate(request);
  }

  return (
    <div className="mx-auto flex w-full max-w-[1536px] flex-col gap-6 px-gutter py-8">
      <InputBar
        title="四柱八字精算排盘"
        badge="lunar-python 权威历算"
        subtitle="真太阳时经度校正与节气精确交节，一次排定干支、十神、藏干、纳音、身强身弱与大运流年。示例：1988-02-15 23:30 · 成都 · 乾造。"
        showCalendar
        submitLabel={bazi.isPending ? '排盘中…' : '开始排盘'}
        pending={bazi.isPending}
        onSubmit={handleSubmit}
      >
        <LabeledField label="造向（性别）">
          <SegmentedControl
            ariaLabel="性别"
            options={GENDER_OPTIONS}
            value={gender}
            onChange={(next) => setGender(next)}
          />
        </LabeledField>
        <label className="flex cursor-pointer items-center gap-2 text-sm text-ink-variant">
          <input
            type="checkbox"
            checked={applyTrueSolarTime}
            onChange={(event) => setApplyTrueSolarTime(event.target.checked)}
            className="h-4 w-4 accent-[#d4af37]"
          />
          真太阳时校正（推荐）
        </label>
      </InputBar>

      {bazi.error ? (
        <div className="flex items-start gap-2 rounded-element border border-wuxing-fire/40 bg-wuxing-fire/10 px-4 py-3 text-sm text-ink">
          <Icon name="alert" size={18} className="mt-0.5 shrink-0 text-wuxing-fire" />
          <span>{bazi.error.message}</span>
        </div>
      ) : null}

      {bazi.isPending && !bazi.data ? (
        <p className="label-caps text-ink-muted">正在依据真太阳时排定四柱…</p>
      ) : null}

      {bazi.data ? <BaziResults chart={bazi.data} /> : null}
    </div>
  );
}

/** The full chart composition rendered once a real result is available. */
function BaziResults({ chart }: { chart: BaziChart }) {
  return (
    <>
      <ChartSummary chart={chart} />

      <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-12">
        <ResultCard
          className="lg:col-span-8"
          title="四柱命造干支矩阵"
          eyebrow="FOUR PILLARS MATRIX"
          icon="compass"
          actions={
            <span className="label-caps text-ink-muted">
              {chart.calendar === 'solar' ? '公历' : '农历'} · {chart.standard_datetime}
            </span>
          }
          elevated
        >
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            {chart.pillars.map((pillar) => (
              <PillarCard key={pillar.position} pillar={pillar} />
            ))}
          </div>
        </ResultCard>

        <div className="flex flex-col gap-6 lg:col-span-4">
          <ResultCard title="命局核心判定" eyebrow="DAY MASTER" icon="gauge" elevated>
            <StrengthDial analysis={chart.analysis} />
          </ResultCard>
          <ResultCard title="五行能量量化分布" eyebrow="WUXING" icon="seal" elevated>
            <WuxingBars scores={chart.wuxing} missing={chart.missing_elements} />
          </ResultCard>
        </div>
      </div>

      <ResultCard title="大运流变时间轴" eyebrow="DAYUN · 十年一步" icon="timeline" elevated>
        <DayunTimeline
          direction={chart.dayun_direction}
          startSolar={chart.dayun_start_solar}
          steps={chart.dayun}
          liunian={chart.current_liunian}
        />
      </ResultCard>

      <Provenance engine={chart.engine} />
    </>
  );
}

/** Headline strip: the four pillars plus the chart's key natal attributes. */
function ChartSummary({ chart }: { chart: BaziChart }) {
  const tst =
    chart.tst_applied && chart.true_solar_time
      ? `真太阳时 ${chart.true_solar_time}（校正 ${chart.tst_offset_minutes?.toFixed(1) ?? '0'} 分）`
      : '未校正（标准时直排）';

  return (
    <div className="panel flex flex-col gap-4 p-5 sm:p-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <span className="label-caps">四柱命造 · FOUR PILLARS</span>
          <span className="font-display text-3xl font-bold tracking-wide text-gold-bright text-glow-gold sm:text-4xl">
            {chart.four_pillars}
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Chip label="生肖" value={chart.zodiac} />
          <Chip label="日元" value={`${chart.day_master}（${chart.day_master_element}）`} />
          <Chip label="命宫" value={`${chart.ming_gong} · ${chart.ming_gong_nayin}`} />
          <Chip label="胎元" value={`${chart.tai_yuan} · ${chart.tai_yuan_nayin}`} />
        </div>
      </div>
      <div className="gold-rule" />
      <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-ink-variant">
        <span>
          农历：<span className="text-ink">{chart.lunar_date}</span>
        </span>
        <span>
          标准时：<span className="numeric text-ink">{chart.standard_datetime}</span>
        </span>
        <span className="text-gold-soft">{tst}</span>
        <span>
          经度：<span className="numeric text-ink">{chart.longitude.toFixed(2)}°</span>
        </span>
      </div>
    </div>
  );
}

/** A compact label/value chip used in the summary header. */
function Chip({ label, value }: { label: string; value: string }) {
  return (
    <span className="flex items-center gap-1.5 rounded-element border border-rim bg-[#0e111a] px-2.5 py-1 text-xs">
      <span className="label-caps">{label}</span>
      <span className="text-ink">{value}</span>
    </span>
  );
}

/** Methodology + provenance note anchored to the real computation engine. */
function Provenance({ engine }: { engine: string }) {
  return (
    <div className="panel flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-start gap-3">
        <Icon name="seal" size={22} className="mt-0.5 shrink-0 text-gold" />
        <div className="flex flex-col gap-1">
          <span className="font-display text-base text-ink">术数数理模型与文献溯源</span>
          <p className="max-w-3xl text-sm leading-relaxed text-ink-muted">
            四柱干支、十神、藏干、纳音与大运流年均由 <span className="text-gold-soft">{engine}</span>{' '}
            权威历算库排定；开启真太阳时时，先按出生经度与均时差校正再定日柱时柱。命理释义为传统阴阳五行数理文化的量化推演，仅供文化参考。
          </p>
        </div>
      </div>
      <span className="label-caps shrink-0 text-ink-muted">ENGINE · {engine}</span>
    </div>
  );
}
