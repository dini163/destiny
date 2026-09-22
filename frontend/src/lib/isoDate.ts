/**
 * ISO 日期加减若干天，仍在 ISO 里。
 *
 * `T00:00:00Z` + `setUTCDate` 是必须的：按本地时区做加减会在夏令时切换那两天跳错一天，
 * 而跳错一天的症状是整段矩阵少一天或多一天，没人会把它当时区问题去查。
 */
export function shiftIso(iso: string, days: number): string {
  const next = new Date(`${iso}T00:00:00Z`);
  next.setUTCDate(next.getUTCDate() + days);
  return next.toISOString().slice(0, 10);
}
