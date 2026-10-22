import { useState } from 'react';

import { SynastryAspectList } from '../components/synastry/SynastryAspectList';
import { SynastryBiWheel } from '../components/synastry/SynastryBiWheel';
import { SynastryConsole, type SideState } from '../components/synastry/SynastryConsole';
import { SynastryScoreRing } from '../components/synastry/SynastryScoreRing';
import { ProfilePicker } from '../components/profiles/ProfilePicker';
import { ProfileEditor } from '../components/profiles/ProfileEditor';
import { AstroWheel } from '../components/western/AstroWheel';
import { ElementBalance } from '../components/western/ElementBalance';
import { HouseTable } from '../components/western/HouseTable';
import { Icon } from '../components/ui/Icon';
import { PlainProse } from '../components/ui/PlainProse';
import { ResultCard } from '../components/ui/ResultCard';
import { VerdictCard } from '../components/ui/VerdictCard';
import { useSynastry } from '../hooks/useSynastry';
import { useProfiles } from '../hooks/useProfiles';
import type { PersonProfile, ProfileDraft } from '../lib/profiles';
import { aspectStyle } from '../lib/astro';
import type { SynastryChart, SynastryRequest } from '../types/synastry';

/** The five major aspects, for the wheel's colour legend. */
const ASPECT_LEGEND: ReadonlyArray<{ type: string; angle: string }> = [
  { type: 'conjunction', angle: '0°' },
  { type: 'sextile', angle: '60°' },
  { type: 'square', angle: '90°' },
  { type: 'trine', angle: '120°' },
  { type: 'opposition', angle: '180°' },
];

/**
 * 西洋合盘页（Synastry & Composite）。
 *
 * 一页 = 双人输入台 + 相契度总分环 + 合盘双轮盘 + 人对人相位清单 + 组合盘（中点盘）
 * + 组合盘元素形态与宫头。「算法与星历溯源」整块按 2026-10-21 UI 需求隐藏（后端
 * provenance payload 原样不动）。所有星体黄经、四轴与宫头皆由瑞士星历实时计算，组合盘
 * 取两造同名点的短弧中点（纯几何、可复算），相契度只由「人对人」的合盘相位按模型参数加权
 * 累加，账本逐条可核（PRD 无 mock 铁律）。页面上唯一的意志是两造生辰、定位与共用分宫制。
 */
