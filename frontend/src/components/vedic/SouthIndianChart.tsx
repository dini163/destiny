import { SOUTH_CELLS, grahaColor, planetsInSign, rashiByIndex } from '../../lib/vedic';
import { useI18n } from '../../i18n/context';
import type { VedicChart } from '../../types/vedic';

interface SouthIndianChartProps {
  chart: VedicChart;
}

/**
 * South-Indian rashi chart.
 *
 * The twelve signs occupy FIXED cells and run clockwise from Aries (top, second
 * column); the four centre cells are merged for the chart title. Each cell shows the
 * sign glyph/name, its whole-sign house counted from the Lagna, and the grahas within
 * it — every value the backend's real Lahiri-sidereal computation. The Lagna cell is
 * highlighted; nothing is invented on the client (PRD no-mock rule).
 */
export function SouthIndianChart({ chart }: SouthIndianChartProps) {
  const { t } = useI18n();
  return (
    <div className="relative mx-auto aspect-square w-full max-w-[560px]">
      <div className="grid h-full w-full grid-cols-4 grid-rows-4 gap-px overflow-hidden rounded-element border border-rim-soft bg-rim-soft">
        {SOUTH_CELLS.map((cell) => {
          const rashi = rashiByIndex(chart, cell.signIndex);
          if (!rashi) {
            return null;
          }
          const planets = planetsInSign(chart.planets, cell.signIndex);
          return (
            <div
              key={cell.signIndex}
              className={`flex flex-col gap-1 p-1.5 ${rashi.is_lagna ? 'bg-gold/10' : 'bg-surface'}`}
              style={{ gridRowStart: cell.row, gridColumnStart: cell.col }}
            >
              <div className="flex items-start justify-between gap-1">
                <span className="flex items-center gap-1 text-[11px] leading-none text-ink-variant">
                  <span className="text-sm leading-none text-gold">{rashi.sign_glyph}</span>
                  {rashi.sign_zh}
                </span>
                {rashi.is_lagna ? (
                  <span className="label-caps rounded bg-gold/20 px-1 text-[9px] text-gold-bright">命</span>
                ) : (
                  <span className="numeric text-[10px] leading-none text-ink-muted">{rashi.house}</span>
                )}
              </div>
              <div className="flex flex-1 flex-wrap content-start items-start gap-x-1.5 gap-y-1">
                {planets.map((planet) => (
                  <span
                    key={planet.name}
                    title={`${planet.name_zh} ${planet.degree_text} · ${planet.nakshatra_zh}`}
                    className="text-base leading-none"
                    style={{ color: grahaColor(planet.name) }}
                  >
                    {planet.glyph}
                    {planet.retrograde ? <span className="align-super text-[8px]">℞</span> : null}
                  </span>
                ))}
              </div>
            </div>
          );
        })}

        <div
          className="flex flex-col items-center justify-center gap-1 bg-[var(--field-bg)] p-2 text-center"
          style={{ gridRowStart: 2, gridRowEnd: 4, gridColumnStart: 2, gridColumnEnd: 4 }}
        >
          <span className="label-caps text-ink-muted">{t('南印盘 · SOUTH INDIAN')}</span>
          <span className="font-display text-sm text-gold-bright text-glow-gold">
            {t('上升')} {chart.lagna_sign_glyph} {chart.lagna_sign_zh}
          </span>
          <span className="text-xs text-ink-variant">
            {t('月亮')} {chart.moon_sign_zh} · {chart.moon_nakshatra_zh}
          </span>
          <span className="numeric mt-1 text-[10px] text-ink-muted">
            Ayanamsa {chart.ayanamsa.toFixed(2)}°
          </span>
        </div>
      </div>
    </div>
  );
}
