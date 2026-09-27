/**
 * 门户授时面板的两支民事钟格式化：北京时间与**访客本地时间**。
 *
 * 为什么两个都要：北京钟面是本仓库的术数口径（流时辰界按北京钟面整点，切片 4 决策 2/6），
 * 不能因为「显示本地时间」就从页面上消失；而访客自己所在时区的钟面才是他读到
 * 「现在几点」时心里那个数。两者都是纯格式化，不做任何历法或星历推算。
 */

/** 中国标准时间（北京）的 UTC 偏移分钟数；北京自 1991 年起无夏令时，常量即正确。 */
const BEIJING_OFFSET_MINUTES = 480;

/** 经度每度 4 分钟 ⇒ 一个时区偏移对应的标准经线 = 偏移分钟数 / 4。 */
const MINUTES_PER_DEGREE = 4;

export type CivilClock = {
  /** `YYYY-MM-DD` */
  date: string;
  /** `HH:MM`，喂给 `/meta/true-solar-time` 的 time 参数。 */
  minute: string;
  /** `HH:MM:SS`，面板大字。 */
  clock: string;
};

function pad2(value: number): string {
  return String(value).padStart(2, '0');
}

function civil(y: number, mo: number, d: number, h: number, mi: number, s: number): CivilClock {
  const hhmm = `${pad2(h)}:${pad2(mi)}`;
  return {
    date: `${y}-${pad2(mo + 1)}-${pad2(d)}`,
    minute: hhmm,
    clock: `${hhmm}:${pad2(s)}`,
  };
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
export function beijingTime(now: Date): CivilClock {
  const beijing = new Date(now.getTime() + BEIJING_OFFSET_MINUTES * 60_000);
  return civil(
    beijing.getUTCFullYear(),
    beijing.getUTCMonth(),
    beijing.getUTCDate(),
    beijing.getUTCHours(),
    beijing.getUTCMinutes(),
    beijing.getUTCSeconds(),
  );
}

export type LocalClock = CivilClock & {
  /** 访客语言的时区名，如 `中国标准时间` / `北美东部夏令时间`（夏令时已含在名里）。 */
  zoneLabel: string;
  /** `UTC+8` / `UTC−4` / `UTC+5:30`，取的是**这一刻**的偏移，故夏令时自动跟上。 */
  offsetLabel: string;
  /** 这只钟面所对应的标准经线，如 `东经 120°`；偏移大到来路上没有对应经线时如实说明。 */
  meridianLabel: string;
  /** 本地钟面与北京钟面读数相同（偏移 480 分钟），此时不必重复印第二行北京时间。 */
  sameAsBeijing: boolean;
};

function formatUtcOffset(minutes: number): string {
  if (minutes === 0) {
    return 'UTC±0';
  }
  const sign = minutes < 0 ? '−' : '+';
  const abs = Math.abs(minutes);
  const hours = Math.floor(abs / 60);
  const rest = abs % 60;
  return `UTC${sign}${hours}${rest === 0 ? '' : `:${pad2(rest)}`}`;
}

function formatMeridian(degrees: number): string {
  if (degrees > 180 || degrees < -180) {
    return '无对应标准经线';
  }
  if (degrees === 0) {
    return '本初子午线';
  }
  return `${degrees > 0 ? '东经' : '西经'} ${Math.abs(degrees)}°`;
}

/** 中文长名，由 `Intl` 的时区数据给出；数据缺位时退回一个不假装精确的通用词。 */
function zoneLabelOf(now: Date): string {
  const parts = new Intl.DateTimeFormat('zh-CN', { timeZoneName: 'long' }).formatToParts(now);
  return parts.find((part) => part.type === 'timeZoneName')?.value ?? '本地时区';
}

/**
 * The viewer's own wall clock, read through the local getters so the browser's
 * timezone (DST included) is what decides the civil time.
 *
 * The meridian is derived from the **current** offset, not the zone's nominal one,
 * because the number being printed is the DST-shifted clock: a summer London clock
 * matches 15°E, not the 0° it sits on. `Intl` uses the IANA tz database, so no
 * timezone arithmetic is invented here (AGENTS §6).
 */
export function localClock(now: Date): LocalClock {
  const offsetMinutes = -now.getTimezoneOffset();
  return {
    ...civil(now.getFullYear(), now.getMonth(), now.getDate(), now.getHours(), now.getMinutes(), now.getSeconds()),
    zoneLabel: zoneLabelOf(now),
    offsetLabel: formatUtcOffset(offsetMinutes),
    meridianLabel: formatMeridian(offsetMinutes / MINUTES_PER_DEGREE),
    sameAsBeijing: offsetMinutes === BEIJING_OFFSET_MINUTES,
  };
}
