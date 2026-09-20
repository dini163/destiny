interface LineBarProps {
  /** True for a solid yang line (⚊), false for a broken yin line (⚋). */
  yang: boolean;
  /** Tailwind background class for the bar segments (kept literal for the scanner). */
  barClass?: string;
  /** Add a gold glow behind the bar — used for moving lines. */
  glow?: boolean;
  /** Moving-line marker (○ old yang / × old yin) reserved at the right end. */
  mark?: string | null;
  /** Extra wrapper classes (width, alignment). */
  className?: string;
}

/**
 * A single yao (爻) drawn as a bar: yang is one unbroken segment, yin is two
 * segments split by a central gap. The moving-line marker (○/×) always reserves
 * a fixed slot on the right so a column of bars stays aligned whether or not a
 * line moves.
 *
 * Purely presentational — polarity, colour and markers are decided by the caller
 * from real engine fields (yin_yang / value / moving).
 */
export function LineBar({ yang, barClass, glow, mark, className }: LineBarProps) {
  const bar = barClass ?? 'bg-ink-muted';
  const glowClass = glow ? 'shadow-[0_0_10px_rgba(245,215,127,0.55)]' : '';

  return (
    <div className={`flex items-center gap-1 ${className ?? ''}`}>
      <div className="flex h-2.5 flex-1 items-center">
        {yang ? (
          <span className={`h-2.5 w-full rounded-full ${bar} ${glowClass}`} />
        ) : (
          <span className="flex w-full items-center justify-between gap-2">
            <span className={`h-2.5 w-[42%] rounded-full ${bar} ${glowClass}`} />
            <span className={`h-2.5 w-[42%] rounded-full ${bar} ${glowClass}`} />
          </span>
        )}
      </div>
      <span
        aria-hidden="true"
        className="w-4 shrink-0 text-center font-numeric text-[11px] font-bold leading-none text-gold-bright"
      >
        {mark ?? ''}
      </span>
    </div>
  );
}
