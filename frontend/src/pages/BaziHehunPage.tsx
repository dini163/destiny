import { useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { DualBirthConsole } from '../components/bazi/hehun/DualBirthConsole';
import type { CompleteSides, SideState } from '../components/bazi/hehun/DualBirthConsole';
import { HehunAxisTimeline } from '../components/bazi/hehun/HehunAxisTimeline';
import { HehunComplementChart } from '../components/bazi/hehun/HehunComplementChart';
import { HehunFiredList } from '../components/bazi/hehun/HehunFiredList';
import { HehunPairMatrix } from '../components/bazi/hehun/HehunPairMatrix';
import { HehunPartnerProfiles } from '../components/bazi/hehun/HehunPartnerProfiles';
import { HehunScoreRing } from '../components/bazi/hehun/HehunScoreRing';
import { HehunYiJiPanel } from '../components/bazi/hehun/HehunYiJiPanel';
import { TransitErrorNote } from '../components/bazi/transit/TransitErrorNote';
import { PlainSectionList } from '../components/ui/PlainSectionList';
import { ResultCard } from '../components/ui/ResultCard';
import { VerdictCard } from '../components/ui/VerdictCard';
import { GENDER_LABEL, annotatePlainSections } from '../lib/gender';
import { buildHehunQuery, buildTransitHref, parseHehunLink } from '../lib/transitLink';
import type { HehunSideLink } from '../lib/transitLink';
import { useBaziHehun } from '../hooks/useBaziHehun';
import { useProfiles } from '../hooks/useProfiles';
import { profileToBirthInput, type PersonProfile, type ProfileDraft } from '../lib/profiles';
import { ProfileEditor } from '../components/profiles/ProfileEditor';
import { ProfilePicker } from '../components/profiles/ProfilePicker';
import type { BaziHehunRequest, HehunProfile, HehunSide } from '../types/baziHehun';

/** 轴的两个本地状态。`null` = 交回服务端按 §9.3 的口径决定。 */
export interface AxisState {
  startYear: number | null;
  years: number | null;
}

/**
 * 本页可能收到的 `context` 键 → 中文标签；值一律取自 `error.context`，不补算（§8）。
 *
 * 六个键就是合婚那两条域错误的全部 `context`：`hehun_axis_out_of_range` 给五个（§9.3），
 * `invalid_birth_data` 只再加一个 `partner`（§9.2）。轴的两个入参键（`axis_start_year` /
 * `axis_years`）**不在**此列 —— 后端把越界报成"所请起讫 vs 可推范围"，不是"你填了哪两个数"，
 * 所以那两格在这里出现只会是一张永不命中的表。
 */
const CONTEXT_LABEL: Record<string, string> = {
  partner: '造向',
  requested_from: '所请起',
  requested_to: '所请终',
  male_available_from: '乾造（男）可推起',
  female_available_from: '坤造（女）可推起',
  supported_to: '可推终',
};

/** 链接的一造 → 请求的一造。四个可空字段按 `types/baziHehun.ts` 文件头 ② 原样交 `null`。 */
function profileOf(link: HehunSideLink): HehunProfile {
  return {
    birth_date: link.values.birth_date,
    birth_time: link.values.birth_time,
    calendar: link.values.calendar ?? 'solar',
    city: link.values.city ?? null,
    latitude: link.values.latitude ?? null,
    longitude: link.values.longitude ?? null,
    apply_true_solar_time: link.applyTrueSolarTime,
    name: link.name,
  };
}

/**
 * 请求的一造 → 链接的一造（换轴长与换窗时要把自己那两键原样写回地址栏）。
 *
 * 它与 Task 11 的 {@link profileOf} 是一对逆函数，但**到这一页才落**：本页的
 * `send(sides, axis)` 收的是链接形状的两半，而轴控件手上有的是上一次请求（`lastRequest`），
 * 于是"请求 → 链接"这一步在这一页才第一次有人调用。提前写在 Task 11 里就是一个
 * `noUnusedLocals` 报错的模块级函数。
 */
function sideLinkOf(profile: HehunProfile): HehunSideLink {
  return {
    values: {
      birth_date: profile.birth_date,
      birth_time: profile.birth_time,
      calendar: profile.calendar,
      city: profile.city ?? null,
      latitude: profile.latitude ?? null,
      longitude: profile.longitude ?? null,
    },
    applyTrueSolarTime: profile.apply_true_solar_time ?? true,
    name: profile.name ?? null,
  };
}

/**
 * 轴行 → 那一造的岁运页，并聚焦那一年。
 *
 * `year` 直递 `buildTransitHref` 的 `year` 键：它是立春为界的流年号，与岁运页自己的
 * 口径同一（切片 2），所以从轴上点的 2029 落到那一页仍然是 2029 那一年。两造各一条
 * 链接、不合成一条 —— 轴上的"同频"说的是两个数之差，而"为什么是这个数"必须在各自
 * 那一页的账本里看（§10.5 同一把尺的另一半）。
 */
function transitHrefFor(request: BaziHehunRequest, side: HehunSide, year: number): string {
  const profile = side === 'male' ? request.male : request.female;
  const link = sideLinkOf(profile);
  return buildTransitHref(link.values, {
    gender: side,
    applyTrueSolarTime: link.applyTrueSolarTime,
    year,
  });
}

function makeRequest(sides: CompleteSides, axis: AxisState): BaziHehunRequest {
  return {
    male: profileOf(sides.male),
    female: profileOf(sides.female),
    axis_start_year: axis.startYear,
    axis_years: axis.years ?? undefined,
  };
}

/**
 * 双人合盘页（PRD §6.1.5、spec §8）。
 *
 * 一页 = 双造输入台 + 契合度总分环 + 男女档案对位（年命纳音随档案同区）+ 16 格对冲矩阵
 * + 命中清单 +（Task 12）互补图 + 同频轴 + 宜忌。页面上只有三件事是本页的意志：
 * 两半生辰、轴起哪一年、轴长几年；其余全部交回服务端口径。数据溯源段按 2026-10-21
 * UI 需求隐藏（后端 `provenance` 载荷原样不动）。
 *
 * 与流日/流时同一条入口纪律：链接带全**两半**才自动提交，只带一半（`以此造合婚` 的落点）
 * 即预填而不提交，也不报"链接不完整"。本页自己写查询串，所以那份自动提交由 `send` 里
 * 同步落下的 ref 闸门把住。流时 T9 那一课：`StrictMode` 跑两遍 + 自写回串重跑 effect，
 * 症状是一次进入发两份请求 —— 合婚这一份实测约 3.5 秒 / 27 KB（轴长 21；拉到 30 年 29 KB），
 * 贵的是两造排盘，不是那几行轴。
 */
export function BaziHehunPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const link = useMemo(() => parseHehunLink(searchParams), [searchParams]);

  const [lastRequest, setLastRequest] = useState<BaziHehunRequest | null>(null);
  /** 轴的两个本地状态；手动查询即清空（回到服务端口径，见 `handleSubmit`）。 */
  const [axis, setAxis] = useState<AxisState>({ startYear: null, years: null });
  /** 档案填充：乾/坤两造的 preset，映射为 HehunSideLink 注入 DualBirthConsole。 */
  const [malePreset, setMalePreset] = useState<HehunSideLink | null>(null);
  const [femalePreset, setFemalePreset] = useState<HehunSideLink | null>(null);
  /** 存入档案弹层的预填值（当前一造输入快照，无 id = 新建）。 */
  const [draftPrefill, setDraftPrefill] = useState<ProfileDraft | null>(null);
  const [editorOpen, setEditorOpen] = useState(false);
  const { profiles, upsert } = useProfiles();
  const hehun = useBaziHehun();
  const autoSubmitted = useRef(false);

  /** 档案 → 一造 preset；gender 决定它落到乾造还是坤造，无 gender 默认乾造。 */
  function handlePickProfile(profile: PersonProfile | null, side: HehunSide): void {
    if (!profile) {
      if (side === 'male') setMalePreset(null);
      else setFemalePreset(null);
      return;
    }
    const preset: HehunSideLink = {
      values: profileToBirthInput(profile),
      applyTrueSolarTime: true,
      name: profile.name ?? null,
    };
    if (side === 'male') setMalePreset(preset);
    else setFemalePreset(preset);
  }

  /** 一造 → 存入档案弹层：gender 由造向决定，称谓作姓名。 */
  function handleSaveProfile(side: HehunSide, state: SideState): void {
    setDraftPrefill({
      gender: side === 'male' ? 'male' : 'female',
      name: state.name.trim() || undefined,
      birth_date: state.birthDate,
      birth_time: state.birthTime,
      calendar: state.calendar,
      city: state.location.city ?? null,
      latitude: state.location.latitude ?? null,
      longitude: state.location.longitude ?? null,
    });
    setEditorOpen(true);
  }

  useEffect(() => {
    if (autoSubmitted.current || !link?.male || !link.female) {
      return;
    }
    send(
      { male: link.male, female: link.female },
      { startYear: link.axisStartYear, years: link.axisYears },
    );
    // 依赖只留 `link`：跟着推演状态重跑就会反复发同一份请求（与流日、流时同一条纪律）。
  }, [link]);

  /** 发一次，并把自己那几键写回查询串（与流时同形）。 */
  function send(sides: CompleteSides, axis: AxisState): void {
    autoSubmitted.current = true;
    const request = makeRequest(sides, axis);
    setLastRequest(request);
    setAxis(axis);
    setSearchParams(buildHehunQuery(sides, { axisStartYear: axis.startYear, axisYears: axis.years }), {
      replace: true,
    });
    hehun.mutate(request);
  }

  function handleSubmit(sides: CompleteSides): void {
    // 手动点「开始合婚」即回到服务端口径：轴的两个覆盖值一并清空。换一造还留着上一次的
    // 绝对窗口，是自造一个 `hehun_axis_out_of_range`（§9.3 的窗口由两造出生年决定）。
    send(sides, { startYear: null, years: null });
  }

  /**
   * 换轴长：留住两造生辰与当前窗口起点之外的全部状态。
   *
   * 起点一并清空，因为"5 年"接在"2026 起的 21 年窗"后面是三段话：读者要的是同一年的
   * 短窗，而留着绝对起点会让换长变成换窗。清成 `null` 即交回 §9.3 的缺省口径。
   */
  function handleYearsChange(value: string): void {
    const previous = lastRequest;
    if (!previous) {
      return;
    }
    const years = value === 'default' ? null : Number(value);
    send(sidesOf(previous), { startYear: null, years });
  }

  /**
   * 换窗：整块平移一个窗口的长度，轴长不变。
   *
   * 步长取 `rows.length` 而不是 1 年，于是两段轴恰好首尾相接（下一窗起 = 本窗讫 + 1），
   * 不重叠也不留缝。越界是允许的：那一条域错误会把可推范围原样说出来，而这正是读者
   * 从"再往前一点"这一格里最该知道的事。
   */
  function handleShift(direction: -1 | 1): void {
    const result = hehun.data;
    const previous = lastRequest;
    if (!result || !previous) {
      return;
    }
    const span = result.axis.rows.length;
    const start = direction < 0 ? result.axis.start_year - span : result.axis.end_year + 1;
    send(sidesOf(previous), { startYear: start, years: span });
  }

  /** 请求里的两造 → 链接里的两半（轴控件重发时不留失生辰）。 */
  function sidesOf(request: BaziHehunRequest): CompleteSides {
    return { male: sideLinkOf(request.male), female: sideLinkOf(request.female) };
  }

  const axisHrefFor = lastRequest
    ? (side: HehunSide, year: number): string => transitHrefFor(lastRequest, side, year)
    : null;

  const showLinkNotice = link === null && [...searchParams.keys()].length > 0;
  const result = hehun.data;

  return (
    <div className="mx-auto flex w-full max-w-[1536px] flex-col gap-6 px-gutter py-8">
      <div className="flex flex-wrap items-center gap-2">
        <ProfilePicker
          label={`${GENDER_LABEL.male} · 选档案`}
          profiles={profiles}
          onPick={(profile) => handlePickProfile(profile, 'male')}
        />
        <ProfilePicker
          label={`${GENDER_LABEL.female} · 选档案`}
          profiles={profiles}
          onPick={(profile) => handlePickProfile(profile, 'female')}
        />
      </div>
      <DualBirthConsole
        initial={{ male: link?.male ?? null, female: link?.female ?? null }}
        malePreset={malePreset}
        femalePreset={femalePreset}
        onSaveProfile={handleSaveProfile}
        pending={hehun.isPending}
        onSubmit={handleSubmit}
      />

      {editorOpen ? (
        <ProfileEditor
          initial={draftPrefill}
          onSave={(draft) => upsert(draft)}
          onClose={() => setEditorOpen(false)}
        />
      ) : null}

      {showLinkNotice ? (
        <p className="label-caps text-ink-muted">链接参数不完整，请手动填写两造生辰后查询。</p>
      ) : null}

      {hehun.error ? (
        <TransitErrorNote
          error={hehun.error}
          captions={CONTEXT_LABEL}
          hint="改轴起年份或轴长后重新推演；一造排不出时会指明是乾造（男）还是坤造（女）。"
        />
      ) : null}

      {hehun.isPending && !result ? (
        <p className="label-caps text-ink-muted">正在跨两张盘扫描关系、合局、互济与年命…</p>
      ) : null}

      {result ? (
        <>
          <ResultCard
            eyebrow="COMPATIBILITY SCORE"
            title="契合度总分"
            icon="gauge"
            actions={
              <span className="label-caps text-ink-muted">
                {result.fired.length} 条命中 · 账本 {result.score.factors.length} 行
              </span>
            }
          >
            <HehunScoreRing score={result.score} />
            <VerdictCard verdict={result.verdict} />
          </ResultCard>

          <ResultCard title="合盘白话" eyebrow="OVERALL READING · COMPATIBILITY" icon="sparkle" elevated>
            <PlainSectionList sections={annotatePlainSections(result.plain)} />
          </ResultCard>

          <ResultCard
            eyebrow="TWO CHARTS"
            title="男女档案对位"
            icon="vault"
            actions={<span className="label-caps text-ink-muted">喜忌与五行分布直取各造本命盘</span>}
          >
            <HehunPartnerProfiles male={result.male} female={result.female} nayin={result.nayin} />
          </ResultCard>

          <ResultCard
            eyebrow="PAIR MATRIX"
            title="四柱对冲矩阵"
            icon="compass"
            actions={<span className="label-caps text-ink-muted">16 格恒在 · 空格即「无」</span>}
          >
            <HehunPairMatrix cells={result.matrix} />
          </ResultCard>

          <ResultCard
            eyebrow="FIRED RULES"
            title="命中清单"
            icon="sparkle"
            actions={<span className="label-caps text-ink-muted">族序即账本序</span>}
          >
            <HehunFiredList rows={result.fired} />
          </ResultCard>

          <ResultCard
            eyebrow="FIVE-ELEMENT COMPLEMENT"
            title="五行互补"
            icon="vault"
            actions={<span className="label-caps text-ink-muted">两视角各一张 2×2</span>}
          >
            <HehunComplementChart complement={result.complement} />
          </ResultCard>

          <ResultCard
            eyebrow="SYNCHRONY AXIS"
            title="同频演进轴"
            icon="timeline"
            actions={<span className="label-caps text-ink-muted">分数与岁运年表同一把尺</span>}
          >
            <HehunAxisTimeline
              axis={result.axis}
              busy={hehun.isPending}
              axisYears={axis.years}
              hrefFor={axisHrefFor}
              onYearsChange={handleYearsChange}
              onShift={handleShift}
            />
          </ResultCard>

          <ResultCard
            eyebrow="DIRECTIONS & SEASONS"
            title="宜忌"
            icon="sun"
            actions={<span className="label-caps text-ink-muted">唯一输入是两造喜用</span>}
          >
            <HehunYiJiPanel yiJi={result.yi_ji} />
          </ResultCard>
        </>
      ) : null}
    </div>
  );
}
