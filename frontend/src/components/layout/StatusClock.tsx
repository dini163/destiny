import { useNow } from '../../hooks/useNow';

/**
 * Live observatory telemetry leaves for the App Shell status bar.
 *
 * Both read the REAL client clock via `useNow` — no fabricated GPS or True-Solar-
 * Time offsets (per-chart TST is computed by the backend and shown on result
 * pages). They are separate tiny leaves so the 1s tick re-renders only the badge,
 * never the whole header.
 */

/** Row-1 pill: pulsing beacon + live UTC wall clock. */
export function UtcClock() {
  const now = useNow(1000);
  const hhmmss = now.toISOString().slice(11, 19);
  return (
    <div className="numeric hidden items-center gap-2 rounded-element border border-rim bg-surface/60 px-3 py-1.5 md:flex">
      <span className="relative flex h-1.5 w-1.5">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-gold opacity-70" />
        <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-gold-bright" />
      </span>
      <span className="label-caps">UTC</span>
      <span className="text-sm text-gold-soft">{hhmmss}</span>
    </div>
  );
}

/** Row-2 badge: the J2000 astronomical epoch with the live decimal year. */
export function EpochBadge() {
  const now = useNow(30_000);
  const decimalYear = toDecimalYear(now).toFixed(2);
  return (
    <div className="numeric hidden shrink-0 items-center gap-2 lg:flex">
      <span className="label-caps text-gold">EPOCH</span>
      <span className="text-sm text-ink-variant">{decimalYear}</span>
      <span className="label-caps">J2000</span>
    </div>
  );
}

/** Astronomical decimal year (e.g. 2025.26) — a real epoch coordinate. */
function toDecimalYear(date: Date): number {
  const year = date.getUTCFullYear();
  const start = Date.UTC(year, 0, 1);
  const end = Date.UTC(year + 1, 0, 1);
  return year + (date.getTime() - start) / (end - start);
}
