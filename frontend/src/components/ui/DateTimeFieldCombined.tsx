import { useEffect, useState } from 'react';

import { ChineseDateField, ChineseTimeField } from './DateTimeField';

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
 * that stays empty (→ "now" on the backend) until a full date and a time are chosen.
 *
 * Sits in its own module (rather than alongside `ChineseDateField` / `ChineseTimeField`
 * in `DateTimeField.tsx`) purely to keep that file under the components-line ratchet
 * (AGENTS §2 不变式 6); the wrapping is a thin composition and does not warrant its
 * own layer.
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
