import { useState } from 'react';

import { QimenBoard } from '../components/qimen/QimenBoard';
import { QimenControls } from '../components/qimen/QimenControls';
import { Icon } from '../components/ui/Icon';
import { PlainSectionList } from '../components/ui/PlainSectionList';
import { ProvenancePanel } from '../components/ui/ProvenancePanel';
import { ResultCard } from '../components/ui/ResultCard';
import { useQimen } from '../hooks/useQimen';
import type { QimenChart, QimenRequest } from '../types/qimen';

/**
 * 奇门遁甲 divination page (Qi Men Dun Jia).
 *
 * The console raises a real board via `useQimen`; the page then renders the 定局
 * metadata (阴阳遁·局数·节气三元·四柱·旬首·值符值使·旬空驿马) and the 洛书九宫 four-plate
 * grid — every value taken straight from the engine (PRD no-mock rule). The 用事时辰
 * defaults to now, so 起局 with no input casts the present moment.
 */
export function QimenPage() {
  const [question, setQuestion] = useState('');
  const [castTime, setCastTime] = useState('');
  const qimen = useQimen();

  function handleCast(): void {
    const trimmed = question.trim();
    const request: QimenRequest = {
      question: trimmed === '' ? undefined : trimmed,
      cast_time: normalizeCastTime(castTime),
    };
    qimen.mutate(request);
  }

  return (
    <div className="mx-auto flex w-full max-w-[1536px] flex-col gap-6 px-gutter py-8">
      <QimenControls
        question={question}
        onQuestionChange={setQuestion}
        castTime={castTime}
        onCastTimeChange={setCastTime}
        pending={qimen.isPending}
        onSubmit={handleCast}
      />

      {qimen.error ? (
        <div className="flex items-start gap-2 rounded-element border border-wuxing-fire/40 bg-wuxing-fire/10 px-4 py-3 text-sm text-ink">
          <Icon name="alert" size={18} className="mt-0.5 shrink-0 text-wuxing-fire" />
          <span>{qimen.error.message}</span>
        </div>
      ) : null}

      {qimen.isPending && !qimen.data ? (
        <p className="label-caps text-ink-muted">正在起局，布地盘、转九星八门八神…</p>
      ) : null}

      {qimen.data ? <QimenResults chart={qimen.data} /> : null}
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

/** The full board composition, rendered once a real 起局 is available. */
function QimenResults({ chart }: { chart: QimenChart }) {
  return (
    <>
      <JuSummary chart={chart} />

      <ResultCard
        title="洛书九宫盘"
        eyebrow="天地人神 · 四盘交错"
        icon="gauge"
        elevated
        actions={
          <span className="label-caps rounded-element bg-gold/15 px-2 py-1 text-gold">{chart.ju_name}</span>
        }
      >
        <QimenBoard chart={chart} />
      </ResultCard>

      <ResultCard title="九宫白话" eyebrow="PLAIN READING · 9 PALACES" icon="sparkle" elevated>
        <PlainSectionList
          sections={chart.palaces.map((palace) => ({
            title: `${palace.gua}${palace.number}宫 · ${palace.direction}`,
            text: palace.plain,
          }))}
        />
      </ResultCard>

      <Provenance chart={chart} />
    </>
  );
}

/** The 定局 headline plus the real 四柱 / 值符值使 / 空马 metadata. */
function JuSummary({ chart }: { chart: QimenChart }) {
  return (
    <div className="panel-raised flex flex-col gap-4 p-5 sm:p-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <span className="label-caps">定局 · JU DETERMINATION</span>
          <div className="flex flex-wrap items-baseline gap-3">
            <span className="font-display text-3xl font-semibold text-gold-bright text-glow-gold sm:text-4xl">
              {chart.ju_name}
            </span>
            <span className="font-display text-lg text-ink-variant">
              {chart.jieqi} · {chart.yuan}
            </span>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="label-caps rounded-element bg-astral/15 px-2 py-1 text-astral">
            值符 {chart.zhifu_star} 落{chart.zhifu_palace}宫
          </span>
          <span className="label-caps rounded-element bg-gold/15 px-2 py-1 text-gold">
            值使 {chart.zhishi_door} 落{chart.zhishi_palace}宫
          </span>
        </div>
      </div>

      <div className="gold-rule" />

      <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Meta label="年柱" value={chart.year_ganzhi} />
        <Meta label="月柱" value={chart.month_ganzhi} />
        <Meta label="日柱" value={chart.day_ganzhi} />
        <Meta label="时柱" value={chart.time_ganzhi} />
        <Meta label="时辰旬首" value={`${chart.xunshou}（遁${chart.xunshou_yi}）`} />
        <Meta label="旬空" value={chart.kongwang} />
        <Meta label="驿马" value={chart.yima} />
        <Meta label="用事时刻" value={chart.cast_time} />
      </dl>

      {chart.question ? (
        <p className="text-sm leading-relaxed text-ink-variant">
          <span className="label-caps mr-2 align-middle">占问事项</span>
          {chart.question}
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

/** Methodology + provenance note anchored to the real 起局 engine. */
function Provenance({ chart }: { chart: QimenChart }) {
  const { engine, source, school_note, content_version } = chart.provenance;
  return (
    <div className="panel flex flex-col gap-3 p-5">
      <div className="flex items-start gap-3">
        <Icon name="gauge" size={22} className="mt-0.5 shrink-0 text-gold" />
        <div className="flex flex-col gap-1">
          <span className="font-display text-base text-ink">起局溯源与口径</span>
          <p className="max-w-3xl text-sm leading-relaxed text-ink-muted">
            本局由 <span className="text-gold-soft">{engine}</span> 依{' '}
            <span className="text-gold-soft">{source}</span> 真实推演：年月日时干支与节气由{' '}
            <span className="text-gold-soft">lunar-python</span> 定数，九星八门八神与局数歌诀取自策展奇门数据，起局纯为确定性运算，未作运行时虚构。
          </p>
          <p className="max-w-3xl text-xs leading-relaxed text-ink-muted">{school_note}</p>
        </div>
      </div>
      <ProvenancePanel tables={chart.provenance.tables} />
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-ink-muted">
        <span className="label-caps">ENGINE · {engine}</span>
        <span className="label-caps">CONTENT · {content_version}</span>
        <span>奇门遁甲为传统象数决策参考，结果仅供文化自省，不构成医疗、法律、财务或人生重大决策建议。</span>
      </div>
    </div>
  );
}
