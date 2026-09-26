import type { CSSProperties } from 'react';

import type { DrawnCard, LenormandLayout } from '../../types/lenormand';
import { LenormandCard } from './LenormandCard';

interface LenormandBoardProps {
  /** Cards in spread-position order. */
  cards: DrawnCard[];
  /** Layout family: line (flex row), box (3×3), tableau (8×4 + row of 4). */
  layout: LenormandLayout;
  /** Position index shown in the inspector, if any. */
  selected: number | null;
  /** Select a card by position index. */
  onCardSelect: (index: number) => void;
}

/**
 * The card layout for any Lenormand spread.
 *
 * A line renders as a centred flex row; the box and the 大桌 render as CSS grids with
 * each card placed by its own row/col (so the traditional 8×4 + 4 shape holds). The
 * 大桌 uses compact cards so all 36 fit; every card is face-up (Lenormand never
 * reverses) and selectable for the inspector.
 */
export function LenormandBoard({ cards, layout, selected, onCardSelect }: LenormandBoardProps) {
  const compact = layout === 'tableau';

  if (layout === 'line') {
    return (
      <div className="flex flex-wrap items-start justify-center gap-x-4 gap-y-6 py-2 sm:gap-x-6">
        {cards.map((card) => (
          <LenormandCard
            key={card.position_index}
            card={card}
            selected={selected === card.position_index}
            onSelect={() => onCardSelect(card.position_index)}
          />
        ))}
      </div>
    );
  }

  const columns = layout === 'tableau' ? 8 : 3;
  return (
    <div className="overflow-x-auto pb-1">
      <div
        className="mx-auto grid gap-x-2 gap-y-4 sm:gap-x-3"
        style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}
      >
        {cards.map((card) => (
          <div key={card.position_index} style={gridCell(card.row, card.col)} className="flex justify-center">
            <LenormandCard
              card={card}
              compact={compact}
              selected={selected === card.position_index}
              onSelect={() => onCardSelect(card.position_index)}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

/** Explicit grid placement from a card's 0-based row/col. */
function gridCell(row: number, col: number): CSSProperties {
  return { gridRowStart: row + 1, gridColumnStart: col + 1 };
}
