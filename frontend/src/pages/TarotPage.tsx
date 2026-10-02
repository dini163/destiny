import { useEffect, useMemo, useState } from 'react';

import { CardInspector } from '../components/tarot/CardInspector';
import { SpreadBoard } from '../components/tarot/SpreadBoard';
import { SpreadControls } from '../components/tarot/SpreadControls';
import { SpreadSummary } from '../components/tarot/SpreadSummary';
import { Icon } from '../components/ui/Icon';
import { ProvenancePanel } from '../components/ui/ProvenancePanel';
import { ResultCard } from '../components/ui/ResultCard';
import { useTarotSpread } from '../hooks/useTarotSpread';
import type { DrawnCard, TarotSpreadRequest, TarotSpreadResponse } from '../types/tarot';

/**
 * Tarot oracle page (塔罗神谕).
 *
 * The console deals a real spread via `useTarotSpread`; the page then owns the
 * reading interaction — which positions are flipped face-up and which card the
 * inspector focalises. Every card face, keyword, meaning, position gloss and the
 * synthesis come straight from the backend's curated deck and CSPRNG draw, so the
 * mockup's invented inspector copy, confidence indices and action directives are
 * omitted (PRD no-mock rule).
 */
export function TarotPage() {
  const [spreadId, setSpreadId] = useState('celtic_cross');
  const [question, setQuestion] = useState('');
  const [allowReversed, setAllowReversed] = useState(true);
  const [revealed, setRevealed] = useState<ReadonlySet<number>>(() => new Set());
  const [selected, setSelected] = useState<number | null>(null);
  const tarot = useTarotSpread();

  // Each successful draw is a fresh shuffle: reset flips + selection so the new
  // spread starts face-down. `data` changes identity only when a result lands.
  useEffect(() => {
    setRevealed(new Set());
    setSelected(null);
  }, [tarot.data]);

  function handleDraw(): void {
    const trimmed = question.trim();
    const request: TarotSpreadRequest = {
      spread_id: spreadId,
      allow_reversed: allowReversed,
      question: trimmed === '' ? undefined : trimmed,
    };
    tarot.mutate(request);
  }

  /** Flip a card face-up (idempotent) and focalise it in the inspector. */
  function handleCardSelect(index: number): void {
    setSelected(index);
    setRevealed((prev) => {
      if (prev.has(index)) {
        return prev;
      }
      const next = new Set(prev);
      next.add(index);
      return next;
    });
  }

  function handleRevealAll(): void {
    if (!tarot.data) {
      return;
    }
    setRevealed(new Set(tarot.data.cards.map((card) => card.position_index)));
  }

  const selectedCard = useMemo<DrawnCard | null>(
    () =>
      tarot.data && selected != null
        ? tarot.data.cards.find((card) => card.position_index === selected) ?? null
        : null,
    [tarot.data, selected],
  );

  const allRevealed = tarot.data != null && revealed.size >= tarot.data.cards.length;

  return (
    <div className="mx-auto flex w-full max-w-[1536px] flex-col gap-6 px-gutter py-8">
      <SpreadControls
        spreadId={spreadId}
        onSpreadChange={setSpreadId}
        question={question}
        onQuestionChange={setQuestion}
        allowReversed={allowReversed}
        onAllowReversedChange={setAllowReversed}
        pending={tarot.isPending}
        onSubmit={handleDraw}
      />

      {tarot.error ? (
        <div className="flex items-start gap-2 rounded-element border border-wuxing-fire/40 bg-wuxing-fire/10 px-4 py-3 text-sm text-ink">
          <Icon name="alert" size={18} className="mt-0.5 shrink-0 text-wuxing-fire" />
          <span>{tarot.error.message}</span>
        </div>
      ) : null}

      {tarot.isPending && !tarot.data ? (
        <p className="label-caps text-ink-muted">正在以 CSPRNG 洗牌布阵…</p>
      ) : null}

      {tarot.data ? (
        <TarotResults
          spread={tarot.data}
          revealed={revealed}
          selected={selected}
          selectedCard={selectedCard}
          allRevealed={allRevealed}
          onCardSelect={handleCardSelect}
          onRevealAll={handleRevealAll}
        />
      ) : null}
    </div>
  );
}

