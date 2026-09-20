import { useEffect, useState } from 'react';

/**
 * Subscribe to a ticking wall-clock `Date`.
 *
 * Powers the App Shell status bar's live observatory clock. The value is the real
 * client system time — never a fabricated offset — so the shell telemetry stays
 * honest while no chart has been computed yet.
 *
 * @param intervalMs refresh cadence in milliseconds (default 1000 = every second).
 * @returns a `Date` that is replaced on each tick for the lifetime of the caller.
 */
export function useNow(intervalMs = 1000): Date {
  const [now, setNow] = useState<Date>(() => new Date());

  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), intervalMs);
    return () => window.clearInterval(id);
  }, [intervalMs]);

  return now;
}
