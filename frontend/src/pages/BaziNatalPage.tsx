import { useState } from 'react';
import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';

import { DayunTimeline } from '../components/bazi/DayunTimeline';
import { DimensionGrid } from '../components/bazi/DimensionGrid';
import { GeJuCard } from '../components/bazi/GeJuCard';
import { HiddenStemTable } from '../components/bazi/HiddenStemTable';
import { PillarCard } from '../components/bazi/PillarCard';
import { RelationChips } from '../components/bazi/RelationChips';
import { ShenShaList } from '../components/bazi/ShenShaList';
import { StrengthDial } from '../components/bazi/StrengthDial';
import { WuxingBars } from '../components/bazi/WuxingBars';
import { YongshenPanel } from '../components/bazi/YongshenPanel';
import { Icon } from '../components/ui/Icon';
import type { IconName } from '../components/ui/Icon';
import { InputBar } from '../components/ui/InputBar';
import type { BirthInputValues } from '../components/ui/InputBar';
import { LabeledField } from '../components/ui/LabeledField';
import { ResultCard } from '../components/ui/ResultCard';
import { SegmentedControl } from '../components/ui/SegmentedControl';
import { pillarSlotLabel } from '../lib/pillars';
import { buildHehunPrefillHref, buildTransitHref } from '../lib/transitLink';
import { useBaziNatal } from '../hooks/useBaziNatal';
import type {
  BaziChart,
  BaziNatalRequest,
  DayunDetail,
  TenGodReading,
} from '../types/bazi';
import type { Gender } from '../types/common';

const GENDER_OPTIONS: ReadonlyArray<{ value: Gender; label: string }> = [
  { value: 'male', label: '乾造' },
  { value: 'female', label: '坤造' },
];

/**
 * BaZi natal chart page (四柱推命).
 *
 * The input console collects birth data; on submit the chart is computed by the
 * backend (`useBaziNatal`) and rendered in the sections of spec §8.2 — four
 * pillars, hidden-stem weights, five-element distribution, strength ledger and
 * 格局, 用神三法, 神煞, 刑冲合害, 大运 and 六维详批. Every figure opens into its score
 * ledger and every reading carries its own citation; nothing is composed on the
 * client (PRD no-mock rule). The data-provenance section is hidden per the
 * 2026-10-21 UI requirement (the backend `provenance` payload stays untouched).
 */
export function BaziNatalPage() {
  const [gender, setGender] = useState<Gender>('male');
  const [applyTrueSolarTime, setApplyTrueSolarTime] = useState(true);
  const [name, setName] = useState('');
  /** 这一造的岁运链接，随每次排盘同步；未排过时为 null，入口也随之消失。 */
  const [transitHref, setTransitHref] = useState<string | null>(null);
  /** 这一造的合婚预填链接，同样随每次排盘同步；未排过时为 null，入口随之消失。 */
  const [hehunHref, setHehunHref] = useState<string | null>(null);
  const bazi = useBaziNatal();

  function handleSubmit(values: BirthInputValues): void {
    const request: BaziNatalRequest = {
      ...values,
      gender,
      apply_true_solar_time: applyTrueSolarTime,
      name: name.trim() || null,
    };
    setTransitHref(buildTransitHref(values, { gender, applyTrueSolarTime }));
    setHehunHref(
      buildHehunPrefillHref(values, {
        side: gender,
        applyTrueSolarTime,
        name: name.trim() || null,
      }),
    );
    bazi.mutate(request);
  }

  return (
    <div className="mx-auto flex w-full max-w-[1536px] flex-col gap-6 px-gutter py-8">
      <InputBar
        title="四柱八字精算排盘"
        badge="权威历算"
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
        <LabeledField label="命主称谓（可选，仅回显）">
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            maxLength={40}
            placeholder="如：示例命主"
            className="w-full rounded-element border border-rim bg-[#0e111a] px-3 py-2 text-sm text-ink outline-none focus:border-rim-strong"
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

      {bazi.data ? (
        <BaziResults chart={bazi.data} transitHref={transitHref} hehunHref={hehunHref} />
      ) : null}
    </div>
  );
}

/** One rendered region of spec §8.2: its anchor, card chrome and body. */
interface SectionSpec {
  id: string;
  /** Short name in the sticky anchor nav. */
  label: string;
  title: string;
  eyebrow: string;
  icon: IconName;
  body: ReactNode;
}

/**
 * The section order of spec §8.2, as same-page anchors rather than tabs.
 *
 * One list owns the nav entries and the bodies, so a section the response did
 * not fill is absent from the nav as well as the page — an anchor that jumps to
 * nothing would be a broken promise (spec §8.2 规则 2、3).
 *
 * `transitHref` and `hehunHref` ride along into the 大运 block only: 岁运 is the next step
 * of the same question the luck pillars ask, while 合婚 is this chart's next step on the
 * 「跟谁」question — both need this chart's birth data to run.
 */
