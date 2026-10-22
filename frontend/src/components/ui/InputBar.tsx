import { useEffect, useState } from 'react';
import type { FormEvent, ReactNode } from 'react';

import type { CalendarType } from '../../types/common';
import { ChineseDateField, ChineseTimeField } from './DateTimeField';
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
  /**
   * Re-fill the fields whenever this value changes (e.g. the user picked a saved
   * profile). Unlike `initial`, applying is explicit: every non-null change
   * overwrites the current boxes. Pages pass `profileToBirthInput(profile)`.
   */
  preset?: BirthInputValues | null;
  /** System-specific controls (e.g. gender, house system) rendered in the grid. */
  children?: ReactNode;
  /** Toolbar rendered beside the submit button (e.g. the profile picker). */
  profilePicker?: ReactNode;
  /** When set, renders a 存入档案 button that emits the current values for the page to persist. */
  onSaveProfile?: (values: BirthInputValues) => void;
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
  preset,
  children,
  profilePicker,
  onSaveProfile,
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

  // A picked profile overwrites every field at once (see the `preset` doc).
  useEffect(() => {
    if (!preset) return;
    setBirthDate(preset.birth_date ?? '');
    setBirthTime(preset.birth_time ?? '');
    if (preset.calendar) setCalendar(preset.calendar);
    setLocation({
      city: preset.city ?? null,
      latitude: preset.latitude ?? null,
      longitude: preset.longitude ?? null,
    });
  }, [preset]);

  const ready =
    birthDate !== '' &&
    birthTime !== '' &&
    location.longitude != null &&
    (!requireLatitude || location.latitude != null);

  function buildValues(): BirthInputValues {
    return {
      birth_date: birthDate,
      birth_time: birthTime,
      calendar: showCalendar ? calendar : undefined,
      city: location.city ?? null,
      latitude: location.latitude ?? null,
      longitude: location.longitude ?? null,
    };
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    if (!ready || pending) {
      return;
    }
    onSubmit(buildValues());
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
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          {profilePicker}
          {onSaveProfile ? (
            <button
              type="button"
              className="btn-ghost shrink-0"
              disabled={!birthDate || !birthTime}
              title={birthDate && birthTime ? '把当前生辰与出生地存入本地档案' : '填写生辰后即可存入档案'}
              onClick={() => onSaveProfile(buildValues())}
            >
              <Icon name="vault" size={18} />
              存入档案
            </button>
          ) : null}
          <button type="submit" className="btn-primary shrink-0" disabled={!ready || pending}>
            <Icon name="sparkle" size={18} />
            {submitLabel}
          </button>
        </div>
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
          <div className="flex flex-col gap-2">
            <ChineseDateField
              value={birthDate}
              onChange={setBirthDate}
              calendar={showCalendar ? calendar : 'solar'}
            />
            <ChineseTimeField value={birthTime} onChange={setBirthTime} />
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