export function SynastryPage() {
  const [sideAPreset, setSideAPreset] = useState<SideState | null>(null);
  const [sideBPreset, setSideBPreset] = useState<SideState | null>(null);
  /** 存入档案弹层的预填值（当前一侧输入快照，无 id = 新建）。 */
  const [draftPrefill, setDraftPrefill] = useState<ProfileDraft | null>(null);
  const [editorOpen, setEditorOpen] = useState(false);
  const { profiles, upsert } = useProfiles();
  const synastry = useSynastry();

  /** 档案 → 一侧 preset（公历、UTC 留空按经度推算）。 */
  function presetOf(profile: PersonProfile): SideState {
    return {
      name: profile.name ?? '',
      birthDate: profile.birth_date ?? '',
      birthTime: profile.birth_time ?? '',
      location: {
        city: profile.city ?? null,
        latitude: profile.latitude ?? null,
        longitude: profile.longitude ?? null,
      },
      utcOffset: '',
    };
  }

  function handleSubmit(request: SynastryRequest): void {
    synastry.mutate(request);
  }

  /** 一侧 → 存入档案弹层：称谓作姓名；合盘无造向，gender 留给读者自己选。 */
  function handleSaveProfile(_side: 'A' | 'B', state: SideState): void {
    setDraftPrefill({
      name: state.name.trim() || undefined,
      birth_date: state.birthDate,
      birth_time: state.birthTime,
      calendar: 'solar',
      city: state.location.city ?? null,
      latitude: state.location.latitude ?? null,
      longitude: state.location.longitude ?? null,
    });
    setEditorOpen(true);
  }

  return (
    <div className="mx-auto flex w-full max-w-[1536px] flex-col gap-6 px-gutter py-8">
      <div className="flex flex-wrap items-center gap-2">
        <ProfilePicker
          label="甲方 · 选档案"
          profiles={profiles}
          onPick={(profile) => setSideAPreset(profile ? presetOf(profile) : null)}
        />
        <ProfilePicker
          label="乙方 · 选档案"
          profiles={profiles}
          onPick={(profile) => setSideBPreset(profile ? presetOf(profile) : null)}
        />
      </div>
      <SynastryConsole
        sideAPreset={sideAPreset}
        sideBPreset={sideBPreset}
        onSaveProfile={handleSaveProfile}
        pending={synastry.isPending}
        onSubmit={handleSubmit}
      />

      {editorOpen ? (
        <ProfileEditor
          initial={draftPrefill}
          onSave={(draft) => upsert(draft)}
          onClose={() => setEditorOpen(false)}
        />
      ) : null}

      {synastry.error ? (
        <div className="flex items-start gap-2 rounded-element border border-wuxing-fire/40 bg-wuxing-fire/10 px-4 py-3 text-sm text-ink">
          <Icon name="alert" size={18} className="mt-0.5 shrink-0 text-wuxing-fire" />
          <span>{synastry.error.message}</span>
        </div>
      ) : null}

      {synastry.isPending && !synastry.data ? (
        <p className="label-caps text-ink-muted">正在依瑞士星历比对两张本命盘、合成中点组合盘…</p>
      ) : null}

      {synastry.data ? <SynastryResults chart={synastry.data} /> : null}
    </div>
  );
}

/** The full two-person composition rendered once a real result is available. */
function SynastryResults({ chart }: { chart: SynastryChart }) {
  const { composite } = chart;
  return (
    <>
      <SummaryStrip chart={chart} />

      <VerdictCard verdict={chart.verdict} />

      <ResultCard
        eyebrow="COMPATIBILITY SCORE"
        title="相契度总分"
        icon="gauge"
        actions={
          <span className="label-caps text-ink-muted">
            {chart.synastry_aspects.filter((a) => a.counted).length} 条计入 · 账本 {chart.score.factors.length} 行
          </span>
        }
        elevated
      >
        <div className="flex flex-col gap-4">
          <SynastryScoreRing score={chart.score} />
          <PlainProse
            text={chart.plain_summary}
            className="rounded-card border border-rim bg-surface p-4"
          />
        </div>
      </ResultCard>

      <div className="grid grid-cols-1 items-start gap-6 xl:grid-cols-12">
        <div className="flex flex-col gap-6 xl:col-span-7">
          <ResultCard
            title="合盘双轮盘"
            eyebrow="SYNASTRY BI-WHEEL"
            icon="compass"
            actions={<span className="label-caps text-gold-soft">内{chart.person_a_name} · 外{chart.person_b_name}</span>}
            elevated
          >
            <div className="relative mx-auto aspect-square w-full max-w-[620px]">
              <SynastryBiWheel
                chartA={chart.person_a}
                chartB={chart.person_b}
                aspects={chart.synastry_aspects}
                nameA={chart.person_a_name}
                nameB={chart.person_b_name}
              />
            </div>
            <WheelLegend />
          </ResultCard>

          <ResultCard
            title="人对人相位"
            eyebrow="SYNASTRY ASPECTS"
            icon="sparkle"
            actions={<span className="label-caps text-ink-muted">共 {chart.synastry_aspects.length} 对</span>}
            elevated
          >
            <SynastryAspectList aspects={chart.synastry_aspects} />
          </ResultCard>
        </div>

        <div className="flex flex-col gap-6 xl:col-span-5">
          <ResultCard
            title="组合中点盘"
            eyebrow="COMPOSITE CHART"
            icon="sun"
            actions={<span className="label-caps text-ink-muted">{composite.method} · 短弧中点</span>}
            elevated
          >
            <div className="flex flex-col gap-3">
              <p className="text-sm text-ink-variant">
                组合日
                <span className="font-display text-gold-bright"> {composite.sun_sign_zh} </span>· 组合月
                <span className="font-display text-gold-bright"> {composite.moon_sign_zh} </span>· 组合升
                <span className="font-display text-gold-bright"> {composite.ascendant_sign_zh}</span>
              </p>
              <div className="relative mx-auto aspect-square w-full max-w-[420px]">
                <AstroWheel
                  planets={composite.planets}
                  axes={composite.axes}
                  houses={composite.houses}
                  aspects={composite.aspects}
                />
              </div>
            </div>
          </ResultCard>

          <ResultCard title="组合盘元素与形态" eyebrow="COMPOSITE BALANCE" icon="seal" elevated>
            <ElementBalance
              elementBalance={composite.element_balance}
              modalityBalance={composite.modality_balance}
            />
          </ResultCard>

          <ResultCard title="组合盘十二宫头" eyebrow="COMPOSITE HOUSES" icon="timeline" elevated>
            <HouseTable houses={composite.houses} />
          </ResultCard>
        </div>
      </div>
    </>
  );
}