function sectionsFor(
  chart: BaziChart,
  transitHref: string | null,
  hehunHref: string | null,
): SectionSpec[] {
  const ledger = chart.hidden_stem_ledger ?? [];
  const relations = chart.relations ?? [];
  const branchGroups = chart.branch_groups ?? [];

  const specs: Array<SectionSpec | null> = [
    {
      id: 'pillars',
      label: '四柱',
      title: '四柱命造干支矩阵',
      eyebrow: 'FOUR PILLARS MATRIX',
      icon: 'compass',
      body: (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {chart.pillars.map((pillar) => (
            <PillarCard
              key={pillar.position}
              pillar={pillar}
              hidden_stem_rows={ledger.filter((row) => row.position === pillar.position)}
            />
          ))}
        </div>
      ),
    },
    ledger.length > 0
      ? {
          id: 'stems',
          label: '藏干十神',
          title: '地支藏干权重与十神',
          eyebrow: 'HIDDEN STEMS',
          icon: 'seal',
          body: (
            <div className="flex flex-col gap-4">
              <HiddenStemTable rows={ledger} />
              <TenGodList readings={chart.ten_god_readings ?? []} />
            </div>
          ),
        }
      : null,
    {
      id: 'wuxing',
      label: '五行',
      title: '五行能量量化分布',
      eyebrow: 'WUXING',
      icon: 'sparkle',
      body: <WuxingBars scores={chart.wuxing} missing={chart.missing_elements} />,
    },
    {
      id: 'strength',
      label: '强弱格局',
      title: '日主强弱与格局',
      eyebrow: 'STRENGTH & STRUCTURE',
      icon: 'gauge',
      body: (
        <div className="flex flex-col gap-4">
          <StrengthDial analysis={chart.analysis} />
          {chart.geju ? <GeJuCard geju={chart.geju} /> : null}
        </div>
      ),
    },
    chart.yongshen
      ? {
          id: 'yongshen',
          label: '用神三法',
          title: '用神三法（扶抑 / 通关 / 调候）',
          eyebrow: 'USEFUL GOD',
          icon: 'compass',
          body: <YongshenPanel yongshen={chart.yongshen} />,
        }
      : null,
    chart.shensha
      ? {
          id: 'shensha',
          label: '神煞',
          title: '神煞命中',
          eyebrow: 'SHENSHA',
          icon: 'vault',
          body: <ShenShaList entries={chart.shensha} />,
        }
      : null,
    relations.length > 0 || branchGroups.length > 0
      ? {
          id: 'relations',
          label: '刑冲合害',
          title: '刑冲合害破与合会局',
          eyebrow: 'RELATIONS',
          icon: 'compass',
          body: <RelationChips relations={relations} groups={branchGroups} />,
        }
      : null,
    {
      id: 'dayun',
      label: '大运',
      title: '大运流变时间轴',
      eyebrow: 'DAYUN · 十年一步',
      icon: 'timeline',
      body: (
        <div className="flex flex-col gap-4">
          <DayunTimeline
            direction={chart.dayun_direction}
            startSolar={chart.dayun_start_solar}
            steps={chart.dayun}
            liunian={chart.current_liunian}
          />
          {transitHref ? (
            <Link to={transitHref} className="btn-ghost self-start">
              <Icon name="timeline" size={16} />
              推演此造岁运流年
            </Link>
          ) : null}
          {hehunHref ? (
            <Link to={hehunHref} className="btn-ghost self-start">
              <Icon name="compass" size={16} />
              以此造合婚
            </Link>
          ) : null}
          {chart.dayun_current ? <CurrentDayun detail={chart.dayun_current} /> : null}
        </div>
      ),
    },
    chart.interpretation
      ? {
          id: 'dimensions',
          label: '六维详批',
          title: '六维详批',
          eyebrow: 'SIX DIMENSIONS',
          icon: 'sparkle',
          body: <DimensionGrid reading={chart.interpretation} />,
        }
      : null,
  ];

  return specs.filter((spec): spec is SectionSpec => spec !== null);
}

/** The full chart composition rendered once a real result is available. */
function BaziResults({
  chart,
  transitHref,
  hehunHref,
}: {
  chart: BaziChart;
  transitHref: string | null;
  hehunHref: string | null;
}) {
  const sections = sectionsFor(chart, transitHref, hehunHref);

  return (
    <>
      <ChartSummary chart={chart} />

      <nav
        aria-label="命盘分区"
        className="sticky top-0 z-10 flex flex-wrap items-center gap-x-4 gap-y-2 border-y border-rim bg-void/85 py-2 backdrop-blur"
      >
        {sections.map((section) => (
          <a
            key={section.id}
            href={`#${section.id}`}
            className="label-caps text-ink-muted hover:text-gold-soft"
          >
            {section.label}
          </a>
        ))}
      </nav>

      <div className="flex flex-col gap-6">
        {sections.map((section) => (
          <div key={section.id} id={section.id} className="scroll-mt-20">
            <ResultCard
              title={section.title}
              eyebrow={section.eyebrow}
              icon={section.icon}
              elevated
            >
              {section.body}
            </ResultCard>
          </div>
        ))}
      </div>
    </>
  );
}

/** 十神清点：命局出现的每个十神一条，落点与释义都来自后端。 */
function TenGodList({ readings }: { readings: TenGodReading[] }) {
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

/** 当前大运与命局的伏吟/反吟（`dayun_current`，只有关系，不含神煞）。 */
function CurrentDayun({ detail }: { detail: DayunDetail }) {
  return (
    <div className="flex flex-col gap-2 rounded-element border border-rim bg-[#0e111a] p-3">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <span className="label-caps text-gold-soft">当前大运 · {detail.ganzhi}</span>
        <span className="numeric text-xs text-ink-muted">
          {detail.start_age}—{detail.end_age} 岁
        </span>
      </div>
      {detail.relations.length > 0 ? (
        <RelationChips relations={detail.relations} groups={[]} />
      ) : (
        <p className="text-xs text-ink-muted">此运与四柱之间未构成伏吟或反吟。</p>
      )}
    </div>
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
          {chart.name ? <span className="text-sm text-ink-variant">{chart.name}</span> : null}
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
          {chart.provenance ? (
            <Chip label="参照日" value={chart.provenance.reference_date} />
          ) : null}
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
