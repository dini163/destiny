import { useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { LiushiDayHeader } from '../components/bazi/liushi/LiushiDayHeader';
import { LiushiFocusCard } from '../components/bazi/liushi/LiushiFocusCard';
import { LiushiHourLadder } from '../components/bazi/liushi/LiushiHourLadder';
import { LiushiPeakNote } from '../components/bazi/liushi/LiushiPeakNote';
import { LiushiQiWaveform } from '../components/bazi/liushi/LiushiQiWaveform';
import type { ShiftDirection } from '../components/bazi/liuri/LiuriSegmentHeader';
import { TransitErrorNote } from '../components/bazi/transit/TransitErrorNote';
import { TransitNatalBar } from '../components/bazi/transit/TransitNatalBar';
import { InputBar } from '../components/ui/InputBar';
import type { BirthInputValues } from '../components/ui/InputBar';
import { LabeledField } from '../components/ui/LabeledField';
import { PlainSectionList } from '../components/ui/PlainSectionList';
import { ResultCard } from '../components/ui/ResultCard';
import { SegmentedControl } from '../components/ui/SegmentedControl';
import { useBaziLiushi } from '../hooks/useBaziLiushi';
import { shiftIso } from '../lib/isoDate';
import { buildLiuriHref, buildLiushiQuery, parseLiushiLink } from '../lib/transitLink';
import type { BaziLiushiRequest, TransitHourCell } from '../types/baziLiushi';
import type { Gender } from '../types/common';

const GENDER_OPTIONS: ReadonlyArray<{ value: Gender; label: string }> = [
  { value: 'male', label: '乾造' },
  { value: 'female', label: '坤造' },
];

/** 本页两个 422 码的 `context` 键名 → 中文标签；值一律取自 `error.context`，不补算。 */
const CONTEXT_LABEL: Record<string, string> = {
  requested: '所请',
  supported: '可取时辰',
  supported_from: '本命可推起',
  supported_to: '本命可推终',
};

/**
 * 峰值那一格的下标，同分取更早的一格（决策 8）。
 *
 * 用严格大于：`>=` 会让"两个时辰同为峰值"时标晚的那个，而十二支的读者默认从子起读，
 * 标在后面的那格看起来像是页面挑错了。这一处不在后端算：契约里没有 `peak` 字段，
 * 给一个纯呈现层的判断开一条新契约不值。
 */
function peakIndexOf(hours: TransitHourCell[]): number {
  let best = 0;
  for (let index = 1; index < hours.length; index += 1) {
    if (hours[index].value > hours[best].value) {
      best = index;
    }
  }
  return best;
}

/** 拼一次流时请求：命盘入参照页口径，日与时辰由链接、格子点击或换日决定。 */
function makeRequest(
  values: BirthInputValues,
  gender: Gender,
  applyTrueSolarTime: boolean,
  date: string | null,
  hour: string | null,
): BaziLiushiRequest {
  return {
    ...values,
    gender,
    apply_true_solar_time: applyTrueSolarTime,
    solar_date: date,
    focus_hour_zhi: hour,
  };
}

/**
 * 一日十二时辰页（PRD §6.1.3、spec 切片 4）。
 *
 * 一页 = 命局条 + 日头 + 真气波形 + 十二格梯次谱 + 峰值备忘 + 聚焦时辰详批。
 * 页面上只有两件事是本页的意志：看哪一天、聚焦哪一支；两者留空即由服务端按参考日开窗，
 * 本页不做第二次月界与时辰边界推算（决策 2/9）。十二格共用一根日柱，所以日头那三段只
 * 出现一次（`day_score` / `day_fired`），每格多的只有 `shi.` 那一段。数据溯源段按
 * 2026-10-21 UI 需求隐藏（后端 `provenance` 载荷原样不动）。
 *
 * 入口在流日页的聚焦卡（`?…&date=同日&hour=辰`），因此本路由不在导航栏里 —— 它是流日
 * 的下钻，无生辰即无意义（spec 决策 8 的延伸）。
 */
export function BaziLiushiPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const link = useMemo(() => parseLiushiLink(searchParams), [searchParams]);

  const [gender, setGender] = useState<Gender>(link?.gender ?? 'male');
  const [applyTrueSolarTime, setApplyTrueSolarTime] = useState(link?.applyTrueSolarTime ?? true);
  const [lastRequest, setLastRequest] = useState<BaziLiushiRequest | null>(null);

  const liushi = useBaziLiushi();
  /**
   * 入口链接只允许自动发一次，闸门由 `send` 亲手落下。
   *
   * 必须是同步的 ref 而不是 state，因为有两处会把这条 effect 再点一次：① 本仓开着
   * `StrictMode`，挂载时 effect 跑两遍，两遍读到的都是同一帧的 `false`；② `send` 把自己
   * 那两键写回地址栏，`link` 因此变化并重跑 —— 那是本页写的一笔，不是新的下钻入口。两者
   * 的症状都是「一次查询发两份流时请求」（每份约 1.9 秒、35 KB）。流日页没有这一课，因为它
   * 不写查询串；这一页写，所以闸门必须落在发送的那一帧里。
   */
  const autoSubmitted = useRef(false);

  useEffect(() => {
    if (!link || autoSubmitted.current) {
      return;
    }
    send(makeRequest(link.values, link.gender, link.applyTrueSolarTime, link.date, link.hour));
    // 依赖只留 `link`：跟着推演状态重跑就会反复发同一份请求（与流日页同一条纪律）。
  }, [link]);

  /**
   * 发一次，并把自己那两键写回查询串（决策 12）。
   *
   * `replace: true`：换一格不该让"后退"变成把十二个时辰倒着走完。生辰半段原样交回
   * `buildLiushiQuery`，所以表单里改了城市而没点查询时，URL 跟着请求一起走，不出现
   * "地址是成都、画面上是北京"的错位。
   */
  function send(request: BaziLiushiRequest): void {
    autoSubmitted.current = true;
    setLastRequest(request);
    setSearchParams(
      buildLiushiQuery(request, {
        gender: request.gender,
        applyTrueSolarTime: request.apply_true_solar_time ?? true,
        date: request.solar_date ?? null,
        hour: request.focus_hour_zhi ?? null,
      }),
      { replace: true },
    );
    liushi.mutate(request);
  }

  function handleSubmit(values: BirthInputValues): void {
    send(
      makeRequest(
        values,
        gender,
        applyTrueSolarTime,
        link?.date ?? null,
        link?.hour ?? null,
      ),
    );
  }

  /** 点一格 = 换 `focus_hour_zhi` 整日重发；已是聚焦时辰则什么都不发。 */
  function handleFocus(zhi: string): void {
    const previous = lastRequest;
    if (!previous || liushi.data?.focused?.zhi === zhi) {
      return;
    }
    send({ ...previous, focus_hour_zhi: zhi });
  }

  /**
   * 换日 = `solar_date` ±1 天再发，并且**保留** `focus_hour_zhi`。
   *
   * 与流日页的 `handleShift` 相反（那里一律清空 `focus_date`）：一支在任何一天都存在，
   * 不会像聚焦日那样越界，清空反而让"换一天看同一时辰"变成两次点击（决策 10）。
   * `0` 交回 `null`，即请服务端按参考日开窗 —— 与直接进这一页同一条路径。
   */
  function handleShift(direction: ShiftDirection): void {
    const result = liushi.data;
    const previous = lastRequest;
    if (!result || !previous) {
      return;
    }
    const date = direction === 0 ? null : shiftIso(result.solar_date, direction < 0 ? -1 : 1);
    send({ ...previous, solar_date: date });
  }

  const showLinkNotice = link === null && [...searchParams.keys()].length > 0;
  const result = liushi.data;
  const peak = result ? peakIndexOf(result.hours) : 0;

  /**
   * 上钻回流日：`anchor` 与 `focus` 都交这一天，于是落点正是"这一日所在的节气月矩阵 +
   * 这一日的详批"。两个键给同一个日期不是偷懒——`anchor` 只管定段，缺了 `focus` 就会
   * 回到"未聚焦任何一天"的空态，读者从时辰页退回来却看到一张没点开日子的矩阵。
   */
  const liuriHref =
    result && lastRequest
      ? buildLiuriHref(lastRequest, {
          gender,
          applyTrueSolarTime,
          anchor: result.solar_date,
          focus: result.solar_date,
        })
      : undefined;

  return (
    <div className="mx-auto flex w-full max-w-[1536px] flex-col gap-6 px-gutter py-8">
      <InputBar
        title="流时十二辰 · 一日逐时"
        badge="权威历算"
        subtitle="在一个八字日内逐时辰结算加减：五鼠遁时柱、四段账本、日主临时支，点一格展开该时辰详批。示例：1988-02-15 23:30 · 成都 · 乾造。"
        showCalendar
        initial={link?.values}
        submitLabel={liushi.isPending ? '推演中…' : '开始推演'}
        pending={liushi.isPending}
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

      {liushi.error ? (
        <TransitErrorNote
          error={liushi.error}
          captions={CONTEXT_LABEL}
          hint="换一天或改选十二支之一后重新推演。"
        />
      ) : null}

      {liushi.isPending && !result ? (
        <p className="label-caps text-ink-muted">正在按本命喜忌逐时辰结算…</p>
      ) : null}

      {result ? (
        <>
          <TransitNatalBar natal={result} />

          <ResultCard title="流时白话" eyebrow="OVERALL READING · DAY" icon="sparkle" elevated>
            <PlainSectionList sections={result.plain} />
          </ResultCard>

          <LiushiDayHeader
            result={result}
            busy={liushi.isPending}
            liuriHref={liuriHref}
            onShift={handleShift}
          />

          <ResultCard
            eyebrow="QI WAVEFORM"
            title="一日真气"
            icon="timeline"
            actions={
              <span className="label-caps text-ink-muted">
                峰值 {result.hours[peak].ganzhi}·{Math.round(result.hours[peak].value)}
              </span>
            }
          >
            <LiushiQiWaveform
              hours={result.hours}
              baseline={result.day_score.value}
              peakIndex={peak}
            />
          </ResultCard>

          <ResultCard
            eyebrow="HOUR LADDER"
            title={`${result.day_ganzhi}日十二时辰`}
            icon="clock"
            actions={<span className="label-caps text-ink-muted">点一格看该时辰详批</span>}
          >
            <LiushiHourLadder
              hours={result.hours}
              peakIndex={peak}
              focusZhi={result.focused?.zhi ?? null}
              onSelect={handleFocus}
            />
          </ResultCard>

          <ResultCard eyebrow="PEAK NOTE" title="峰值备忘录" icon="gauge">
            <LiushiPeakNote cell={result.hours[peak]} dayValue={result.day_score.value} />
          </ResultCard>

          {result.focused ? (
            <LiushiFocusCard detail={result.focused} />
          ) : (
            <p className="label-caps text-ink-muted">
              未聚焦任何时辰 —— 点十二格里任意一格即出该时辰详批。
            </p>
          )}
        </>
      ) : null}
    </div>
  );
}
