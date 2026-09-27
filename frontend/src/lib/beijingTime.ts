function pad2(value: number): string {
  return String(value).padStart(2, '0');
}

/**
 * The Beijing (UTC+8) civil clock of an instant, independent of the viewer's own
 * timezone.
 *
 * `getTime()` is *already* the UTC epoch instant, so shifting it by eight hours and
 * reading the `getUTC*` fields is the whole conversion. Adding
 * `getTimezoneOffset()` on top — the term needed only when reading the *local*
 * getters — cancels the shift and leaves raw UTC: correct on a UTC viewer, eight
 * hours slow for the GMT+8 audience this panel is written for.
 */
export function beijingTime(now: Date): { date: string; minute: string; clock: string } {
  const beijing = new Date(now.getTime() + 8 * 3_600_000);
  const minute = `${pad2(beijing.getUTCHours())}:${pad2(beijing.getUTCMinutes())}`;
  return {
    date: `${beijing.getUTCFullYear()}-${pad2(beijing.getUTCMonth() + 1)}-${pad2(beijing.getUTCDate())}`,
    minute,
    clock: `${minute}:${pad2(beijing.getUTCSeconds())}`,
  };
}