interface TarotResultsProps {
  spread: TarotSpreadResponse;
  revealed: ReadonlySet<number>;
  selected: number | null;
  selectedCard: DrawnCard | null;
  allRevealed: boolean;
  onCardSelect: (index: number) => void;
  onRevealAll: () => void;
}

/** The full reading composition, rendered once a real draw is available. */
function TarotResults({
  spread,
  revealed,
  selected,
  selectedCard,
  allRevealed,
  onCardSelect,
  onRevealAll,
}: TarotResultsProps) {
  return (
    <>
      <SpreadSummary spread={spread} />

      <div className="grid grid-cols-1 items-start gap-6 xl:grid-cols-12">
        <div className="xl:col-span-8">
          <ResultCard
            title="牌阵盘面"
            eyebrow="SPREAD BOARD"
            icon="vault"
            elevated
            actions={
              <button
                type="button"
                onClick={onRevealAll}
                disabled={allRevealed}
                className="btn-ghost px-3 py-1.5 text-xs disabled:cursor-default disabled:opacity-40"
              >
                <Icon name="sparkle" size={14} />
                {allRevealed ? '已全部翻开' : '翻开全部'}
              </button>
            }
          >
            <SpreadBoard
              cards={spread.cards}
              revealed={revealed}
              selected={selected}
              onCardSelect={onCardSelect}
            />
            <p className="mt-1 text-center text-xs text-ink-muted">
              点选任意牌张即可翻开并展开详解；逆位牌以颠倒方向呈现。
            </p>
          </ResultCard>
        </div>

        <div className="xl:col-span-4">
          <ResultCard
            title="牌义详解"
            eyebrow="CARD INSPECTOR"
            icon="sparkle"
            elevated
            className="xl:sticky xl:top-32"
          >
            <CardInspector card={selectedCard} />
          </ResultCard>
        </div>
      </div>

      <ResultCard title="综合解读" eyebrow="SYNTHESIS" icon="seal" elevated>
        <p className="whitespace-pre-line text-sm leading-relaxed text-ink-variant">{spread.synthesis}</p>
      </ResultCard>

      <Provenance spread={spread} />
    </>
  );
}

/** Methodology + provenance note anchored to the real draw engine. */
function Provenance({ spread }: { spread: TarotSpreadResponse }) {
  return (
    <div className="panel flex flex-col gap-3 p-5">
      <div className="flex items-start gap-3">
        <Icon name="seal" size={22} className="mt-0.5 shrink-0 text-gold" />
        <div className="flex flex-col gap-1">
          <span className="font-display text-base text-ink">洗牌溯源与免责</span>
          <p className="max-w-3xl text-sm leading-relaxed text-ink-muted">
            本次<span className="text-gold-soft"> {spread.spread_name_zh} </span>由{' '}
            <span className="text-gold-soft">{spread.rng}</span> 加密安全乱数抽牌（不放回，牌张互不重复），
            牌名、关键词与牌义取自 <span className="text-gold-soft">{spread.engine}</span> 策展 78 张牌库，综合解读由引擎的固定句式串起这些真实字段。
            塔罗为象征性自省工具，结果仅供娱乐与文化参考，不构成医疗、法律、财务或人生重大决策建议。
          </p>
        </div>
      </div>
      <ProvenancePanel tables={spread.provenance.tables} />
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-ink-muted">
        <span className="label-caps">ENGINE · {spread.provenance.engine}</span>
        <span className="label-caps">RNG · {spread.rng}</span>
      </div>
    </div>
  );
}
