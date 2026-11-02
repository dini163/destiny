import { SourceNote } from '../ui/SourceNote';
import { pillarLabel } from '../../lib/pillars';
import type { GeJu } from '../../types/bazi';

/**
 * 格局 header card: which structure the month branch sets, and whether it
 * succeeded. `notes` are whole sentences from the corpus table (Task 6) — the
 * component joins nothing and adds nothing.
 */
export function GeJuCard({ geju }: { geju: GeJu }) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <span className="font-display text-2xl font-bold text-gold-bright">{geju.name}</span>
        <span
          className={
            geju.is_success
              ? 'label-caps rounded-element bg-wuxing-wood/15 px-2 py-0.5 text-wuxing-wood'
              : 'label-caps rounded-element bg-wuxing-fire/15 px-2 py-0.5 text-wuxing-fire'
          }
        >
          {geju.is_success ? '成格' : '不成格'}
        </span>
      </div>

      <p className="text-xs text-ink-muted" title={`from_pillar=${geju.from_pillar}`}>
        起于{pillarLabel(geju.from_pillar)}柱 · 取十神{geju.ten_god}
      </p>

      <ul className="flex flex-col gap-2">
        {geju.notes.map((note, index) => (
          <li
            key={`${geju.name}-${index}`}
            className="rounded-element border border-rim bg-[var(--field-bg)] p-2.5 text-sm leading-relaxed text-ink-variant"
          >
            {note}
          </li>
        ))}
      </ul>

      <span className="self-end">
        <SourceNote source={geju.source} />
      </span>
    </div>
  );
}
