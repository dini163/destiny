import { useState } from 'react';

import { CastControls } from '../components/zhouyi/CastControls';
import { CastLedger } from '../components/zhouyi/CastLedger';
import { ClassicalText } from '../components/zhouyi/ClassicalText';
import { HexagramCard } from '../components/zhouyi/HexagramCard';
import { HexagramStack } from '../components/zhouyi/HexagramStack';
import { Icon } from '../components/ui/Icon';
import { ProvenancePanel } from '../components/ui/ProvenancePanel';
import { ResultCard } from '../components/ui/ResultCard';
import { useZhouyiCast } from '../hooks/useZhouyiCast';
import { defaultManualCoins, methodLabel, positionLabel } from '../lib/zhouyi';
import type { CoinFace } from '../lib/zhouyi';
import type { CastMethod, ZhouyiCast, ZhouyiCastRequest } from '../types/zhouyi';

/**
 * Zhouyi / Liuyao divination page (周易六爻).
 *
 * The console casts a real hexagram via `useZhouyiCast`; the page then renders the
 * najia matrix (本卦 with its aligned 变卦 column), the throw ledger, the 变卦 /
 * 互卦 identity cards and the classical 卦爻辞 — every value taken straight from the
 * engine. The mockup's invented 用神/伏神/神煞/旺衰 annotations and case numbers are
 * omitted because the engine does not compute them (PRD no-mock rule).
 *
 * The 卦爻辞 panel carries each line's curated vernacular retelling above the received
 * text (丁组 spec §5), so there is no separate 白话 block on this page: the retelling
 * belongs to the line it translates.
 */
export function ZhouyiPage() {
  const [method, setMethod] = useState<CastMethod>('three_coin');
  const [question, setQuestion] = useState('');
  const [castTime, setCastTime] = useState('');
  const [manualCoins, setManualCoins] = useState<CoinFace[][]>(() => defaultManualCoins());
  const zhouyi = useZhouyiCast();

  function handleCast(): void {
    const trimmed = question.trim();
    const request: ZhouyiCastRequest = {
      method,
      question: trimmed === '' ? undefined : trimmed,
      cast_time: normalizeCastTime(castTime),
      manual_coins: method === 'manual' ? manualCoins : undefined,
    };
    zhouyi.mutate(request);
  }

  return (
    <div className="mx-auto flex w-full max-w-[1536px] flex-col gap-6 px-gutter py-8">
      <CastControls
        method={method}
        onMethodChange={setMethod}
        question={question}
        onQuestionChange={setQuestion}
        castTime={castTime}
        onCastTimeChange={setCastTime}
        manualCoins={manualCoins}
        onManualCoinsChange={setManualCoins}
        pending={zhouyi.isPending}
        onSubmit={handleCast}
      />

      {zhouyi.error ? (
        <div className="flex items-start gap-2 rounded-element border border-wuxing-fire/40 bg-wuxing-fire/10 px-4 py-3 text-sm text-ink">
          <Icon name="alert" size={18} className="mt-0.5 shrink-0 text-wuxing-fire" />
          <span>{zhouyi.error.message}</span>
        </div>
      ) : null}

      {zhouyi.isPending && !zhouyi.data ? (
        <p className="label-caps text-ink-muted">正在起卦排盘，推演纳甲六亲…</p>
      ) : null}

      {zhouyi.data ? <ZhouyiResults cast={zhouyi.data} /> : null}
    </div>
  );
}

/** `datetime-local` omits seconds; the backend wants `yyyy-mm-ddTHH:mm:ss`. */
function normalizeCastTime(value: string): string | undefined {
  const trimmed = value.trim();
  if (trimmed === '') {
    return undefined;
  }
  return trimmed.length === 16 ? `${trimmed}:00` : trimmed;
}

