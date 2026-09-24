import { useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { DualBirthConsole } from '../components/bazi/hehun/DualBirthConsole';
import type { CompleteSides } from '../components/bazi/hehun/DualBirthConsole';
import { HehunFiredList } from '../components/bazi/hehun/HehunFiredList';
import { HehunPairMatrix } from '../components/bazi/hehun/HehunPairMatrix';
import { HehunPartnerProfiles } from '../components/bazi/hehun/HehunPartnerProfiles';
import { HehunScoreRing } from '../components/bazi/hehun/HehunScoreRing';
import { TransitErrorNote } from '../components/bazi/transit/TransitErrorNote';
import { ResultCard } from '../components/ui/ResultCard';
import { buildHehunQuery, parseHehunLink } from '../lib/transitLink';
import type { HehunSideLink } from '../lib/transitLink';
import { useBaziHehun } from '../hooks/useBaziHehun';
import type { BaziHehunRequest, HehunProfile } from '../types/baziHehun';

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
  male_available_from: '乾造可推起',
  female_available_from: '坤造可推起',
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
 * 一页 = 双造输入台 + 契合度总分环 + 乾坤档案对位（年命纳音随档案同区）+ 16 格对冲矩阵
 * + 命中清单 +（Task 12）互补图 + 同频轴 + 宜忌 + 溯源。页面上只有三件事是本页的意志：
 * 两半生辰、轴起哪一年、轴长几年；其余全部交回服务端口径。
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

  const [, setLastRequest] = useState<BaziHehunRequest | null>(null);
  const hehun = useBaziHehun();
  const autoSubmitted = useRef(false);

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

  const showLinkNotice = link === null && [...searchParams.keys()].length > 0;
  const result = hehun.data;

  return (
    <div className="mx-auto flex w-full max-w-[1536px] flex-col gap-6 px-gutter py-8">
      <DualBirthConsole
        initial={{ male: link?.male ?? null, female: link?.female ?? null }}
        pending={hehun.isPending}
        onSubmit={handleSubmit}
      />

      {showLinkNotice ? (
        <p className="label-caps text-ink-muted">链接参数不完整，请手动填写两造生辰后查询。</p>
      ) : null}

      {hehun.error ? (
        <TransitErrorNote
          error={hehun.error}
          captions={CONTEXT_LABEL}
          hint="改轴起年份或轴长后重新推演；一造排不出时会指明是乾造还是坤造。"
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
          </ResultCard>

          <ResultCard
            eyebrow="TWO CHARTS"
            title="乾坤档案对位"
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
        </>
      ) : null}
    </div>
  );
}
