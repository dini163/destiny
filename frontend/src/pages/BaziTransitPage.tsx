import { useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { TransitNatalBar } from '../components/bazi/transit/TransitNatalBar';
import { TransitErrorNote } from '../components/bazi/transit/TransitErrorNote';
import { TransitYearCard } from '../components/bazi/transit/TransitYearCard';
import { TransitYearTable } from '../components/bazi/transit/TransitYearTable';
import { Icon } from '../components/ui/Icon';
import { InputBar } from '../components/ui/InputBar';
import type { BirthInputValues } from '../components/ui/InputBar';
import { LabeledField } from '../components/ui/LabeledField';
import { ProvenancePanel } from '../components/ui/ProvenancePanel';
import { ResultCard } from '../components/ui/ResultCard';
import { SegmentedControl } from '../components/ui/SegmentedControl';
import { useBaziTransit } from '../hooks/useBaziTransit';
import { buildLiuriHref, parseTransitLink } from '../lib/transitLink';
import type {
  BaziTransitRequest,
  BaziTransitResult,
  TransitMonth,
  TransitYear,
} from '../types/baziTransit';
import type { Gender } from '../types/common';

const GENDER_OPTIONS: ReadonlyArray<{ value: Gender; label: string }> = [
  { value: 'male', label: '乾造' },
  { value: 'female', label: '坤造' },
];

/**
 * 跨度只有两档，取自服务端的 `TRANSIT_DEFAULT_YEARS` 与 `TRANSIT_MAX_YEARS`。
 * 数字在这里出现只是把两个合法选项摆出来；真越界时以 422 回文的 `context` 为准。
 */
const SPAN_OPTIONS: ReadonlyArray<{ value: '5' | '10'; label: string }> = [
  { value: '5', label: '5 年' },
  { value: '10', label: '10 年' },
];

/** 区间端点：起始年为空即整段交给服务端补齐，此时跨度无从附着。 */
interface TransitRangeField {
  start_year: number | null;
  end_year: number | null;
}

/**
 * 页顶四个 422 码的 `context` 键名 → 中文标签。
 *
 * 数值一律取自 `error.context`（spec §8）：文案是后端写的，数字也是后端算的，
 * 前端只是把它们换个能排版的形状摆出来，不改写、不补算。呈现由共用的
 * `TransitErrorNote` 负责，流日页带着自己那三个日期键的标签表用同一件。
 */
const CONTEXT_LABEL: Record<string, string> = {
  start_year: '区间起',
  end_year: '区间终',
  focus_year: '聚焦年',
  max_years: '跨度上限',
  requested: '实求跨度',
  supported_from: '本命可推起',
  supported_to: '本命可推终',
  requested_from: '所请起',
  requested_to: '所请终',
};

/** 拼一次岁运请求：命盘入参照页的口径，区间与聚焦年由本页控件决定。 */
function makeRequest(
  values: BirthInputValues,
  gender: Gender,
  applyTrueSolarTime: boolean,
  range: TransitRangeField,
  focusYear: number | null,
): BaziTransitRequest {
  return {
    ...values,
    gender,
    apply_true_solar_time: applyTrueSolarTime,
    ...range,
    focus_year: focusYear,
  };
}

/** 起始年输入 → 年份；空、非四位数字都不算填了。 */
function parseYear(raw: string): number | null {
  const trimmed = raw.trim();
  if (!/^\d{4}$/.test(trimmed)) {
    return null;
  }
  return Number(trimmed);
}

/**
 * 岁运推演页（PRD §6.1.4）。
 *
 * 一页 = 命局条 + 流年区间 + 单年详批（聚焦年再下钻十二节气月）+ 溯源。区间三个端点
 * 全部可空，缺省补齐只在服务端做一次，本页把结果原样回显，不再二次推算（spec §7.2）。
 * 页面上没有任何手算的平均或"综合评定"：分数一律走 `ScoreLedger` 展开的账本。
 *
 * 入口在主盘页的大运区块（`?birth_date=…` 查询串），因此本路由不在导航栏里 ——
 * 它是主盘的子页，不是一新一大体系（spec 决策 8）。
 */
export function BaziTransitPage() {
  const [searchParams] = useSearchParams();
  const link = useMemo(() => parseTransitLink(searchParams), [searchParams]);

  const [gender, setGender] = useState<Gender>(link?.gender ?? 'male');
  const [applyTrueSolarTime, setApplyTrueSolarTime] = useState(
    link?.applyTrueSolarTime ?? true,
  );
  const [startYear, setStartYear] = useState(link?.year ? String(link.year) : '');
  const [span, setSpan] = useState<'5' | '10'>('5');
  /** 点已展开的年份即收回详批卡：数据已在手上，收回不必再问一次服务端。 */
  const [collapsed, setCollapsed] = useState(false);

  const transit = useBaziTransit();
  /**
   * 最近一次提交的生辰：年表下钻与「看本段逐日」的链接都要在它上面拼，所以它得是
   * 渲染期读得到的 state 而不是 ref —— href 在 render 里算，ref 读到的只会是上一次的。
   */
  const [lastValues, setLastValues] = useState<BirthInputValues | null>(null);
  const autoSubmitted = useRef(false);

  useEffect(() => {
    if (!link || autoSubmitted.current) {
      return;
    }
    autoSubmitted.current = true;
    setLastValues(link.values);
    // 带上 `year` 的上钻链接要一次就落到那一年：区间以它为首年（+4 = 默认跨度 5 年减
    // 一，与 `span` 的初值同一口径），否则服务端会按参考日开窗，那一年多半在窗外，
    // 迎头就是一记 `transit_focus_out_of_range`。
    transit.mutate(
      makeRequest(
        link.values,
        link.gender,
        link.applyTrueSolarTime,
        link.year === null
          ? { start_year: null, end_year: null }
          : { start_year: link.year, end_year: link.year + 4 },
        link.year,
      ),
    );
    // 依赖只留 `link`：`transit.mutate` 是 react-query 给出的稳定引用，而这条链
    // 只允许在带合格查询串进入时放一次，跟着推演状态重跑就会反复发同一份请求。
  }, [link]);

  function rangeFields(): TransitRangeField {
    const start = parseYear(startYear);
    // 起始年留空时连结束年也不发：那一刻区间由服务端按参考日补齐（跨度默认 5 年）。
    if (start === null) {
      return { start_year: null, end_year: null };
    }
    return { start_year: start, end_year: start + Number(span) - 1 };
  }

  function handleSubmit(values: BirthInputValues): void {
    setLastValues(values);
    setCollapsed(false);
    transit.mutate(makeRequest(values, gender, applyTrueSolarTime, rangeFields(), null));
  }

  /** 点行 = 请这一年下钻；再点当前年 = 收回。聚焦年之后由服务端回显，不是本地状态。 */
  function handleFocus(year: number): void {
    const values = lastValues;
    if (transit.data?.focus_year === year) {
      setCollapsed((shown) => !shown);
      return;
    }
    setCollapsed(false);
    if (!values) {
      return;
    }
    transit.mutate(
      makeRequest(values, gender, applyTrueSolarTime, {
        start_year: transit.data?.start_year ?? null,
        end_year: transit.data?.end_year ?? null,
      }, year),
    );
  }

  const showLinkNotice = link === null && [...searchParams.keys()].length > 0;
  const focused: TransitYear | null = focusYear(transit.data, collapsed);

  /**
   * 月卡 → 流日矩阵的 href：`anchor` 交给该段的交节日，点进去就落在那一段上。
   * 组件自己不拼链接（决定 10）—— 生辰只在这里有，月卡拿到的是一条成品 href。
   */
  const liuriHrefFor = lastValues
    ? (month: TransitMonth) =>
        buildLiuriHref(lastValues, {
          gender,
          applyTrueSolarTime,
          anchor: month.start_solar,
        })
    : undefined;

  return (
    <div className="mx-auto flex w-full max-w-[1536px] flex-col gap-6 px-gutter py-8">
      <InputBar
        title="岁运推演 · 流年与流月"
        badge="lunar-python 权威历算"
        subtitle="沿用本命盘的喜忌，逐年逐月对岁运规则表结算加减：一年一行账，命中即可展开判语与凭据。示例：1988-02-15 23:30 · 成都 · 乾造。"
        showCalendar
        initial={link?.values}
        submitLabel={transit.isPending ? '推演中…' : '开始推演'}
        pending={transit.isPending}
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

        <LabeledField label="流年区间">
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2 rounded-element border border-rim bg-[#0e111a] px-3 py-2 transition focus-within:border-rim-strong">
              <Icon name="timeline" size={16} className="shrink-0 text-ink-muted" />
              <input
                className="numeric w-full bg-transparent text-sm text-ink outline-none placeholder:text-ink-muted"
                type="number"
                inputMode="numeric"
                min={1900}
                max={2100}
                step={1}
                value={startYear}
                onChange={(event) => setStartYear(event.target.value)}
                placeholder="起始年（留空 = 参考年起）"
                aria-label="起始年"
              />
            </div>
            <SegmentedControl
              ariaLabel="跨度"
              options={SPAN_OPTIONS}
              value={span}
              onChange={(next) => setSpan(next)}
            />
            <p className="text-xs leading-relaxed text-ink-muted">
              跨度只在填了起始年后生效：留空时区间由服务端按参考日取 5 年。
            </p>
          </div>
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

      {transit.error ? (
        <TransitErrorNote
          error={transit.error}
          captions={CONTEXT_LABEL}
          hint="改过起始年或跨度后可重新推演。"
        />
      ) : null}

      {transit.isPending && !transit.data ? (
        <p className="label-caps text-ink-muted">正在按本命喜忌结算岁运…</p>
      ) : null}

      {transit.data ? (
        <>
          <TransitNatalBar natal={transit.data} />

          <ResultCard
            eyebrow="ANNUAL LEDGER"
            title="流年区间账本"
            icon="timeline"
            actions={<RangeEcho result={transit.data} />}
          >
            <TransitYearTable
              years={transit.data.years}
              focusYear={collapsed ? null : transit.data.focus_year}
              onFocus={handleFocus}
            />
          </ResultCard>

          {focused ? <TransitYearCard year={focused} hrefFor={liuriHrefFor} /> : null}

          {transit.data.provenance ? (
            <ResultCard eyebrow="PROVENANCE" title="数据溯源" icon="seal">
              <ProvenancePanel
                tables={transit.data.provenance.tables}
                meta={[
                  { label: '推演引擎', value: transit.data.provenance.engine },
                  {
                    label: '大运参照日',
                    value: transit.data.provenance.reference_date,
                    title: '请求未指定时取服务器当日',
                  },
                  {
                    label: '区间',
                    value: `${transit.data.start_year}—${transit.data.end_year} 年`,
                  },
                  {
                    label: '真太阳时',
                    value: transit.data.true_solar_time ?? '未校正（标准时直排）',
                  },
                  { label: '经度', value: `${transit.data.longitude.toFixed(2)}°` },
                ]}
                notes={[
                  '岁运分数是规则表的加减账，不是吉凶断言；每一分都在账本里可核对（spec §6.1）。',
                  '喜忌沿用本命盘用神三法的合并结果，岁运不另立用神（spec 决策 3）。',
                ]}
              />
            </ResultCard>
          ) : null}
        </>
      ) : null}
    </div>
  );
}

/** 聚焦年对应的那一年；未请求聚焦年或已收回时不给卡片。 */
function focusYear(result: BaziTransitResult | undefined, collapsed: boolean): TransitYear | null {
  if (!result || result.focus_year === null || collapsed) {
    return null;
  }
  return result.years.find((year) => year.year === result.focus_year) ?? null;
}

/** 区间回显：端点与所跨运段都取自响应，本页不重复推算一遍。 */
function RangeEcho({ result }: { result: BaziTransitResult }) {
  return (
    <span className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs">
      <span className="flex items-center gap-1.5">
        <span className="label-caps text-ink-muted">区间</span>
        <span className="numeric text-ink">{`${result.start_year}—${result.end_year}`}</span>
      </span>
      <span className="flex items-center gap-1.5">
        <span className="label-caps text-ink-muted">所跨运段</span>
        <span className="numeric text-ink-variant">
          {result.dayun_covered
            .map((step) => `${step.ganzhi || '未起运'}（${step.start_year}—${step.end_year}）`)
            .join('、')}
        </span>
      </span>
      {result.focus_year !== null ? (
        <span className="flex items-center gap-1.5">
          <span className="label-caps text-ink-muted">聚焦</span>
          <span className="numeric text-gold-soft">{result.focus_year}</span>
        </span>
      ) : null}
    </span>
  );
}
