import { useState } from 'react';

import { useI18n } from '../i18n/context';
import { CombinationLens } from '../components/lenormand/CombinationLens';
import { LenormandBoard } from '../components/lenormand/LenormandBoard';
import { LenormandCard } from '../components/lenormand/LenormandCard';
import { LenormandControls } from '../components/lenormand/LenormandControls';
import { Icon } from '../components/ui/Icon';
import { ResultCard } from '../components/ui/ResultCard';
import { VerdictCard } from '../components/ui/VerdictCard';
import { useLenormand } from '../hooks/useLenormand';
import { polarityChip, significatorRequestValue } from '../lib/lenormand';
import type { DrawnCard, LenormandReading, LenormandRequest, SignificatorChoice } from '../types/lenormand';

/**
 * 雷诺曼神谕 divination page (Lenormand).
 *
 * The console draws a real spread via `useLenormand`; the page then renders the card
 * layout (line / box / 大桌), a 组合直读透镜, a selected-card inspector and a synthesis —
 * every value taken straight from the engine (PRD no-mock rule). Cards are always
 * upright (Lenormand never reverses) and clickable to inspect their full meaning.
 */
export function LenormandPage() {
  const { t } = useI18n();
  const [spread, setSpread] = useState('three_card');
  const [significator, setSignificator] = useState<SignificatorChoice>('none');
  const [question, setQuestion] = useState('');
  const [selected, setSelected] = useState<number | null>(null);
  const lenormand = useLenormand();

  function handleDraw(): void {
    const trimmed = question.trim();
    const request: LenormandRequest = {
      spread_id: spread,
      question: trimmed === '' ? undefined : trimmed,
      significator: significatorRequestValue(significator),
    };
    setSelected(null);
    lenormand.mutate(request);
  }

  return (
    <div className="mx-auto flex w-full max-w-[1536px] flex-col gap-6 px-gutter py-8">
      <LenormandControls
        spread={spread}
        onSpreadChange={setSpread}
        significator={significator}
        onSignificatorChange={setSignificator}
        question={question}
        onQuestionChange={setQuestion}
        pending={lenormand.isPending}
        onSubmit={handleDraw}
      />

      {lenormand.error ? (
        <div className="flex items-start gap-2 rounded-element border border-wuxing-fire/40 bg-wuxing-fire/10 px-4 py-3 text-sm text-ink">
          <Icon name="alert" size={18} className="mt-0.5 shrink-0 text-wuxing-fire" />
          <span>{lenormand.error.message}</span>
        </div>
      ) : null}

      {lenormand.isPending && !lenormand.data ? (
        <p className="label-caps text-ink-muted">{t('正在洗牌抽牌，铺陈牌阵…')}</p>
      ) : null}

      {lenormand.data ? (
        <LenormandResults reading={lenormand.data} selected={selected} onSelect={setSelected} />
      ) : null}
    </div>
  );
}

/** The full reading composition, rendered once a real draw is available. */
function LenormandResults({
  reading,
  selected,
  onSelect,
}: {
  reading: LenormandReading;
  selected: number | null;
  onSelect: (index: number | null) => void;
}) {
  const { t } = useI18n();
  const cards = reading.cards;
  const sigIndex = cards.findIndex((card) => card.is_significator);
  const activeIndex = selected ?? (sigIndex >= 0 ? sigIndex : 0);
  const activeCard = cards[activeIndex] ?? null;

  return (
    <>
      <ResultCard
        title="牌阵布局"
        eyebrow={`${reading.spread_name_en} · ${cards.length} ${t('张')}`}
        icon="vault"
        elevated
        actions={
          <span className="label-caps rounded-element bg-gold/15 px-2 py-1 text-gold">
            {reading.spread_name_zh}
          </span>
        }
      >
        {reading.question ? (
          <p className="text-sm leading-relaxed text-ink-variant">
            <span className="label-caps mr-2 align-middle">{t('所问之事')}</span>
            {reading.question}
          </p>
        ) : null}
        <LenormandBoard
          cards={cards}
          layout={reading.layout}
          selected={activeIndex}
          onCardSelect={(index) => onSelect(index)}
        />
        <p className="text-xs text-ink-muted">{reading.description}</p>
      </ResultCard>

      <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-12">
        <div className="lg:col-span-7">
          <ResultCard title="组合直读透镜" icon="compass">
            <CombinationLens reading={reading} />
          </ResultCard>
        </div>
        <div className="lg:col-span-5">
          <ResultCard title="牌义详解" icon="search" className="lg:sticky lg:top-32">
            {activeCard ? (
              <CardInspector card={activeCard} onDeselect={() => onSelect(null)} />
            ) : (
              <p className="text-sm text-ink-muted">{t('点击牌阵中任意一张牌，查看其完整牌义。')}</p>
            )}
          </ResultCard>
        </div>
      </div>

      <VerdictCard verdict={reading.verdict} />

      <ResultCard title="综合判读" icon="sparkle">
        <p className="font-display text-sm leading-relaxed text-ink-variant sm:text-base">{reading.synthesis}</p>
      </ResultCard>
    </>
  );
}

/** The full detail of the selected card, all fields straight from the response. */
function CardInspector({ card, onDeselect }: { card: DrawnCard; onDeselect: () => void }) {
  const { t } = useI18n();
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-start gap-3">
        <LenormandCard card={card} selected onSelect={onDeselect} />
        <div className="flex flex-col gap-1">
          <span className="label-caps text-gold-soft">
            {t('第 {{n}} 位 ·', { n: card.position_index + 1 })} {card.position_label_zh}
          </span>
          <span className="font-display text-xl font-semibold text-ink">
            {String(card.number).padStart(2, '0')} {card.name_zh}
          </span>
          <span className="text-xs uppercase tracking-wide text-ink-muted">{card.name}</span>
          <span className={`mt-1 w-fit rounded-element px-2 py-0.5 text-xs font-semibold ${polarityChip(card.polarity)}`}>
            {card.polarity_label}
          </span>
        </div>
      </div>

      <p className="text-sm leading-relaxed text-ink-muted">{card.position_meaning}</p>

      <div className="gold-rule" />

      <div className="flex flex-wrap gap-1.5">
        {card.keywords.map((keyword) => (
          <span key={keyword} className="rounded-element border border-rim-soft bg-surface px-2 py-0.5 text-xs text-ink-variant">
            {keyword}
          </span>
        ))}
      </div>

      <div className="flex flex-col gap-1.5 rounded-element border border-rim-soft bg-surface/50 px-3 py-2.5">
        <span className="label-caps text-ink-muted">{t('核心牌义')}</span>
        <p className="font-display text-sm leading-relaxed text-ink-variant">{card.meaning}</p>
      </div>

      <p className="text-xs leading-relaxed text-ink-muted">
        {t('名词核心：')}<span className="text-gold-soft">{card.essence}</span>
        {t('；作后牌修饰前牌时：')}<span className="text-gold-soft">{card.as_modifier}</span>。
      </p>
    </div>
  );
}
