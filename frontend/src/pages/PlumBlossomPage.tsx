import { useState } from 'react';

import { HexagramTriad } from '../components/meihua/HexagramTriad';
import { MeihuaControls } from '../components/meihua/MeihuaControls';
import { MeihuaScoreLedger } from '../components/meihua/MeihuaScoreLedger';
import { TiYongPanel } from '../components/meihua/TiYongPanel';
import { Icon } from '../components/ui/Icon';
import { ResultCard } from '../components/ui/ResultCard';
import { VerdictCard } from '../components/ui/VerdictCard';
import { useMeihua } from '../hooks/useMeihua';
import { meihuaMethodLabel, movingPositionLabel } from '../lib/meihua';
import type { MeihuaCast, MeihuaCastRequest, MeihuaMethod } from '../types/meihua';

/** Three 报数 slots, kept as raw strings so the inputs stay editable. */
const EMPTY_NUMBERS = ['', '', ''];

/**
 * 梅花易数 divination page (Plum Blossom Numerology).
 *
 * The console raises a real hexagram via `useMeihua`; the page then renders the
 * 本 / 互 / 变 triptych, the 体用生克 reading, the 卦气旺衰 context and the 吉凶指数
 * ledger — every value taken straight from the engine (PRD no-mock rule). The
 * transparent 起卦 arithmetic (derivation.formula) is surfaced so the cast is
 * auditable, exactly as 邵康节's method prescribes.
 */
export function PlumBlossomPage() {
  const [method, setMethod] = useState<MeihuaMethod>('time');
  const [numbers, setNumbers] = useState<string[]>(() => EMPTY_NUMBERS.slice());
  const [question, setQuestion] = useState('');
  const [castTime, setCastTime] = useState('');
  const meihua = useMeihua();

  function handleCast(): void {
    const trimmed = question.trim();
    const request: MeihuaCastRequest = {
      method,
      numbers: method === 'number' ? parseNumbers(numbers) : undefined,
      question: trimmed === '' ? undefined : trimmed,
      cast_time: normalizeCastTime(castTime),
    };
    meihua.mutate(request);
  }

  return (
    <div className="mx-auto flex w-full max-w-[1536px] flex-col gap-6 px-gutter py-8">
      <MeihuaControls
        method={method}
        onMethodChange={setMethod}
        numbers={numbers}
        onNumbersChange={setNumbers}
        question={question}
        onQuestionChange={setQuestion}
        castTime={castTime}
        onCastTimeChange={setCastTime}
        pending={meihua.isPending}
        onSubmit={handleCast}
      />

      {meihua.error ? (
        <div className="flex items-start gap-2 rounded-element border border-wuxing-fire/40 bg-wuxing-fire/10 px-4 py-3 text-sm text-ink">
          <Icon name="alert" size={18} className="mt-0.5 shrink-0 text-wuxing-fire" />
          <span>{meihua.error.message}</span>
        </div>
      ) : null}

      {meihua.isPending && !meihua.data ? (
        <p className="label-caps text-ink-muted">正在起卦，推演体用互变…</p>
      ) : null}

      {meihua.data ? <MeihuaResults cast={meihua.data} /> : null}
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

/** Parse the 报数 slots into the positive integers the engine expects. */
function parseNumbers(values: string[]): number[] | undefined {
  const parsed = values
    .map((value) => value.trim())
    .filter((value) => value !== '')
    .map((value) => Number.parseInt(value, 10))
    .filter((value) => Number.isFinite(value) && value > 0);
  return parsed.length > 0 ? parsed : undefined;
}

/** The full reading composition, rendered once a real cast is available. */
function MeihuaResults({ cast }: { cast: MeihuaCast }) {
  return (
    <>
      <CastSummary cast={cast} />

      <VerdictCard verdict={cast.verdict} />

      <ResultCard title="卦象三盘" eyebrow="本 · 互 · 变" icon="seal" elevated>
        <HexagramTriad cast={cast} />
      </ResultCard>

      <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-12">
        <div className="lg:col-span-7">
          <ResultCard title="体用生克" eyebrow="TI · YONG" icon="compass">
            <TiYongPanel cast={cast} />
          </ResultCard>
        </div>
        <div className="lg:col-span-5">
          <ResultCard
            title="吉凶指数"
            eyebrow="FORTUNE INDEX"
            icon="gauge"
            className="lg:sticky lg:top-32"
          >
            <MeihuaScoreLedger cast={cast} />
          </ResultCard>
        </div>
      </div>

      <ResultCard title="互变推演" eyebrow="PROCESS · OUTCOME" icon="timeline">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <AnalysisBlock label="互卦 · 事之中段" text={cast.hu_analysis} />
          <AnalysisBlock label="变卦 · 事之归宿" text={cast.bian_analysis} />
        </div>
      </ResultCard>
    </>
  );
}

/** The ben → bian headline plus the real cast metadata and 起卦 arithmetic. */
function CastSummary({ cast }: { cast: MeihuaCast }) {
  const { ben, bian, method, cast_time, question, moving_position, derivation, wangshuai } = cast;

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
            <span className="font-display text-3xl leading-none text-gold-muted">{bian.symbol}</span>
            <span className="font-display text-2xl font-semibold text-ink sm:text-3xl">{bian.full_name_zh}</span>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="label-caps rounded-element bg-gold/15 px-2 py-1 text-gold">
            {meihuaMethodLabel(method)}
          </span>
          <span className="label-caps rounded-element bg-astral/15 px-2 py-1 text-astral">
            {movingPositionLabel(moving_position)}动
          </span>
        </div>
      </div>

      <div className="gold-rule" />

      <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Meta label="起卦时刻" value={cast_time} />
        <Meta label="月令卦气" value={`${wangshuai.season_zh} · ${wangshuai.commanding_element}当令`} />
        <Meta label="体卦" value={`${cast.ti.trigram.name_zh}${cast.ti.trigram.element}`} />
        <Meta label="用卦" value={`${cast.yong.trigram.name_zh}${cast.yong.trigram.element}`} />
      </dl>

      <div className="flex flex-col gap-1 rounded-element border border-rim-soft bg-[var(--field-bg)] px-3 py-2">
        <span className="label-caps text-ink-muted">起卦推演 · DERIVATION</span>
        <p className="numeric text-xs leading-relaxed text-ink-variant">{derivation.formula}</p>
        <p className="text-[11px] leading-relaxed text-ink-muted">{derivation.inputs}</p>
      </div>

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

/** One 互卦 / 变卦 tendency paragraph from the engine. */
function AnalysisBlock({ label, text }: { label: string; text: string }) {
  return (
    <div className="flex flex-col gap-1.5 rounded-element border border-rim-soft bg-surface/50 px-3 py-2.5">
      <span className="label-caps text-ink-muted">{label}</span>
      <p className="font-display text-sm leading-relaxed text-ink-variant">{text}</p>
    </div>
  );
}
