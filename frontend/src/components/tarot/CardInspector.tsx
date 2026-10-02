import type { ReactNode } from 'react';

import type { DrawnCard } from '../../types/tarot';
import { arcanaZh, cardAccent, elementZh, orientationMeta, rankZh, suitZh } from '../../lib/tarot';
import { Icon } from '../ui/Icon';
import { CardEmblem } from './CardEmblem';

interface CardInspectorProps {
  /** The selected card, or null before the reader picks one. */
  card: DrawnCard | null;
}

/**
 * Focal-card detail panel.
 *
 * Renders only real deck fields for the selected position: bilingual name,
 * orientation, arcana/suit/rank/element, the position's meaning, the curated
 * keywords and the orientation-specific interpretation. The mockup's invented
 * "light/shadow", astrological correspondences and confidence indices are
 * deliberately omitted (PRD no-mock rule).
 */
export function CardInspector({ card }: CardInspectorProps) {
  if (!card) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-14 text-center">
        <span className="flex h-12 w-12 items-center justify-center rounded-card border border-rim bg-surface text-gold">
          <Icon name="sparkle" size={22} />
        </span>
        <p className="max-w-[16rem] text-sm leading-relaxed text-ink-muted">
          点选牌阵中的任意一张牌，此处将展开其正逆位牌义、关键词与宫位释义。
        </p>
      </div>
    );
  }

  const accent = cardAccent(card);
  const orientation = orientationMeta(card.orientation);

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-start gap-4">
        <span
          className="flex h-16 w-16 shrink-0 items-center justify-center rounded-card border"
          style={{ borderColor: `${accent}55`, backgroundColor: `${accent}12` }}
        >
          <CardEmblem card={card} color={accent} className="h-9 w-9" />
        </span>
        <div className="flex min-w-0 flex-col gap-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="label-caps">
              第 {String(card.position_index + 1).padStart(2, '0')} 张 · {card.position_label_zh}
            </span>
            <span
              className="rounded-[3px] px-1.5 py-0.5 text-[11px] font-semibold"
              style={{ color: orientation.color, backgroundColor: `${orientation.color}1f` }}
            >
              {orientation.label}
            </span>
          </div>
          <h3 className="font-display text-xl font-bold leading-tight text-ink">{card.name_zh}</h3>
          <span className="text-xs uppercase tracking-wide text-ink-muted">{card.name}</span>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <Chip>{arcanaZh(card.arcana)}</Chip>
        {card.suit ? <Chip accent={accent}>{suitZh(card.suit)}</Chip> : null}
        {card.rank ? <Chip accent={accent}>{rankZh(card.rank)}</Chip> : null}
        {card.element ? <Chip accent={accent}>{elementZh(card.element)} 元素</Chip> : null}
        <Chip>编号 {card.number}</Chip>
      </div>

      <div className="flex flex-col gap-3">
        <Block label={`宫位释义 · ${card.position_label_zh}`}>
          <p className="text-sm leading-relaxed text-ink-variant">{card.position_meaning_zh}</p>
          <p className="text-xs leading-relaxed text-ink-muted">{card.position_meaning}</p>
        </Block>

        <Block label="关键词 · KEYWORDS">
          <div className="flex flex-wrap gap-1.5">
            {card.keywords_zh.map((keyword) => (
              <span
                key={keyword}
                className="rounded-full border px-2.5 py-0.5 text-xs"
                style={{ borderColor: `${accent}40`, color: accent, backgroundColor: `${accent}0f` }}
              >
                {keyword}
              </span>
            ))}
          </div>
          <p className="text-xs text-ink-muted">{card.keywords.join(' · ')}</p>
        </Block>

        <Block label={`牌义 · ${orientation.label}`}>
          <p className="text-sm leading-relaxed text-ink-variant">{card.meaning_zh}</p>
          <p className="text-xs leading-relaxed text-ink-muted">{card.meaning}</p>
        </Block>
      </div>
    </div>
  );
}

/** A small metadata pill; `accent` tints it to the card's suit/major colour. */
function Chip({ children, accent }: { children: ReactNode; accent?: string }) {
  return (
    <span
      className="rounded-element border px-2 py-0.5 text-xs"
      style={
        accent
          ? { borderColor: `${accent}40`, color: accent, backgroundColor: `${accent}0f` }
          : undefined
      }
    >
      {children}
    </span>
  );
}

/** A captioned section within the inspector. */
function Block({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="label-caps">{label}</span>
      {children}
    </div>
  );
}
