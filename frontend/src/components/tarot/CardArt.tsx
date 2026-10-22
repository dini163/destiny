import { useState, type ReactNode } from 'react';

import type { DrawnCard, TarotRank, TarotSuit } from '../../types/tarot';
import { cardAccent } from '../../lib/tarot';
import { MAJOR_ART, type ArtNode } from './arcanaArt';

interface CardArtProps {
  /** The card whose face artwork is rendered. */
  card: DrawnCard;
  /** Extra wrapper classes (sizing/positioning). */
  className?: string;
}

/**
 * The full card-face artwork.
 *
 * Artwork is now bitmap-first: each card_id maps to a generated illustration at
 * `/cards/tarot/<card_id>.jpg` (78 images, one per card, drawn in a unified
 * mystic-oil style and family-safe). While the image is missing or fails to
 * load, the card falls back to the deterministic vector artwork below, so a
 * broken asset never blanks a face. Reversal is handled by the parent (the face
 * container rotates 180°), so neither branch needs its own orientation logic.
 */
export function CardArt({ card, className }: CardArtProps) {
  const [useBitmap, setUseBitmap] = useState(true);
  if (!useBitmap) {
    return <CardArtSvg card={card} className={className} />;
  }
  return (
    <img
      src={`/cards/tarot/${card.card_id}.jpg`}
      alt=""
      aria-hidden="true"
      draggable={false}
      loading="lazy"
      className={`h-full w-full object-cover ${className ?? ''}`}
      onError={() => setUseBitmap(false)}
    />
  );
}

/** Vector fallback: gold/suit strokes that read as a real tarot print. */
function CardArtSvg({ card, className }: CardArtProps) {
  const accent = cardAccent(card);
  return (
    <svg
      viewBox="0 0 100 150"
      className={className}
      fill="none"
      stroke={accent}
      strokeWidth={1.3}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {/* 图案区底层光晕，让线条浮在深空之上 */}
      <circle cx="50" cy="80" r="46" fill={accent} opacity="0.05" stroke="none" />
      {shapesFor(card).map((node, index) => (
        <Shape key={index} node={node} />
      ))}
    </svg>
  );
}

/** Render one artwork node (path / circle / line). */
function Shape({ node }: { node: ArtNode }) {
  const opacity = node.o ?? 0.92;
  if (node.d) {
    return <path d={node.d} strokeOpacity={opacity} />;
  }
  if (node.cx != null && node.cy != null && node.r != null) {
    return <circle cx={node.cx} cy={node.cy} r={node.r} strokeOpacity={opacity} />;
  }
  return <line x1={node.x1} y1={node.y1} x2={node.x2} y2={node.y2} strokeOpacity={opacity} />;
}

/** Choose the artwork for a drawn card. */
function shapesFor(card: DrawnCard): ArtNode[] {
  if (card.arcana === 'major') {
    return MAJOR_ART[card.number] ?? [];
  }
  if (card.rank) {
    return courtShapes(card.rank, card.suit ?? 'wands');
  }
  const count = Math.min(Math.max(card.number, 1), 10);
  return pipShapes(card.suit ?? 'wands', count);
}

// --- Minor arcana ----------------------------------------------------------

/** Pip positions for counts 1–10, balanced on the 100×150 grid. */
const PIP_LAYOUT: Record<number, Array<[number, number]>> = {
  1: [[50, 82]],
  2: [
    [36, 68],
    [64, 96],
  ],
  3: [
    [50, 62],
    [33, 92],
    [67, 92],
  ],
  4: [
    [36, 64],
    [64, 64],
    [36, 96],
    [64, 96],
  ],
  5: [
    [36, 62],
    [64, 62],
    [50, 80],
    [36, 98],
    [64, 98],
  ],
  6: [
    [33, 60],
    [67, 60],
    [33, 82],
    [67, 82],
    [33, 104],
    [67, 104],
  ],
  7: [
    [32, 56],
    [50, 62],
    [68, 56],
    [32, 84],
    [68, 84],
    [42, 106],
    [58, 106],
  ],
  8: [
    [35, 54],
    [65, 54],
    [35, 74],
    [65, 74],
    [50, 64],
    [35, 94],
    [65, 94],
    [50, 104],
  ],
  9: [
    [35, 50],
    [65, 50],
    [35, 70],
    [65, 70],
    [35, 90],
    [65, 90],
    [50, 60],
    [50, 80],
    [50, 104],
  ],
  10: [
    [35, 50],
    [65, 50],
    [35, 70],
    [65, 70],
    [35, 90],
    [65, 90],
    [50, 60],
    [50, 80],
    [42, 108],
    [58, 108],
  ],
};

