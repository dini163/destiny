import { useEffect, useMemo, useState } from 'react';

import type { CalendarType } from '../../types/common';
import { Icon } from './Icon';
import { SelectMenu } from './SelectMenu';

/**
 * Chinese 年/月/日 + 时/分 birth selectors.
 *
 * The native `<input type="date|time">` renders its field format and popup in the
 * *browser's* UI language, which the page `lang` cannot override — an English-locale
 * browser shows `mm/dd/yyyy` and AM/PM even on a zh-CN page. These dropdowns read as
 * Chinese in every locale, and they emit the exact same `yyyy-mm-dd` / `HH:MM` strings
 * the shared `InputBar` contract (and every backend `BirthInput`) already expects, so
 * they drop in without touching a single consuming page. Both fields stay empty until
 * a complete value is chosen, preserving the console's "must fill birth data" gate.
 */

const DEFAULT_MIN_YEAR = 1900;
const ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'] as const;

const MONTHS = buildRange(1, 12);
const HOURS = buildRange(0, 23);
const MINUTES = buildRange(0, 59);

const BOX_CLASS =
  'flex items-center gap-1 rounded-element border border-rim bg-[#0e111a] px-2 py-1.5 transition focus-within:border-rim-strong';
const UNIT_CLASS = 'shrink-0 text-xs text-ink-muted';

function buildRange(start: number, end: number): number[] {
  const out: number[] = [];
  for (let i = start; i <= end; i += 1) out.push(i);
  return out;
}

function pad2(n: number): string {
  return String(n).padStart(2, '0');
}

/** Days in the given month; 农历 caps at 30 (a lunar month is 29 or 30 days). */
function daysInMonth(year: number | '', month: number | '', calendar: CalendarType): number {
  if (calendar === 'lunar') return 30;
  if (year === '' || month === '') return 31;
  return new Date(year, month, 0).getDate();
}

/** 时辰 (地支) for an hour: 23:00–00:59 is 子时, 01:00–02:59 is 丑时, and so on. */
function shichenOf(hour: number): string {
  return `${ZHI[Math.floor(((hour + 1) % 24) / 2)]}时`;
}

function splitDate(value: string): { y: number | ''; m: number | ''; d: number | '' } {
  const [ys, ms, ds] = value.split('-');
  const y = ys ? Number(ys) : Number.NaN;
  const m = ms ? Number(ms) : Number.NaN;
  const d = ds ? Number(ds) : Number.NaN;
  return {
    y: Number.isFinite(y) && y > 0 ? y : '',
    m: Number.isFinite(m) && m > 0 ? m : '',
    d: Number.isFinite(d) && d > 0 ? d : '',
  };
}

function splitTime(value: string): { h: number | ''; min: number | '' } {
  const [hs, ms] = value.split(':');
  const h = hs ? Number(hs) : Number.NaN;
  const m = ms ? Number(ms) : Number.NaN;
  return {
    h: Number.isFinite(h) && h >= 0 ? h : '',
    min: Number.isFinite(m) && m >= 0 ? m : '',
  };
}

/**
 * Latest selectable birth year — the current year, because a birth date can't fall in
 * the future. Read live from the system clock, so the range rolls forward on its own
 * each New Year (2027 appears automatically once 2027 begins) with no code change.
 */
function defaultMaxYear(): number {
  return new Date().getFullYear();
}

/** Year list, newest-first (descending), widened to include an out-of-range prefill so it always renders. */
function buildYears(selected: number | '', minYear: number, maxYear: number): number[] {
  const start = selected !== '' && selected < minYear ? selected : minYear;
  const end = selected !== '' && selected > maxYear ? selected : maxYear;
  return buildRange(start, end).reverse();
}

interface ChineseDateFieldProps {
  /** Current `yyyy-mm-dd` value, or `''` when incomplete. */
  value: string;
  onChange: (next: string) => void;
  /** 农历 months are capped at 30 days; 公历 follows the real month length. */
  calendar?: CalendarType;
  /** Inclusive earliest selectable year. Defaults to 1900. */
  minYear?: number;
  /** Inclusive latest selectable year. Defaults to the current year. */
  maxYear?: number;
  /** Accessible-name prefix for the 年/月/日 selects. Defaults to 出生. */
  ariaLabel?: string;
}