/** Headline strip: both natals' trinity plus the composite trinity. */
function SummaryStrip({ chart }: { chart: SynastryChart }) {
  const a = chart.person_a;
  const b = chart.person_b;
  const c = chart.composite;
  return (
    <div className="panel flex flex-col gap-4 p-5 sm:p-6">
      <div className="flex flex-col gap-1">
        <span className="label-caps">西洋合盘 · SYNASTRY &amp; COMPOSITE</span>
        <span className="font-display text-2xl font-bold tracking-wide text-gold-bright text-glow-gold sm:text-3xl">
          {chart.person_a_name} × {chart.person_b_name}
        </span>
      </div>
      <div className="gold-rule" />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <TrinityCell caption={chart.person_a_name} sun={a.sun_sign_zh} moon={a.moon_sign_zh} asc={a.ascendant_sign_zh} when={a.local_datetime} />
        <TrinityCell caption={chart.person_b_name} sun={b.sun_sign_zh} moon={b.moon_sign_zh} asc={b.ascendant_sign_zh} when={b.local_datetime} />
        <TrinityCell caption="组合盘 Composite" sun={c.sun_sign_zh} moon={c.moon_sign_zh} asc={c.ascendant_sign_zh} />
      </div>
    </div>
  );
}

/** One person's (or the composite's) 日/月/升 trinity in a compact cell. */
function TrinityCell({
  caption,
  sun,
  moon,
  asc,
  when,
}: {
  caption: string;
  sun: string;
  moon: string;
  asc: string;
  when?: string;
}) {
  return (
    <div className="flex flex-col gap-1.5 rounded-element border border-rim-soft bg-surface px-4 py-3">
      <span className="label-caps text-ink-muted">{caption}</span>
      <span className="font-display text-lg text-ink">
        日{sun} · 月{moon} · 升{asc}
      </span>
      {when ? <span className="numeric text-xs text-ink-muted">当地生时 {when}</span> : null}
    </div>
  );
}

/** Legend: what the two rings mean plus the aspect chord colours. */
function WheelLegend() {
  return (
    <div className="mt-4 flex flex-col gap-2 border-t border-rim-soft pt-3">
      <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1 text-xs text-ink-variant">
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-3 w-3 rounded-full border-2 border-gold" />
          外圈：乙方（带金环）
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-3 w-3 rounded-full border-2 border-ink-muted" />
          内圈：甲方
        </span>
        <span className="text-ink-muted">连线为计入相契度的人对人相位（核心轴更粗）</span>
      </div>
      <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1">
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
    </div>
  );
}
