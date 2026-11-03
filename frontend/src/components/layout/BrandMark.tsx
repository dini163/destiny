/**
 * Destiny brand lockup — the eight-pointed observatory star beside the wordmark.
 *
 * Purely presentational (no routing) so it can sit inside the header link or the
 * footer seal. The star geometry matches `public/favicon.svg` for one identity.
 * The tagline below the wordmark is translated via `useI18n()` because it reads
 * as brand copy rather than an icon, and overseas users benefit from an English
 * variant on every page.
 */
import { useI18n } from '../../i18n/context';

export function BrandMark({ compact = false }: { compact?: boolean }) {
  const { t } = useI18n();
  return (
    <span className="brand-lockup flex items-center gap-3 text-gold">
      <svg viewBox="0 0 64 64" className="h-8 w-8 shrink-0" role="img" aria-label="Destiny">
        <g fill="none" stroke="currentColor" strokeWidth={1.25}>
          <circle cx="32" cy="32" r="23" opacity="0.45" />
          <circle cx="32" cy="32" r="17" opacity="0.3" />
        </g>
        <path
          d="M32 5 L36.6 27.4 L59 32 L36.6 36.6 L32 59 L27.4 36.6 L5 32 L27.4 27.4 Z"
          fill="currentColor"
        />
        <g stroke="currentColor" strokeWidth={1.1} opacity="0.65">
          <path d="M14.5 14.5 L26 26" />
          <path d="M49.5 14.5 L38 26" />
          <path d="M49.5 49.5 L38 38" />
          <path d="M14.5 49.5 L26 38" />
        </g>
        <circle cx="32" cy="32" r="2.6" fill="var(--void)" />
      </svg>
      {!compact && (
        <span className="flex flex-col leading-none">
          <span className="font-display text-lg font-semibold tracking-[0.18em] text-gold">
            DESTINY
          </span>
          <span className="label-caps mt-1.5">{t('观己 · 知时 · 懂相处')}</span>
        </span>
      )}
    </span>
  );
}
