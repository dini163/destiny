import { formatSpan, grahaColor } from '../../lib/vedic';
import { useI18n } from '../../i18n/context';
import type { Vimshottari } from '../../types/vedic';

interface DashaTimelineProps {
  vimshottari: Vimshottari;
}

/**
 * The Vimshottari dasha timeline.
 *
 * The 120-year sequence of mahadashas — each expanded into its nine antardashas —
 * counted from the nakshatra the natal Moon occupies. The header summarises the birth
 * balance and the period current on the target date; the running mahadasha and its
 * active antardasha are highlighted. All durations are the backend's real computation,
 * derived from the Moon's exact longitude (PRD no-mock rule).
 */
export function DashaTimeline({ vimshottari }: DashaTimelineProps) {
  const { t } = useI18n();
  const { current } = vimshottari;
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-x-5 gap-y-2 rounded-element border border-rim-soft bg-surface/60 px-3 py-2 text-sm">
        <span className="text-ink-muted">
          {t('生月宿')}{' '}
          <span className="text-gold-bright">{vimshottari.birth_nakshatra_zh}</span>
          <span className="numeric text-xs text-ink-muted"> ({vimshottari.birth_nakshatra})</span>
        </span>
        <span className="text-ink-muted">
          {t('起运主星')} <span className="text-gold-bright">{vimshottari.birth_lord_zh}</span>
        </span>
        <span className="text-ink-muted">
          {t('出生余额')}{' '}
          <span className="numeric text-gold-soft">{formatSpan(vimshottari.balance_at_birth_years, t)}</span>
        </span>
        {current ? (
          <span className="text-ink-muted">
            <span className="numeric">{current.target_date}</span> {t('行')}{' '}
            <span className="text-gold-bright">{current.mahadasha_lord_zh}</span> {t('大运')}
            {current.antardasha_lord_zh ? (
              <>
                {' '}· <span className="text-gold-soft">{current.antardasha_lord_zh}</span> {t('小运')}
              </>
            ) : null}
          </span>
        ) : null}
      </div>

      <ol className="flex flex-col gap-2">
        {vimshottari.mahadashas.map((md) => (
          <li
            key={`${md.lord}-${md.start_date}`}
            className={`rounded-element border px-3 py-2 ${
              md.is_current ? 'border-gold/50 bg-gold/10' : 'border-rim-soft bg-surface/40'
            }`}
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="flex items-center gap-2">
                <span className="text-base leading-none" style={{ color: grahaColor(md.lord) }}>
                  {md.glyph}
                </span>
                <span className={`font-display ${md.is_current ? 'text-gold-bright' : 'text-ink'}`}>
                  {md.lord_zh}{t('大运')}
                </span>
                <span className="numeric text-xs text-ink-muted">{formatSpan(md.years, t)}</span>
                {md.is_current ? (
                  <span className="label-caps rounded bg-gold/20 px-1.5 text-[9px] text-gold-bright">{t('现行')}</span>
                ) : null}
              </span>
              <span className="numeric text-xs text-ink-muted">
                {md.start_date} → {md.end_date}
              </span>
            </div>
            {md.antardashas.length ? (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {md.antardashas.map((ad) => (
                  <span
                    key={`${md.lord}-${ad.lord}-${ad.start_date}`}
                    title={`${ad.lord_zh} · ${formatSpan(ad.years, t)} · ${ad.start_date} → ${ad.end_date}`}
                    className={`flex items-center gap-1 rounded border px-1.5 py-0.5 text-[11px] ${
                      ad.is_current
                        ? 'border-gold/50 bg-gold/15 text-gold-bright'
                        : 'border-rim-soft bg-surface/60 text-ink-variant'
                    }`}
                  >
                    <span style={{ color: grahaColor(ad.lord) }}>{ad.glyph}</span>
                    {ad.lord_zh}
                    <span className="numeric text-ink-muted">{formatSpan(ad.years, t)}</span>
                  </span>
                ))}
              </div>
            ) : null}
          </li>
        ))}
      </ol>
    </div>
  );
}
