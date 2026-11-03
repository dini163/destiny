import { useI18n } from '../../i18n/context';
import { aspectStyle } from '../../lib/astro';
import { natureStyle } from '../../lib/transit';
import type { CrossAspect } from '../../types/transit';

interface CrossAspectListProps {
  /** The selected layer's moving-to-natal aspects, already tightest-first. */
  aspects: CrossAspect[];
  /** Shown when no aspect falls within the classical orbs. */
  emptyHint?: string;
}

/**
 * Cross-aspect list (移动层对本命的相位).
 *
 * Each row reads "moving body — aspect — natal point" with the exact orb and the
 * backend's standard nature chip. Colours are presentation only; the aspect type
 * and orb come straight from the geometric detection (PRD no-mock rule).
 */
export function CrossAspectList({ aspects, emptyHint }: CrossAspectListProps) {
  const { t } = useI18n();
  if (aspects.length === 0) {
    return (
      <p className="text-sm text-ink-muted">
        {t(emptyHint ?? '当前经典容许度内，未检出移动层星体对本命所成之主要相位。')}
      </p>
    );
  }
  return (
    <ul className="flex flex-col gap-1.5">
      {aspects.map((aspect, index) => {
        const asp = aspectStyle(aspect.type);
        const nat = natureStyle(aspect.nature);
        return (
          <li
            key={`${aspect.moving}-${aspect.type}-${aspect.natal}-${index}`}
            className="flex flex-wrap items-center gap-x-3 gap-y-1 rounded-element border border-rim-soft bg-surface/60 px-3 py-2"
          >
            <span className="flex w-[5.5rem] shrink-0 items-center gap-1.5">
              <span className="text-base leading-none" style={{ color: nat.color }}>
                {aspect.moving_glyph}
              </span>
              <span className="truncate text-sm text-ink">{aspect.moving_zh}</span>
            </span>
            <span
              className="flex shrink-0 items-center gap-1 rounded-full border px-2 py-0.5"
              style={{ borderColor: `${asp.color}66`, color: asp.color }}
            >
              <span className="text-sm leading-none">{aspect.glyph}</span>
              <span className="text-xs">{t(asp.label)}</span>
            </span>
            <span className="shrink-0 text-ink-muted" aria-hidden="true">
              →
            </span>
            <span className="w-[5.5rem] shrink-0 truncate text-sm text-ink-variant">{t('本命{{zh}}', { zh: aspect.natal_zh })}</span>
            <span className="ml-auto flex shrink-0 items-center gap-2">
              <span className="numeric text-xs text-ink-muted">{t('容 {{orb}}°', { orb: aspect.orb.toFixed(2) })}</span>
              <span
                className="rounded-full px-2 py-0.5 text-xs"
                style={{ backgroundColor: `${nat.color}22`, color: nat.color }}
              >
                {t(nat.label)}
              </span>
            </span>
          </li>
        );
      })}
    </ul>
  );
}
