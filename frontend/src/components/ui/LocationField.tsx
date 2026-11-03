import { useEffect, useRef, useState } from 'react';

import { useI18n } from '../../i18n/context';
import { useCities } from '../../hooks/useCities';
import { Icon } from './Icon';

/** The resolved birth-location slice emitted to the parent form. */
export interface LocationValue {
  city?: string | null;
  latitude?: number | null;
  longitude?: number | null;
}

interface LocationFieldProps {
  value: LocationValue;
  onChange: (next: LocationValue) => void;
}

/** Format a signed longitude as e.g. `104.07°E`. */
function formatLongitude(longitude: number): string {
  return `${Math.abs(longitude).toFixed(2)}°${longitude >= 0 ? 'E' : 'W'}`;
}

/** Format a signed latitude as e.g. `30.57°N`. */
function formatLatitude(latitude: number): string {
  return `${Math.abs(latitude).toFixed(2)}°${latitude >= 0 ? 'N' : 'S'}`;
}

/**
 * Birth-location picker: geocoded city search with a manual lat/lon fallback.
 *
 * Wraps the `/meta/cities` lookup (see `useCities`) and hides the autocomplete
 * plumbing. Selecting a city fills both coordinates; editing a coordinate switches
 * to manual mode and clears the city label. The manual fallback matters because the
 * bundled snapshot is a curated subset (PRD: city DB + manual lat/lon).
 */
export function LocationField({ value, onChange }: LocationFieldProps) {
  const { t } = useI18n();
  const [term, setTerm] = useState('');
  const [open, setOpen] = useState(false);
  const boxRef = useRef<HTMLDivElement>(null);
  const { data, isFetching, isError, refetch } = useCities(term);

  // Dismiss the suggestion list when clicking outside the field.
  useEffect(() => {
    function onPointerDown(event: MouseEvent): void {
      if (boxRef.current && !boxRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', onPointerDown);
    return () => document.removeEventListener('mousedown', onPointerDown);
  }, []);

  const searching = open && term.trim().length > 0;
  const results = searching ? (data ?? []) : [];
  const hasCoords = value.latitude != null && value.longitude != null;

  function selectCity(name: string, latitude: number, longitude: number): void {
    onChange({ city: name, latitude, longitude });
    setTerm('');
    setOpen(false);
  }

  function editCoordinate(axis: 'latitude' | 'longitude', raw: string): void {
    const trimmed = raw.trim();
    const parsed = trimmed === '' ? Number.NaN : Number(trimmed);
    const next: LocationValue = { ...value, city: null };
    const resolved = Number.isFinite(parsed) ? parsed : null;
    if (axis === 'latitude') {
      next.latitude = resolved;
    } else {
      next.longitude = resolved;
    }
    onChange(next);
  }

  function clear(): void {
    onChange({ city: null, latitude: null, longitude: null });
    setTerm('');
  }

  return (
    <div className="flex flex-col gap-2">
      <div ref={boxRef} className="relative">
        {/* A <label> makes the entire 44px row — icon and trailing affordance included — a single tap target that focuses the input; a bare input would only be tappable across its ~20px text line. */}
        <label className="flex min-h-11 items-center gap-2 rounded-element border border-rim bg-[var(--field-bg)] px-3 transition focus-within:border-rim-strong">
          <Icon name="pin" size={16} className="shrink-0 text-gold" />
          <input
            className="w-full bg-transparent text-sm text-ink outline-none placeholder:text-ink-muted"
            type="text"
            value={term}
            placeholder={value.city ? value.city : t('搜索城市，或下方直接填写经纬度')}
            onChange={(event) => {
              setTerm(event.target.value);
              setOpen(true);
            }}
            onFocus={() => setOpen(true)}
            aria-label={t('出生城市搜索')}
          />
          {hasCoords || value.city ? (
            <button
              type="button"
              onClick={clear}
              className="shrink-0 text-ink-muted transition hover:text-ink"
              aria-label={t('清除地点')}
            >
              <Icon name="close" size={16} />
            </button>
          ) : (
            <Icon name="search" size={16} className="shrink-0 text-ink-muted" />
          )}
        </label>

        {searching && results.length > 0 ? (
          <ul className="absolute z-20 mt-1 max-h-56 w-full overflow-auto rounded-element border border-rim bg-surface-raised/95 py-1 shadow-xl backdrop-blur-xl">
            {results.map((city) => (
              <li key={`${city.name}-${city.longitude}`}>
                <button
                  type="button"
                  className="flex w-full items-center justify-between gap-2 px-3 py-2 text-left text-sm transition hover:bg-gold/10"
                  onClick={() => selectCity(city.name, city.latitude, city.longitude)}
                >
                  <span className="text-ink">
                    {city.name}
                    <span className="ml-1 text-ink-muted">{city.province}</span>
                  </span>
                  <span className="numeric shrink-0 text-xs text-gold-soft">
                    {formatLongitude(city.longitude)}, {formatLatitude(city.latitude)}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        ) : null}

        {searching && !isFetching && isError ? (
          <div role="alert" className="absolute z-20 mt-1 w-full rounded-element border border-rim bg-surface-raised px-3 py-2 text-sm text-ink shadow-xl">
            <p>{t('城市查询服务暂时不可用，请检查后端服务是否启动，或在下方手动填写经纬度。')}</p>
            <button type="button" className="mt-1 min-h-11 text-gold underline" onClick={() => void refetch()}>
              {t('重试查询')}
            </button>
          </div>
        ) : null}

        {searching && !isFetching && !isError && data && results.length === 0 ? (
          <p className="absolute z-20 mt-1 w-full rounded-element border border-rim bg-surface-raised/95 px-3 py-2 text-xs text-ink-muted backdrop-blur-xl">
            {t('未匹配到「{{term}}」，请在下方手动填写经纬度。', { term: term.trim() })}
          </p>
        ) : null}
      </div>

      <div className="grid grid-cols-2 gap-2">
        <label className="flex min-h-11 items-center gap-1.5 rounded-element border border-rim bg-[var(--field-bg)] px-2.5 transition focus-within:border-rim-strong">
          <span className="label-caps shrink-0">{t('纬度')}</span>
          <input
            className="numeric w-full bg-transparent text-right text-sm text-ink outline-none placeholder:text-ink-muted"
            type="number"
            step="0.0001"
            min={-90}
            max={90}
            inputMode="decimal"
            placeholder="30.5728"
            value={value.latitude ?? ''}
            onChange={(event) => editCoordinate('latitude', event.target.value)}
            aria-label={t('纬度')}
          />
        </label>
        <label className="flex min-h-11 items-center gap-1.5 rounded-element border border-rim bg-[var(--field-bg)] px-2.5 transition focus-within:border-rim-strong">
          <span className="label-caps shrink-0">{t('经度')}</span>
          <input
            className="numeric w-full bg-transparent text-right text-sm text-ink outline-none placeholder:text-ink-muted"
            type="number"
            step="0.0001"
            min={-180}
            max={180}
            inputMode="decimal"
            placeholder="104.0668"
            value={value.longitude ?? ''}
            onChange={(event) => editCoordinate('longitude', event.target.value)}
            aria-label={t('经度')}
          />
        </label>
      </div>

      {hasCoords ? (
        <p className="numeric flex items-center gap-1.5 text-xs text-gold-soft">
          <Icon name="check" size={14} className="shrink-0" />
          {value.city ? `${value.city} · ` : `${t('手动坐标')} · `}
          {formatLongitude(value.longitude as number)}, {formatLatitude(value.latitude as number)}
        </p>
      ) : null}
    </div>
  );
}
