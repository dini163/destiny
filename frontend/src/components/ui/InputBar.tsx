import { useState } from 'react';
import type { FormEvent, ReactNode } from 'react';

import type { CalendarType } from '../../types/common';
import { Icon } from './Icon';
import { LabeledField } from './LabeledField';
import { LocationField } from './LocationField';
import type { LocationValue } from './LocationField';
import { SegmentedControl } from './SegmentedControl';
import { TrueSolarTimeBadge } from './TrueSolarTimeBadge';

/** The birth-data slice every natal system needs, emitted on submit. */
export interface BirthInputValues extends LocationValue {
  birth_date: string;
  birth_time: string;
  calendar?: CalendarType;
}

const CALENDAR_OPTIONS: ReadonlyArray<{ value: CalendarType; label: string }> = [
  { value: 'solar', label: '公历' },
  { value: 'lunar', label: '农历' },
];

interface InputBarProps {
  /** Console headline. */
  title: string;
  /** One-line description of the engine. */
  subtitle?: string;
  /** Small provenance chip beside the title (e.g. the engine name). */
  badge?: string;
  /** Show the 公历/农历 toggle (Chinese systems); Western natal is Gregorian-only. */
  showCalendar?: boolean;
  /**
   * Require a latitude as well as a longitude before enabling submit. Western
   * charts need the full geographic position because houses and the ascendant
   * depend on latitude, not just longitude.
   */
  requireLatitude?: boolean;
  /** Overrides the default True Solar Time preview (e.g. the Western UTC-offset note). */
  footerSlot?: ReactNode;
  /**
   * Pre-fill the fields, for a page reached from a link whose query string carries
   * the birth data. Seeds the boxes once; a mounted console stays under the user's edits.
   */
  initial?: BirthInputValues;
  /** System-specific controls (e.g. gender, house system) rendered in the grid. */
  children?: ReactNode;
  /** Primary button label. */
  submitLabel: string;
  /** Disable the button and show a busy state while a request is in flight. */
  pending?: boolean;
  /** Called with the resolved birth data when the console is complete. */
  onSubmit: (values: BirthInputValues) => void;
}

/**
 * Shared birth-data input console (PRD §7 input bar).
 *
 * Owns the date/time/calendar fields and the location picker, and previews the True
 * Solar Time correction once a longitude is resolved — hiding the geocoding and TST
 * plumbing from each page. Pages inject system-specific controls through `children`
 * and receive a ready-to-send {@link BirthInputValues} on submit. Submission is
 * gated on a complete date, time and location so the backend never gets a request it
 * would reject for missing birth data.
 */
export function InputBar({
  title,
  subtitle,
  badge,
  showCalendar = false,
  requireLatitude = false,
  footerSlot,
  initial,
  children,
  submitLabel,
  pending = false,
  onSubmit,
}: InputBarProps) {
  const [birthDate, setBirthDate] = useState(initial?.birth_date ?? '');
  const [birthTime, setBirthTime] = useState(initial?.birth_time ?? '');
  const [calendar, setCalendar] = useState<CalendarType>(initial?.calendar ?? 'solar');
  const [location, setLocation] = useState<LocationValue>({
    city: initial?.city ?? null,
    latitude: initial?.latitude ?? null,
    longitude: initial?.longitude ?? null,
  });

  const ready =
    birthDate !== '' &&
    birthTime !== '' &&
    location.longitude != null &&
    (!requireLatitude || location.latitude != null);

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    if (!ready || pending) {
      return;
    }
    onSubmit({
      birth_date: birthDate,
      birth_time: birthTime,
      calendar: showCalendar ? calendar : undefined,
      city: location.city ?? null,
      latitude: location.latitude ?? null,
      longitude: location.longitude ?? null,
    });
  }

  return (
    <form onSubmit={handleSubmit} className="panel-raised flex flex-col gap-5 p-5 sm:p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-card border border-rim bg-surface text-gold">
            <Icon name="compass" size={22} />
          </span>
          <div className="flex flex-col gap-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="font-display text-xl font-semibold text-ink sm:text-2xl">{title}</h1>
              {badge ? (
                <span className="label-caps rounded-element bg-gold/15 px-2 py-0.5 text-gold">{badge}</span>
              ) : null}
            </div>
            {subtitle ? (
              <p className="max-w-2xl text-sm leading-relaxed text-ink-muted">{subtitle}</p>
            ) : null}
          </div>
        </div>
        <button type="submit" className="btn-primary shrink-0" disabled={!ready || pending}>
          <Icon name="sparkle" size={18} />
          {submitLabel}
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-12">
        <LabeledField
          className="xl:col-span-5"
          label="生辰（精准至分）"
          hint={
            showCalendar ? (
              <SegmentedControl
                ariaLabel="历法"
                options={CALENDAR_OPTIONS}
                value={calendar}
                onChange={(next) => setCalendar(next)}
              />
            ) : undefined
          }
        >
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            <div className="flex items-center gap-2 rounded-element border border-rim bg-[#0e111a] px-3 py-2 transition focus-within:border-rim-strong">
              <Icon name="calendar" size={16} className="shrink-0 text-ink-muted" />
              <input
                className="numeric w-full bg-transparent text-sm text-ink outline-none"
                type="date"
                value={birthDate}
                onChange={(event) => setBirthDate(event.target.value)}
                aria-label="出生日期"
              />
            </div>
            <div className="flex items-center gap-2 rounded-element border border-rim bg-[#0e111a] px-3 py-2 transition focus-within:border-rim-strong">
              <Icon name="clock" size={16} className="shrink-0 text-ink-muted" />
              <input
                className="numeric w-full bg-transparent text-sm text-ink outline-none"
                type="time"
                value={birthTime}
                onChange={(event) => setBirthTime(event.target.value)}
                aria-label="出生时间"
              />
            </div>
          </div>
        </LabeledField>

        <LabeledField className="xl:col-span-4" label="出生基准地（全球坐标）">
          <LocationField value={location} onChange={(next) => setLocation(next)} />
        </LabeledField>

        {children ? <div className="flex flex-col gap-3 xl:col-span-3">{children}</div> : null}
      </div>

      {footerSlot ?? (
        <TrueSolarTimeBadge
          date={birthDate || null}
          time={birthTime || null}
          longitude={location.longitude ?? null}
        />
      )}
      {!ready ? (
        <p className="label-caps text-ink-muted">
          {requireLatitude
            ? '填写出生日期、时间并完成经纬度定位后即可排盘。'
            : '填写出生日期、时间并完成定位后即可排盘。'}
        </p>
      ) : null}
    </form>
  );
}
