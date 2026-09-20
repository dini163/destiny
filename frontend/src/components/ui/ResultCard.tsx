import type { ReactNode } from 'react';

import { Icon } from './Icon';
import type { IconName } from './Icon';

interface ResultCardProps {
  /** Chinese headline. */
  title: string;
  /** Optional label-caps eyebrow above the title. */
  eyebrow?: string;
  /** Optional leading icon rendered in gold. */
  icon?: IconName;
  /** Optional right-aligned actions/meta in the header. */
  actions?: ReactNode;
  /** Card body. */
  children: ReactNode;
  /** Extra wrapper classes (e.g. grid spans). */
  className?: string;
  /** Render on the raised (Level 2) surface instead of the standard panel. */
  elevated?: boolean;
}

/**
 * The standard result surface: a gilded glass panel with an optional icon title,
 * eyebrow, right-aligned actions and a body separated by a burnished rule.
 *
 * Every chart section composes these so the observatory keeps one card language.
 */
export function ResultCard({
  title,
  eyebrow,
  icon,
  actions,
  children,
  className,
  elevated,
}: ResultCardProps) {
  return (
    <section
      className={`${elevated ? 'panel-raised' : 'panel'} flex flex-col gap-4 p-5 sm:p-6 ${className ?? ''}`}
    >
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          {icon ? <Icon name={icon} size={20} className="shrink-0 text-gold" /> : null}
          <div className="flex flex-col">
            {eyebrow ? <span className="label-caps">{eyebrow}</span> : null}
            <h2 className="font-display text-lg font-semibold text-ink sm:text-xl">{title}</h2>
          </div>
        </div>
        {actions ? <div className="flex flex-wrap items-center gap-3">{actions}</div> : null}
      </header>
      <div className="gold-rule" />
      {children}
    </section>
  );
}
