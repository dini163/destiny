import type { ReactNode } from 'react';

import type { DrawnCard } from '../../types/tarot';

interface CardEmblemProps {
  /** The drawn card whose suit/arcana decides the emblem. */
  card: DrawnCard;
  /** Stroke colour (the card's accent). */
  color: string;
  /** Extra wrapper classes (sizing). */
  className?: string;
}

/**
 * The central emblem of a card face: the suit pip for Minor Arcana, a radiant
 * celestial seal for Major Arcana.
 *
 * Drawn as inline SVG on the same 24px grid as the chrome icons so the deck is
 * fully self-contained — the mockup's external card photographs are not usable
 * offline, and no imagery is fabricated here.
 */
export function CardEmblem({ card, color, className }: CardEmblemProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      className={className}
      fill="none"
      stroke={color}
      strokeWidth={1.3}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {emblemFor(card)}
    </svg>
  );
}

function emblemFor(card: DrawnCard): ReactNode {
  if (card.arcana === 'major' || !card.suit) {
    return <MajorSeal />;
  }
  switch (card.suit) {
    case 'wands':
      return <Wands />;
    case 'cups':
      return <Cups />;
    case 'swords':
      return <Swords />;
    case 'pentacles':
      return <Pentacles />;
    default:
      return <MajorSeal />;
  }
}

/** Wands — a living staff with two leaves and a bud (fire / will). */
function Wands() {
  return (
    <>
      <path d="M12 21.5V7.5" />
      <circle cx="12" cy="5" r="1.7" />
      <path d="M12.4 11.5c0-2.6 1.7-4.3 4.3-4.3 0 2.6-1.7 4.3-4.3 4.3z" />
      <path d="M11.6 15c0-2.1-1.5-3.5-3.6-3.5 0 2.1 1.5 3.5 3.6 3.5z" />
    </>
  );
}

/** Cups — a chalice (water / emotion). */
function Cups() {
  return (
    <>
      <path d="M6.5 5h11l-1.1 5.4a4.5 4.5 0 0 1-8.8 0z" />
      <path d="M12 14.6V19" />
      <path d="M8.6 21h6.8" />
    </>
  );
}

/** Swords — a blade point-up (air / intellect). */
function Swords() {
  return (
    <>
      <path d="M12 2.5l1.7 2.1v8.7L12 15l-1.7-1.7V4.6z" />
      <path d="M7.6 14.6h8.8" />
      <path d="M12 15.2v4.6" />
      <path d="M10.2 21.4h3.6" />
    </>
  );
}

/** Pentacles — a five-pointed star within a disc (earth / material). */
function Pentacles() {
  return (
    <>
      <circle cx="12" cy="12" r="9.2" />
      <path d="M12 5.6l2 4.4 4.7.5-3.5 3.2 1 4.7-4.2-2.4-4.2 2.4 1-4.7-3.5-3.2 4.7-.5z" />
    </>
  );
}

/** Major Arcana — a radiant sun/celestial seal. */
function MajorSeal() {
  return (
    <>
      <circle cx="12" cy="12" r="8.8" strokeOpacity="0.45" />
      <circle cx="12" cy="12" r="3.6" />
      <path d="M12 1.6v2.6M12 19.8v2.6M1.6 12h2.6M19.8 12h2.6M4.9 4.9l1.9 1.9M17.2 17.2l1.9 1.9M19.1 4.9l-1.9 1.9M6.8 17.2l-1.9 1.9" />
    </>
  );
}
