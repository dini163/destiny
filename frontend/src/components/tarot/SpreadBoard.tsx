import type { DrawnCard } from '../../types/tarot';
import { TarotCard } from './TarotCard';

interface SpreadBoardProps {
  /** Cards in spread-position order. */
  cards: DrawnCard[];
  /** Position indices already turned face-up. */
  revealed: ReadonlySet<number>;
  /** Position index shown in the inspector, if any. */
  selected: number | null;
  /** Flip + select a card by position index. */
  onCardSelect: (index: number) => void;
}

/**
 * The card layout for any spread.
 *
 * A single centred flex-wrap grid adapts to every spread size (1, 3, 5 or 10
 * cards) without a per-layout special case, over a faint sacred-geometry
 * watermark echoing the oracle chamber. Flip and selection state live in the
 * page; the board only renders it. Until the reader turns a card, the lead
 * position plays a periodic flip nudge so the face-down backs read as cards to
 * open rather than artwork-less fronts.
 */
export function SpreadBoard({ cards, revealed, selected, onCardSelect }: SpreadBoardProps) {
  const showLeadHint = revealed.size === 0;

  return (
    <div className="relative">
      <div
        className="pointer-events-none absolute inset-0 flex items-center justify-center opacity-[0.05]"
        aria-hidden="true"
      >
        <svg viewBox="0 0 100 100" className="h-[420px] w-[420px] text-gold" fill="none" stroke="currentColor" strokeWidth={0.4}>
          <circle cx="50" cy="50" r="48" />
          <circle cx="50" cy="50" r="34" />
          <polygon points="50,4 90,74 10,74" />
          <polygon points="50,96 90,26 10,26" />
        </svg>
      </div>

      <div className="relative flex flex-wrap items-start justify-center gap-x-4 gap-y-7 py-2 sm:gap-x-7">
        {cards.map((card, index) => (
          <TarotCard
            key={card.position_index}
            card={card}
            revealed={revealed.has(card.position_index)}
            selected={selected === card.position_index}
            hint={index === 0 && showLeadHint}
            onSelect={() => onCardSelect(card.position_index)}
          />
        ))}
      </div>
    </div>
  );
}