/** A single suit pip drawn around its anchor point (x, y). */
function pipShapes(suit: TarotSuit, count: number): ArtNode[] {
  return PIP_LAYOUT[count].flatMap(([x, y]) => pipAt(suit, x, y));
}

function pipAt(suit: TarotSuit, x: number, y: number): ArtNode[] {
  switch (suit) {
    case 'wands':
      return [
        { d: `M${x} ${y - 7} V${y + 7}` },
        { cx: x, cy: y - 7, r: 2 },
        { d: `M${x + 1} ${y - 2} q4 -3 6 0 q-4 3 -6 0`, o: 0.8 },
      ];
    case 'cups':
      return [
        { d: `M${x - 4} ${y - 6} h8 l-1.2 5.4 a3.6 3.6 0 0 1 -5.6 0 z` },
        { d: `M${x} ${y + 1.5} V${y + 4.5}` },
        { d: `M${x - 3} ${y + 7} h6`, o: 0.85 },
      ];
    case 'swords':
      return [
        { d: `M${x} ${y - 8} l1.5 2.1 v5 L${x} ${y + 0.4} l-1.5 -1.3 v-5 z` },
        { d: `M${x - 2.4} ${y + 2} h4.8`, o: 0.85 },
        { d: `M${x} ${y + 3.6} v3.4`, o: 0.85 },
        { cx: x, cy: y + 8, r: 1.2, o: 0.9 },
      ];
    case 'pentacles':
      return [
        { cx: x, cy: y, r: 7 },
        { d: `M${x} ${y - 3.8} l1.6 3.4 3.6 0.5 -2.6 2.5 0.8 3.6 -3.4 -1.9 -3.4 1.9 0.8 -3.6 -2.6 -2.5 3.6 -0.5 z`, o: 0.95 },
      ];
  }
}

/** Court cards: a simplified figure holding the suit's sign of office. */
function courtShapes(rank: TarotRank, suit: TarotSuit): ArtNode[] {
  switch (rank) {
    case 'Page':
      return [
        { cx: 50, cy: 58, r: 5, o: 0.95 },
        { d: 'M36 84 q14 -10 28 0 l2 16 h-32 z', o: 0.9 },
        ...pipAt(suit, 50, 108),
      ];
    case 'Knight':
      return [
        { d: 'M28 106 q4 -22 24 -22', o: 0.9 },
        { cx: 52, cy: 82, r: 5, o: 0.9 },
        { d: 'M52 82 V72 M48 76 l8 -8', o: 0.8 },
        { cx: 50, cy: 66, r: 4, o: 0.95 },
        { d: 'M50 70 V54', o: 0.85 },
      ];
    case 'Queen':
      return [
        { d: 'M40 42 l3 -6 h14 l3 6 z M44 36 v-3 M50 36 v-4 M56 36 v-3', o: 0.9 },
        { d: 'M30 112 h40 v-20 h-40 z M34 92 h32', o: 0.85 },
        { d: 'M50 68 v14 M44 74 h12', o: 0.8 },
        { cx: 50, cy: 66, r: 2.4, o: 0.95 },
        ...pipAt(suit, 50, 112),
      ];
    case 'King':
      return [
        { d: 'M40 42 l3 -6 h14 l3 6 z M44 36 v-3 M50 36 v-4 M56 36 v-3', o: 0.9 },
        { d: 'M30 114 h40 v-22 h-40 z M34 92 h32', o: 0.85 },
        { d: 'M62 84 V112', o: 0.9 },
        { cx: 62, cy: 80, r: 2.4, o: 0.95 },
        ...pipAt(suit, 50, 116),
      ];
  }
}
