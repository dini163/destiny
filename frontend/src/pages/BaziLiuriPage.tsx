import { useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { LiuriFocusCard } from '../components/bazi/liuri/LiuriFocusCard';
import { LiuriMatrix } from '../components/bazi/liuri/LiuriMatrix';
import { LiuriSegmentHeader } from '../components/bazi/liuri/LiuriSegmentHeader';
import type { ShiftDirection } from '../components/bazi/liuri/LiuriSegmentHeader';
import { TransitErrorNote } from '../components/bazi/transit/TransitErrorNote';
import { TransitNatalBar } from '../components/bazi/transit/TransitNatalBar';
import { InputBar } from '../components/ui/InputBar';
import type { BirthInputValues } from '../components/ui/InputBar';
import { LabeledField } from '../components/ui/LabeledField';
import { ProvenancePanel } from '../components/ui/ProvenancePanel';
import { ResultCard } from '../components/ui/ResultCard';
import { SegmentedControl } from '../components/ui/SegmentedControl';
import { useBaziLiuri } from '../hooks/useBaziLiuri';
import { parseLiuriLink } from '../lib/transitLink';
import type { BaziLiuriRequest } from '../types/baziLiuri';
import type { Gender } from '../types/common';

const GENDER_OPTIONS: ReadonlyArray<{ value: Gender; label: string }> = [
  { value: 'male', label: '乾造' },
  { value: 'female', label: '坤造' },
];

/**
 * 本页两个 422 码的 `context` 键名 → 中文标签。
 *
 * 值一律取自 `error.context`（spec §8）：日期是后端定的段界，前端只是换个能排版的形状
 * 摆出来，不改写、不补算。流日的六个键全是 `YYYY-MM-DD` 串，与岁运那批年份数字共用
 * 同一件 `TransitErrorNote`。
 */
const CONTEXT_LABEL: Record<string, string> = {
  requested: '所请日期',
  supported_from: '本命可推起',
  supported_to: '本命可推终',
  focus_date: '聚焦日',
  month_start_solar: '本段起',
  month_end_solar: '本段终',
};

/** 拼一次流日请求：命盘入参照页的口径，两个日期由链接、格子点击或段切换决定。 */
function makeRequest(
  values: BirthInputValues,
  gender: Gender,
  applyTrueSolarTime: boolean,
  anchor: string | null,
  focus: string | null,
): BaziLiuriRequest {
  return {
    ...values,
    gender,
    apply_true_solar_time: applyTrueSolarTime,
    anchor_date: anchor,
    focus_date: focus,
  };
}

/**
 * ISO 日期加减若干天，仍在 ISO 里。
 *
 * `T00:00:00Z` + `setUTCDate` 是必须的：按本地时区做加减会在夏令时切换那两天跳错一天，
 * 而跳错一天的症状是整段矩阵少一天或多一天，没人会把它当时区问题去查。
 */
function shiftIso(iso: string, days: number): string {
  const next = new Date(`${iso}T00:00:00Z`);
  next.setUTCDate(next.getUTCDate() + days);
  return next.toISOString().slice(0, 10);
}

/**
 * 全月流日矩阵页（PRD §6.1.2）。
 *
 * 一页 = 命局条 + 段头 + 逐日矩阵 + 聚焦日详批 + 溯源。页面上只有两个日期是本页的意志：
 * `anchor_date` 定段、`focus_date` 定详批，两者留空即由服务端按参考日开窗并原样回显，
 * 本页不做第二次月界推算（决策 9）。段长、月名、段基准一切以响应为准。
 *
 * 入口在岁运页的月卡（`?…&anchor=交节日`），因此本路由不在导航栏里 —— 它是岁运的下钻，
 * 无生辰即无意义，不是一新一大体系（spec 决策 8）。
 */
export function BaziLiuriPage() {
  const [searchParams] = useSearchParams();
  const link = useMemo(() => parseLiuriLink(searchParams), [searchParams]);

  const [gender, setGender] = useState<Gender>(link?.gender ?? 'male');
  const [applyTrueSolarTime, setApplyTrueSolarTime] = useState(
    link?.applyTrueSolarTime ?? true,
  );

  const liuri = useBaziLiuri();
  /**
   * 最近一次提交的请求。点格与切段都只在它上面改一两个字段，其余（生辰、造向、锚日）
   * 原样交回 —— 这样「换一天看」不会顺带把用户没打算改的东西改掉。
   *
   * 用 ref 而不是 state：href 不在本页拼（那是岁运页的事），这几个 handler 是唯一读它
   * 的地方，渲染期不需要它参与。
   */
  const lastRequest = useRef<BaziLiuriRequest | null>(null);
  const autoSubmitted = useRef(false);

  useEffect(() => {
    if (!link || autoSubmitted.current) {
      return;
    }
    autoSubmitted.current = true;
    send(makeRequest(link.values, link.gender, link.applyTrueSolarTime, link.anchor, link.focus));
    // 依赖只留 `link`：`liuri.mutate` 是 react-query 给出的稳定引用，而这条链只允许在
    // 带合格查询串进入时放一次，跟着推演状态重跑就会反复发同一份请求。
  }, [link]);

  /** 发一次并记住发的是哪一份：段切换与下钻都要在它的基础上改字段。 */
  function send(request: BaziLiuriRequest): void {
    lastRequest.current = request;
    liuri.mutate(request);
  }

  function handleSubmit(values: BirthInputValues): void {
    send(
      makeRequest(
        values,
        gender,
        applyTrueSolarTime,
        link?.anchor ?? null,
        link?.focus ?? null,
      ),
    );
  }

  /**
   * 点一格 = 换 `focus_date` 整段重发。
   *
   * 契约里没有「只取一天」的半截载荷：简表本来就在手上，重发换来的是那一段加上这一天的
   * 明细（决策 5）。已经是聚焦日则什么都不发 —— 点同一格不该让段头翻一次账。
   */
  function handleFocus(solarDate: string): void {
    const previous = lastRequest.current;
    if (!previous || liuri.data?.focused?.solar_date === solarDate) {
      return;
    }
    send({ ...previous, focus_date: solarDate });
  }

  /**
   * 切段 = 换 `anchor_date` 再发一次，并且一律清空 `focus_date`。
   *
   * 清空是因为聚焦日几乎必然不落在新的那一段里：留着它只会换来一条
   * `liuri_focus_out_of_month`，而「上一段」的意图从来不是「还要看这一天」。
   * `0` 交回 `null`，让服务端按参考日开窗 —— 与直接进这一页是同一条路径。
   */
  function handleShift(direction: ShiftDirection): void {
    const result = liuri.data;
    const previous = lastRequest.current;
    if (!result || !previous) {
      return;
    }
    const anchor =
      direction === 0
        ? null
        : shiftIso(
            direction < 0 ? result.month_start_solar : result.month_end_solar,
            direction < 0 ? -1 : 1,
          );
    send({ ...previous, anchor_date: anchor, focus_date: null });
  }

  const showLinkNotice = link === null && [...searchParams.keys()].length > 0;
  const result = liuri.data;

  return (
    <div className="mx-auto flex w-full max-w-[1536px] flex-col gap-6 px-gutter py-8">
      <InputBar
        title="流日矩阵 · 全月逐日"
        badge="lunar-python 权威历算"
        subtitle="在一个节气月段内逐日结算加减：一格一天的气数、档位、命中与通书宜忌，点一格展开当日详批。示例：1988-02-15 23:30 · 成都 · 乾造。"
        showCalendar
        initial={link?.values}
        submitLabel={liuri.isPending ? '推演中…' : '开始推演'}
        pending={liuri.isPending}
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

      {showLinkNotice ? (
        <p className="label-caps text-ink-muted">链接参数不完整，请手动填写后查询。</p>
      ) : null}

      {liuri.error ? (
        <TransitErrorNote
          error={liuri.error}
          captions={CONTEXT_LABEL}
          hint="改选段内日期或换一段后重新推演。"
        />
      ) : null}

      {liuri.isPending && !result ? (
        <p className="label-caps text-ink-muted">正在按本命喜忌逐日结算…</p>
      ) : null}

      {result ? (
        <>
          <TransitNatalBar natal={result} />

          <LiuriSegmentHeader result={result} busy={liuri.isPending} onShift={handleShift} />

          <ResultCard
            eyebrow="DAILY MATRIX"
            title={`${result.month_ganzhi}月逐日矩阵`}
            icon="calendar"
            actions={<span className="label-caps text-ink-muted">点一格看当日详批</span>}
          >
            <LiuriMatrix
              days={result.days}
              referenceDate={result.provenance.reference_date}
              focusDate={result.focused?.solar_date ?? null}
              onSelect={handleFocus}
            />
          </ResultCard>

          {result.focused ? (
            <LiuriFocusCard detail={result.focused} />
          ) : (
            <p className="label-caps text-ink-muted">
              未聚焦任何一天 —— 点矩阵里任意一格即出当日详批。
            </p>
          )}

          {result.provenance ? (
            <ResultCard eyebrow="PROVENANCE" title="数据溯源" icon="seal">
              <ProvenancePanel
                tables={result.provenance.tables}
                meta={[
                  { label: '推演引擎', value: result.provenance.engine },
                  {
                    label: '参考日',
                    value: result.provenance.reference_date,
                    title: '请求未指定锚日时取服务器当日',
                  },
                  {
                    label: '本段起讫',
                    value: `${result.month_start_solar} ~ ${result.month_end_solar}`,
                  },
                  {
                    label: '真太阳时',
                    value: result.true_solar_time ?? '未校正（标准时直排）',
                  },
                  { label: '经度', value: `${result.longitude.toFixed(2)}°` },
                ]}
                notes={[
                  '逐日分数是岁运规则表在日段的加减账，不是吉凶断言；每一分都在账本里可核对（spec §6.1）。',
                  '段界取节气月（立春起寅月），与岁运页同段月卡逐字同源（决策 9）。',
                  '通书宜忌取自外部历法库，只作历注呈现，不参与本页任何计分（决策 6）。',
                ]}
              />
            </ResultCard>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