/** 年 / 月 / 日 dropdowns emitting a `yyyy-mm-dd` string. */
export function ChineseDateField({
  value,
  onChange,
  calendar = 'solar',
  minYear = DEFAULT_MIN_YEAR,
  maxYear = defaultMaxYear(),
  ariaLabel = '出生',
}: ChineseDateFieldProps) {
  const seeded = splitDate(value);
  const [year, setYear] = useState<number | ''>(seeded.y);
  const [month, setMonth] = useState<number | ''>(seeded.m);
  const [day, setDay] = useState<number | ''>(seeded.d);

  // Adopt an externally completed value (e.g. a prefill link) part by part, so a
  // partial in-progress selection is never clobbered by the empty string it emits.
  useEffect(() => {
    const next = splitDate(value);
    if (next.y !== '') setYear(next.y);
    if (next.m !== '') setMonth(next.m);
    if (next.d !== '') setDay(next.d);
  }, [value]);

  const years = useMemo(() => buildYears(year, minYear, maxYear), [year, minYear, maxYear]);
  const maxDay = daysInMonth(year, month, calendar);

  function compose(y: number | '', m: number | '', d: number | ''): string {
    return y !== '' && m !== '' && d !== '' ? `${y}-${pad2(m)}-${pad2(d)}` : '';
  }

  function pickYear(raw: string): void {
    const y = raw === '' ? '' : Number(raw);
    const d = clamp(day, daysInMonth(y, month, calendar));
    setYear(y);
    setDay(d);
    onChange(compose(y, month, d));
  }

  function pickMonth(raw: string): void {
    const m = raw === '' ? '' : Number(raw);
    const d = clamp(day, daysInMonth(year, m, calendar));
    setMonth(m);
    setDay(d);
    onChange(compose(year, m, d));
  }

  function pickDay(raw: string): void {
    const d = raw === '' ? '' : Number(raw);
    setDay(d);
    onChange(compose(year, month, d));
  }

  // Re-clamp the day when the 公历/农历 toggle shortens the month (e.g. 31 → 30).
  useEffect(() => {
    if (day !== '' && day > maxDay) {
      setDay(maxDay);
      onChange(compose(year, month, maxDay));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [calendar, maxDay]);

  return (
    <div className={BOX_CLASS}>
      <Icon name="calendar" size={16} className="shrink-0 text-ink-muted" />
      <SelectMenu
        value={year === '' ? '' : String(year)}
        onChange={pickYear}
        ariaLabel={`${ariaLabel}年`}
        options={[
          { value: '', label: '----' },
          ...years.map((y) => ({ value: String(y), label: String(y) })),
        ]}
      />
      <span className={UNIT_CLASS}>年</span>
      <SelectMenu
        value={month === '' ? '' : String(month)}
        onChange={pickMonth}
        ariaLabel={`${ariaLabel}月`}
        options={[
          { value: '', label: '--' },
          ...MONTHS.map((m) => ({ value: String(m), label: pad2(m) })),
        ]}
      />
      <span className={UNIT_CLASS}>月</span>
      <SelectMenu
        value={day === '' ? '' : String(day)}
        onChange={pickDay}
        ariaLabel={`${ariaLabel}日`}
        options={[
          { value: '', label: '--' },
          ...buildRange(1, maxDay).map((d) => ({ value: String(d), label: pad2(d) })),
        ]}
      />
      <span className={UNIT_CLASS}>日</span>
    </div>
  );
}

interface ChineseTimeFieldProps {
  /** Current `HH:MM` value, or `''` when incomplete. */
  value: string;
  onChange: (next: string) => void;
  /** Accessible-name prefix for the 时/分 selects. Defaults to 出生. */
  ariaLabel?: string;
}

/** 时 / 分 dropdowns emitting an `HH:MM` string, with the 时辰 hinted once set. */
export function ChineseTimeField({ value, onChange, ariaLabel = '出生' }: ChineseTimeFieldProps) {
  const seeded = splitTime(value);
  const [hour, setHour] = useState<number | ''>(seeded.h);
  const [minute, setMinute] = useState<number | ''>(seeded.min);

  useEffect(() => {
    const next = splitTime(value);
    if (next.h !== '') setHour(next.h);
    if (next.min !== '') setMinute(next.min);
  }, [value]);

  function compose(h: number | '', m: number | ''): string {
    return h !== '' && m !== '' ? `${pad2(h)}:${pad2(m)}` : '';
  }

  function pickHour(raw: string): void {
    const h = raw === '' ? '' : Number(raw);
    setHour(h);
    onChange(compose(h, minute));
  }

  function pickMinute(raw: string): void {
    const m = raw === '' ? '' : Number(raw);
    setMinute(m);
    onChange(compose(hour, m));
  }

  return (
    <div className={BOX_CLASS}>
      <Icon name="clock" size={16} className="shrink-0 text-ink-muted" />
      <SelectMenu
        value={hour === '' ? '' : String(hour)}
        onChange={pickHour}
        ariaLabel={`${ariaLabel}时`}
        options={[
          { value: '', label: '--' },
          ...HOURS.map((h) => ({ value: String(h), label: pad2(h) })),
        ]}
      />
      <span className={UNIT_CLASS}>时</span>
      <SelectMenu
        value={minute === '' ? '' : String(minute)}
        onChange={pickMinute}
        ariaLabel={`${ariaLabel}分`}
        options={[
          { value: '', label: '--' },
          ...MINUTES.map((m) => ({ value: String(m), label: pad2(m) })),
        ]}
      />
      <span className={UNIT_CLASS}>分</span>
      {hour !== '' ? (
        <span className="ml-auto shrink-0 text-xs text-gold-soft">{shichenOf(hour)}</span>
      ) : null}
    </div>
  );
}

/** Clamp a chosen day into `1..max`, keeping an unset day unset. */
function clamp(day: number | '', max: number): number | '' {
  if (day === '') return '';
  return day > max ? max : day;
}

/** `'yyyy-mm-ddTHH:MM'` → `{ date, time }`; either half is `''` when absent. */
function splitDateTimeLocal(value: string): { date: string; time: string } {
  if (!value) return { date: '', time: '' };
  const [date, time] = value.split('T');
  return { date: date ?? '', time: (time ?? '').slice(0, 5) };
}

interface ChineseDateTimeFieldProps {
  /** Current `datetime-local` value (`yyyy-mm-ddTHH:MM`), or `''` when incomplete. */
  value: string;
  onChange: (next: string) => void;
  /** Inclusive earliest selectable year. Defaults to 1900. */
  minYear?: number;
  /** Inclusive latest selectable year. Defaults to the current year. */
  maxYear?: number;
  /** Accessible-name prefix for the selects. Defaults to 出生. */
  ariaLabel?: string;
}

/**
 * 年月日 + 时分 dropdowns emitting a `datetime-local` (`yyyy-mm-ddTHH:MM`) string — the
 * Chinese counterpart to `<input type="datetime-local">`, used for a 用事 / 起卦时刻
 * that stays empty (→ “now” on the backend) until a full date and a time are chosen.
 */
export function ChineseDateTimeField({
  value,
  onChange,
  minYear,
  maxYear,
  ariaLabel = '出生',
}: ChineseDateTimeFieldProps) {
  const seeded = splitDateTimeLocal(value);
  const [date, setDate] = useState(seeded.date);
  const [time, setTime] = useState(seeded.time);

  // Adopt an externally completed value part by part (never clobber a partial pick).
  useEffect(() => {
    const next = splitDateTimeLocal(value);
    if (next.date !== '') setDate(next.date);
    if (next.time !== '') setTime(next.time);
  }, [value]);

  function emit(nextDate: string, nextTime: string): void {
    onChange(nextDate !== '' && nextTime !== '' ? `${nextDate}T${nextTime}` : '');
  }

  return (
    <div className="flex flex-col gap-2">
      <ChineseDateField
        value={date}
        onChange={(next) => {
          setDate(next);
          emit(next, time);
        }}
        minYear={minYear}
        maxYear={maxYear}
        ariaLabel={ariaLabel}
      />
      <ChineseTimeField
        value={time}
        onChange={(next) => {
          setTime(next);
          emit(date, next);
        }}
        ariaLabel={ariaLabel}
      />
    </div>
  );
}
