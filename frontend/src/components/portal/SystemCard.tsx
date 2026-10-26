import type { CSSProperties } from 'react';
import { Link } from 'react-router-dom';

import type { PortalSystem } from '../../lib/portal';
import { Icon } from '../ui/Icon';

interface SystemCardProps {
  system: PortalSystem;
  /** Position in the grid, used only to stagger the one-shot enter animation. */
  index?: number;
}

/**
 * One tile of the entry matrix.
 *
 * A live system renders as a `<Link>` to its real route with a call to action; an
 * unbuilt system renders as an inert panel. The blurb and highlight tags are
 * curated descriptions of the discipline — never a fabricated result.
 */
export function SystemCard({ system, index = 0 }: SystemCardProps) {
  const live = system.route !== null;
  const enterStyle = { '--card-delay': `${Math.min(index, 12) * 45}ms` } as CSSProperties;

  const content = (
    <>
      <span
        className={`flex shrink-0 items-center justify-center rounded-card border ${
          live
            ? 'h-12 w-12 border-rim bg-gold/10 text-gold'
            : 'h-10 w-10 border-rim-soft bg-surface text-ink-muted'
        }`}
      >
        <Icon name={system.icon} size={live ? 26 : 22} />
      </span>

      <div className="flex flex-col gap-1.5">
        <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
          <h3
            className={`whitespace-nowrap font-display text-lg font-semibold ${live ? 'text-ink group-hover:text-gold-bright' : 'text-ink-variant'}`}
          >
            {system.nameZh}
          </h3>
          <span className="label-caps">{system.nameEn}</span>
        </div>
        <p className="line-clamp-2 text-xs leading-relaxed text-ink-muted">{system.blurb}</p>
      </div>

      <div className="flex items-center justify-between gap-2 border-t border-rim-soft pt-3">
        <div className="flex flex-wrap items-center gap-1.5">
          {system.highlights.map((tag) => (
            <span
              key={tag}
              className="numeric rounded-element bg-surface px-1.5 py-0.5 text-[11px] text-ink-variant"
            >
              {tag}
            </span>
          ))}
        </div>
        {live ? (
          <span className="label-caps flex shrink-0 items-center gap-1 text-gold">
            {system.cta}
            <Icon name="arrowRight" size={14} />
          </span>
        ) : null}
      </div>
    </>
  );

  const base = 'portal-card group flex flex-col justify-between gap-4 rounded-card border p-5';

  if (system.route !== null) {
    return (
      <Link
        to={system.route}
        style={enterStyle}
        className={`${base} portal-card-enter panel-raised border-rim hover:border-gold-strong`}
      >
        {content}
      </Link>
    );
  }

  return (
    <div style={enterStyle} className={`${base} portal-card-enter panel border-rim-soft`}>
      {content}
    </div>
  );
}
