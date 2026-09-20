import type { DrawnCard } from '../../types/tarot';
import { cardAccent, cardCornerLabel, orientationMeta, suitZh } from '../../lib/tarot';
import { CardEmblem } from './CardEmblem';

interface TarotCardProps {
  /** The drawn card occupying this position. */
  card: DrawnCard;
  /** Whether the card has been turned face-up. */
  revealed: boolean;
  /** Whether this card is the one shown in the inspector. */
  selected: boolean;
  /** Flip + select the card. */
  onSelect: () => void;
}

/**
 * A single spread position: a face-down card that flips to reveal its face.
 *
 * The whole card is a button (keyboard-focusable, `aria-pressed` tracks the
 * flip). The face is rendered purely from real deck fields — corner numeral,
 * suit emblem, bilingual name and orientation badge — with reversed cards shown
 * physically upside-down. No card artwork is fetched or fabricated.
 */
export function TarotCard({ card, revealed, selected, onSelect }: TarotCardProps) {
  const accent = cardAccent(card);
  const orientation = orientationMeta(card.orientation);
  const reversed = card.orientation === 'reversed';

  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={revealed}
      aria-label={`第 ${card.position_index + 1} 张 · ${card.position_label_zh}${revealed ? ` · ${card.name_zh} ${orientation.label}` : ' · 未翻开'}`}
      className="group flex w-[104px] shrink-0 flex-col items-center gap-2 focus:outline-none sm:w-[112px]"
    >
      <div className="[perspective:1200px]">
        <div
          className={`relative h-[164px] w-[104px] transition-transform duration-500 [transform-style:preserve-3d] sm:h-[176px] sm:w-[112px] ${
            revealed ? '[transform:rotateY(180deg)]' : ''
          }`}
        >
          <CardBack selected={selected} />
          <div className="absolute inset-0 [backface-visibility:hidden] [transform:rotateY(180deg)]">
            <div
              className={`flex h-full w-full flex-col rounded-card border p-2 transition-colors ${
                selected ? 'border-gold-strong' : 'border-rim group-hover:border-rim-strong'
              }`}
              style={{
                background: 'linear-gradient(160deg, #1b2130 0%, #12161f 55%, #0b0d13 100%)',
                boxShadow: selected
                  ? '0 0 0 1px rgba(212,175,55,0.45), 0 10px 28px -10px rgba(0,0,0,0.85)'
                  : '0 8px 22px -12px rgba(0,0,0,0.8)',
              }}
            >
              <div
                className={`flex h-full flex-col justify-between ${reversed ? 'rotate-180' : ''}`}
              >
                <div className="flex items-start justify-between gap-1">
                  <span className="numeric text-[13px] font-bold leading-none" style={{ color: accent }}>
                    {cardCornerLabel(card)}
                  </span>
                  <span
                    className="rounded-[3px] px-1 py-0.5 text-[9px] font-semibold leading-none"
                    style={{ color: orientation.color, backgroundColor: `${orientation.color}1f` }}
                  >
                    {orientation.label}
                  </span>
                </div>

                <div className="flex flex-col items-center gap-1">
                  <CardEmblem card={card} color={accent} className="h-11 w-11 opacity-90" />
                  {card.suit ? (
                    <span className="label-caps text-[8px]" style={{ color: accent }}>
                      {suitZh(card.suit)}
                    </span>
                  ) : (
                    <span className="label-caps text-[8px] text-gold-soft">大阿</span>
                  )}
                </div>

                <div className="flex flex-col gap-0.5">
                  <span className="truncate font-display text-[12px] font-semibold leading-tight text-ink">
                    {card.name_zh}
                  </span>
                  <span className="truncate text-[8px] uppercase leading-tight tracking-wide text-ink-muted">
                    {card.name}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <span className="flex flex-col items-center gap-0.5 text-center">
        <span className="label-caps text-[9px] text-gold-soft">
          {String(card.position_index + 1).padStart(2, '0')}
        </span>
        <span className="text-[11px] font-medium leading-tight text-ink-variant">
          {card.position_label_zh}
        </span>
      </span>
    </button>
  );
}

/** The ornate face-down back, shown before a card is flipped. */
function CardBack({ selected }: { selected: boolean }) {
  return (
    <div
      className={`absolute inset-0 flex items-center justify-center rounded-card border [backface-visibility:hidden] ${
        selected ? 'border-gold-strong' : 'border-rim'
      }`}
      style={{
        background:
          'repeating-linear-gradient(45deg, #141a28 0 6px, #10141f 6px 12px), radial-gradient(circle at 50% 50%, #1c2333, #0b0d13)',
        boxShadow: '0 8px 22px -12px rgba(0,0,0,0.8)',
      }}
    >
      <div className="flex h-[calc(100%-12px)] w-[calc(100%-12px)] items-center justify-center rounded-[5px] border border-gold/25">
        <svg
          viewBox="0 0 24 24"
          className="h-9 w-9 text-gold/70"
          fill="none"
          stroke="currentColor"
          strokeWidth={1}
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <circle cx="12" cy="12" r="8.6" strokeOpacity="0.5" />
          <path d="M12 3.4l2.1 5.3 5.5.4-4.2 3.6 1.3 5.4L12 15.4l-4.7 2.7 1.3-5.4-4.2-3.6 5.5-.4z" />
        </svg>
      </div>
    </div>
  );
}
