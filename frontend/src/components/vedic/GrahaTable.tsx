import { grahaColor } from '../../lib/vedic';
import { useI18n } from '../../i18n/context';
import type { VedicChart } from '../../types/vedic';

interface GrahaTableProps {
  chart: VedicChart;
}

/**
 * The Navagraha ephemeris.
 *
 * Lists each of the nine grahas (the seven planets plus Rahu and Ketu — no
 * Uranus/Neptune/Pluto in classical Jyotish) with its sidereal sign, within-sign
 * degree, whole-sign house, nakshatra (+ lord and pada) and retrograde flag. All
 * values are the backend's real Lahiri-ayanamsa computation (PRD no-mock rule).
 */
export function GrahaTable({ chart }: GrahaTableProps) {
  const { t } = useI18n();
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="label-caps text-ink-muted">
            <th className="px-2 py-2 text-left font-normal">{t('行星 / Graha')}</th>
            <th className="px-2 py-2 text-left font-normal">{t('星座')}</th>
            <th className="px-2 py-2 text-right font-normal">{t('黄经度')}</th>
            <th className="px-2 py-2 text-center font-normal">{t('宫')}</th>
            <th className="px-2 py-2 text-left font-normal">{t('星宿 Nakshatra')}</th>
            <th className="px-2 py-2 text-center font-normal">{t('主星')}</th>
            <th className="px-2 py-2 text-center font-normal">{t('足')}</th>
            <th className="px-2 py-2 text-center font-normal">{t('逆')}</th>
          </tr>
        </thead>
        <tbody>
          {chart.planets.map((planet) => {
            const color = grahaColor(planet.name);
            return (
              <tr key={planet.name} className="border-t border-rim-soft">
                <td className="px-2 py-2">
                  <span className="flex items-center gap-2">
                    <span className="text-base leading-none" style={{ color }}>
                      {planet.glyph}
                    </span>
                    <span className="text-ink">{planet.name_zh}</span>
                    <span className="text-[10px] text-ink-muted">{planet.name_sa}</span>
                  </span>
                </td>
                <td className="px-2 py-2">
                  <span className="flex items-center gap-1.5 text-ink-variant">
                    <span style={{ color }}>{planet.sign_glyph}</span>
                    {planet.sign_zh}
                  </span>
                </td>
                <td className="numeric px-2 py-2 text-right text-ink">{planet.degree_text}</td>
                <td className="numeric px-2 py-2 text-center text-ink-variant">{planet.house}</td>
                <td className="px-2 py-2">
                  <span className="flex flex-col leading-tight">
                    <span className="text-ink-variant">{planet.nakshatra_zh}</span>
                    <span className="text-[10px] text-ink-muted">{planet.nakshatra}</span>
                  </span>
                </td>
                <td className="px-2 py-2 text-center text-ink-variant">{planet.nakshatra_lord_zh}</td>
                <td className="numeric px-2 py-2 text-center text-ink-variant">{planet.pada}</td>
                <td className="px-2 py-2 text-center">
                  {planet.retrograde ? (
                    <span className="text-[#ffb4ab]">℞</span>
                  ) : (
                    <span className="text-ink-muted">—</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