/** The full reading composition, rendered once a real cast is available. */
function ZhouyiResults({ cast }: { cast: ZhouyiCast }) {
  const { ben, bian, hu, lines, moving_positions } = cast;

  return (
    <>
      <CastSummary cast={cast} />

      <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-12">
        <div className="lg:col-span-8">
          <ResultCard title="纳甲六亲盘" eyebrow="NAJIA MATRIX" icon="seal" elevated>
            <HexagramStack ben={ben} bian={bian} lines={lines} />
          </ResultCard>
        </div>
        <div className="lg:col-span-4">
          <ResultCard title="起卦记录" eyebrow="CAST LEDGER" icon="timeline" className="lg:sticky lg:top-32">
            <CastLedger lines={lines} />
          </ResultCard>
        </div>
      </div>

      <div className="grid grid-cols-1 items-start gap-6 md:grid-cols-2">
        <ResultCard title="变卦" eyebrow="CHANGED · 之卦" icon="arrowRight">
          {bian ? (
            <HexagramCard hexagram={bian} moving={moving_positions} note="本卦动爻阴阳互变得变卦，示事之趋向。" />
          ) : (
            <p className="text-sm leading-relaxed text-ink-muted">
              六爻安静，本卦无动爻，故无变卦。占断以本卦卦辞与世应为主。
            </p>
          )}
        </ResultCard>
        <ResultCard title="互卦" eyebrow="NUCLEAR · 互卦" icon="vault">
          <HexagramCard hexagram={hu} note="取本卦二三四爻为下卦、三四五爻为上卦，得互卦，示事之中段。" />
        </ResultCard>
      </div>

      <ResultCard title="卦爻辞" eyebrow="CLASSICAL TEXT · 周易通行本" icon="sparkle" elevated>
        <ClassicalText ben={ben} lines={lines} />
      </ResultCard>

      <Provenance cast={cast} />
    </>
  );
}

/** The ben → bian headline plus the real cast metadata. */
function CastSummary({ cast }: { cast: ZhouyiCast }) {
  const { ben, bian, method, cast_time, day_ganzhi, question, moving_positions } = cast;

  return (
    <div className="panel-raised flex flex-col gap-4 p-5 sm:p-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <span className="label-caps">本卦 → 变卦 · PRIMARY TO CHANGED</span>
          <div className="flex flex-wrap items-center gap-3">
            <span className="font-display text-3xl leading-none text-gold">{ben.symbol}</span>
            <span className="font-display text-2xl font-semibold text-gold-bright text-glow-gold sm:text-3xl">
              {ben.full_name_zh}
            </span>
            <Icon name="arrowRight" size={22} className="text-gold" />
            {bian ? (
              <>
                <span className="font-display text-3xl leading-none text-gold-muted">{bian.symbol}</span>
                <span className="font-display text-2xl font-semibold text-ink sm:text-3xl">
                  {bian.full_name_zh}
                </span>
              </>
            ) : (
              <span className="font-display text-xl text-ink-muted">六爻安静 · 无变卦</span>
            )}
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="label-caps rounded-element bg-gold/15 px-2 py-1 text-gold">
            {methodLabel(method)}
          </span>
          <span className="label-caps rounded-element bg-wuxing-fire/15 px-2 py-1 text-wuxing-fire">
            {moving_positions.length} 爻动
          </span>
        </div>
      </div>

      <div className="gold-rule" />

      <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Meta label="起卦时刻" value={cast_time} />
        <Meta label="日柱" value={day_ganzhi} />
        <Meta label="本卦宫" value={`${ben.palace_name_zh} · ${ben.generation}`} />
        <Meta
          label="动爻"
          value={moving_positions.length > 0 ? moving_positions.map(positionLabel).join('、') : '无'}
        />
      </dl>

      {question ? (
        <p className="text-sm leading-relaxed text-ink-variant">
          <span className="label-caps mr-2 align-middle">所占之事</span>
          {question}
        </p>
      ) : null}
    </div>
  );
}

/** A single caption + value pair in the summary strip. */
function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className="label-caps">{label}</dt>
      <dd className="font-display text-sm text-ink-variant">{value}</dd>
    </div>
  );
}

/** Methodology + provenance note anchored to the real cast engine. */
function Provenance({ cast }: { cast: ZhouyiCast }) {
  return (
    <div className="panel flex flex-col gap-4 p-5 sm:p-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <Icon name="seal" size={22} className="mt-0.5 shrink-0 text-gold" />
          <div className="flex flex-col gap-1">
            <span className="font-display text-base text-ink">起卦溯源与免责</span>
            <p className="max-w-3xl text-sm leading-relaxed text-ink-muted">
              本次以 <span className="text-gold-soft">{methodLabel(cast.method)}</span> 起卦，由{' '}
              <span className="text-gold-soft">{cast.engine}</span> 依《周易》通行本与京房纳甲法真实推演；铜钱取爻以{' '}
              <span className="text-gold-soft">{cast.rng}</span> 加密安全乱数决定，梅花时间法则依起卦时刻定数。
              六爻为传统象数自省工具，结果仅供文化参考，不构成医疗、法律、财务或人生重大决策建议。
            </p>
          </div>
        </div>
        <span className="label-caps shrink-0 text-ink-muted">ENGINE · {cast.engine}</span>
      </div>

      <ProvenancePanel tables={cast.provenance.tables} />

      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-ink-muted">
        <span className="label-caps">历法 · {cast.provenance.engine}</span>
        <span className="label-caps">CONTENT · {cast.provenance.content_version}</span>
      </div>
    </div>
  );
}
