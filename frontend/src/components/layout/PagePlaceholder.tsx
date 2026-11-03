import type { ReactNode } from 'react';

interface PagePlaceholderProps {
  /** Chinese display title. */
  title: string;
  /** One-line description of the destination. */
  summary: string;
  /** Small status line (e.g. the implementation step) beneath the rule. */
  status: string;
  /** Optional call-to-action slot. */
  action?: ReactNode;
}

/**
 * Scaffold stand-in for a routed page.
 *
 * Establishes the route + shell wiring in Step 9; each system page replaces its
 * placeholder with the real chart surface in Steps 11–15 (the 404 page keeps it).
 */
export function PagePlaceholder({
  title,
  summary,
  status,
  action,
}: PagePlaceholderProps) {
  return (
    <section className="mx-auto flex max-w-[1536px] flex-col items-center px-gutter py-margin">
      <div className="panel-raised w-full max-w-2xl px-8 py-14 text-center sm:px-12">
        <h1 className="font-display text-4xl font-semibold text-gold-bright text-glow-gold">
          {title}
        </h1>
        <div className="gold-rule mx-auto my-7 w-40" />
        <p className="text-base leading-relaxed text-ink-variant">{summary}</p>
        {action ? <div className="mt-8 flex justify-center">{action}</div> : null}
        <p className="label-caps mt-9">{status}</p>
      </div>
    </section>
  );
}
