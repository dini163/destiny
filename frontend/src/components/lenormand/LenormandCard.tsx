import type { DrawnCard } from '../../types/lenormand';
import { polarityAccent, polarityChip } from '../../lib/lenormand';
import { useI18n } from '../../i18n/context';

interface LenormandCardProps {
  /** The drawn card occupying this position. */
  card: DrawnCard;
  /** Compact rendering for the 36-card 大桌 (numeral + name only). */
  compact?: boolean;
  /** Whether this card is the one shown in the inspector. */
  selected: boolean;
  /** Select the card. */
  onSelect: () => void;
}

/**
 * A single Lenormand card face.
 *
 * Lenormand cards are never reversed, so there is no flip — the face is always up
 * and the whole card is a button that selects it for the inspector. The face is
 * rendered purely from real deck fields (numeral, bilingual name, polarity tint,
 * essence/keywords); no artwork is fetched or fabricated. The 指示牌 gets a gold ring.
 */
export function LenormandCard({ card, compact, selected, onSelect }: LenormandCardProps) {
  const { t } = useI18n();
  const accent = polarityAccent(card.polarity);
  const ring = card.is_significator || selected;

  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={selected}
      aria-label={`${t('第 {{n}} 位', { n: card.position_index + 1 })} · ${card.position_label_zh} · ${card.number} ${card.name_zh} ${card.polarity_label}`}
      className="group flex shrink-0 flex-col items-center gap-1 focus:outline-none"
    >
      <div
        className={`relative flex flex-col rounded-card border transition-colors ${
          compact ? 'h-[86px] w-[62px] p-1 sm:h-[96px] sm:w-[70px]' : 'h-[150px] w-[100px] p-2 sm:h-[164px] sm:w-[110px]'
        } ${card.is_significator ? 'border-gold-strong' : selected ? 'border-gold-strong' : 'border-rim group-hover:border-rim-strong'}`}
        style={{
          background: 'linear-gradient(160deg, #1b2130 0%, #12161f 55%, #0b0d13 100%)',
          boxShadow: ring
            ? '0 0 0 1px rgba(212,175,55,0.45), 0 10px 28px -10px rgba(0,0,0,0.85)'
            : '0 8px 22px -12px rgba(0,0,0,0.8)',
        }}
      >
        <div className="flex items-start justify-between gap-1">
          <span className={`numeric leading-none ${compact ? 'text-[11px]' : 'text-[13px]'} font-bold`} style={{ color: accent }}>
            {String(card.number).padStart(2, '0')}
          </span>
          {compact ? (
            <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: accent }} />
          ) : (
            <span className={`rounded-[3px] px-1 py-0.5 text-[8px] font-semibold leading-none ${polarityChip(card.polarity)}`}>
              {card.polarity_label}
            </span>
          )}
        </div>

        <div className={`flex flex-1 flex-col items-center justify-center gap-0.5 text-center ${compact ? '' : 'gap-1'}`}>
          {compact ? (
            <span className="font-display text-[13px] font-semibold leading-tight text-[#ede9dd]">{card.name_zh}</span>
          ) : (
            <>
              <CardEmblem color={accent} />
              <span className="font-display text-[15px] font-semibold leading-tight text-[#ede9dd]">{card.name_zh}</span>
              <span className="text-[8px] uppercase leading-tight tracking-wide text-[#adb6a6]">{card.name}</span>
            </>
          )}
        </div>

        {compact ? null : (
          <div className="flex flex-col items-center gap-0.5">
            <span className="font-display text-[10px] leading-tight text-gold-soft">{card.essence}</span>
            <span className="line-clamp-1 text-[8px] leading-tight text-[#adb6a6]">{card.keywords.join(' · ')}</span>
          </div>
        )}

        {card.is_significator ? (
          <span className="absolute -top-1.5 -right-1.5 rounded-full bg-gold px-1 text-[8px] font-bold leading-tight text-void">
            {t('指示')}
          </span>
        ) : null}
      </div>

      <span className="flex flex-col items-center gap-0.5 text-center">
        <span className="label-caps text-[9px] text-gold-soft">
          {String(card.position_index + 1).padStart(2, '0')}
        </span>
        {compact ? null : (
          <span className="text-[11px] font-medium leading-tight text-ink-variant">{card.position_label_zh}</span>
        )}
      </span>
    </button>
  );
}

/** A small ornamental star emblem standing in for the card artwork. */
function CardEmblem({ color }: { color: string }) {
  return (
    <svg viewBox="0 0 24 24" className="h-9 w-9 opacity-80" fill="none" stroke={color} strokeWidth={1} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="8.4" strokeOpacity="0.45" />
      <path d="M12 4.2l1.9 4.9 4.9 1.9-4.9 1.9L12 17.8l-1.9-4.9L5.2 11l4.9-1.9z" />
    </svg>
  );
}
