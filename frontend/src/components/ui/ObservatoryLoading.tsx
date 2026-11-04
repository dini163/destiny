interface ObservatoryLoadingProps {
  /** The message describing the calculation currently in progress. */
  message: string;
  className?: string;
}

/**
 * Celestial astrolabe animated loading indicator for divination & calculation.
 * Gives ceremonial feedback while retaining strict accessibility and reduced-motion fallbacks.
 */
export function ObservatoryLoading({ message, className = '' }: ObservatoryLoadingProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      className={`my-6 flex flex-col items-center justify-center gap-3 py-6 text-center ${className}`}
    >
      <div className="relative flex h-14 w-14 items-center justify-center">
        {/* Outer glowing halo */}
        <div className="absolute inset-0 rounded-full bg-gold/10 blur-md animate-pulse" />

        {/* Outer slow-spinning astrolabe ring with celestial tick marks */}
        <svg
          viewBox="0 0 100 100"
          className="absolute inset-0 h-full w-full animate-[spin_8s_linear_infinite] text-gold/40"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          aria-hidden="true"
        >
          <circle cx="50" cy="50" r="46" strokeDasharray="4 6" />
          <circle cx="50" cy="50" r="38" strokeWidth="0.75" strokeOpacity="0.5" />
          <circle cx="50" cy="4" r="2.5" fill="currentColor" />
          <circle cx="96" cy="50" r="2.5" fill="currentColor" />
          <circle cx="50" cy="96" r="2.5" fill="currentColor" />
          <circle cx="4" cy="50" r="2.5" fill="currentColor" />
        </svg>

        {/* Inner counter-rotating ring */}
        <svg
          viewBox="0 0 100 100"
          className="absolute inset-2 h-10 w-10 animate-[spin_5s_linear_infinite_reverse] text-gold-bright"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          aria-hidden="true"
        >
          <polygon points="50,15 80,65 20,65" strokeOpacity="0.4" strokeWidth="1" />
          <polygon points="50,85 80,35 20,35" strokeOpacity="0.4" strokeWidth="1" />
          <circle cx="50" cy="50" r="28" strokeDasharray="6 8" />
        </svg>

        {/* Core pulsing star */}
        <div className="h-2 w-2 rounded-full bg-gold-bright shadow-[0_0_10px_rgba(245,215,127,0.9)] animate-ping" />
      </div>

      <p className="label-caps tracking-widest text-gold-soft text-glow-gold text-xs">
        {message}
      </p>
    </div>
  );
}
