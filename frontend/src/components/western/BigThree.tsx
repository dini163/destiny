import { planetColor } from '../../lib/astro';
import { useI18n } from '../../i18n/context';
import type { AxisPoint, PlanetPlacement } from '../../types/western';

interface BigThreeProps {
  planets: PlanetPlacement[];
  axes: AxisPoint[];
}

/**
 * The natal trinity (本命三巨头): Sun, Moon and Ascendant.
 *
 * Each totem shows the real sign (Chinese + English), the exact degree and the
 * house from the ephemeris. No personality copy is invented — the design's
 * interpretive one-liners are deliberately omitted (PRD no-mock rule).
 */
export function BigThree({ planets, axes }: BigThreeProps) {
  const { t } = useI18n();
  const sun = planets.find((planet) => planet.name === 'Sun');
  const moon = planets.find((planet) => planet.name === 'Moon');
  const ascendant = axes.find((axis) => axis.name === 'ASC');

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
      {sun ? (
        <Totem
          eyebrow={t('太阳 ☉ SUN')}
          color={planetColor('Sun')}
          signZh={sun.sign_zh}
          sign={sun.sign}
          degree={sun.degree_text}
          house={sun.house}
        />
      ) : null}
      {moon ? (
        <Totem
          eyebrow={t('月亮 ☽ MOON')}
          color={planetColor('Moon')}
          signZh={moon.sign_zh}
          sign={moon.sign}
          degree={moon.degree_text}
          house={moon.house}
        />
      ) : null}
      {ascendant ? (
        <Totem
          eyebrow={t('上升 ASC')}
          color="#e1c46e"
          signZh={ascendant.sign_zh}
          sign={ascendant.sign}
          degree={ascendant.degree_text}
          house={ascendant.house}
        />
      ) : null}
    </div>
  );
}

/** A single trinity totem card. */
function Totem({
  eyebrow,
  color,
  signZh,
  sign,
  degree,
  house,
}: {
  eyebrow: string;
  color: string;
  signZh: string;
  sign: string;
  degree: string;
  house: number;
}) {
  const { t } = useI18n();
  return (
    <div className="flex flex-col items-center gap-1 rounded-card border border-rim bg-surface p-4 text-center transition hover:border-rim-strong">
      <span className="label-caps" style={{ color }}>
        {eyebrow}
      </span>
      <span className="font-display text-2xl font-semibold text-ink">{signZh}</span>
      <span className="text-xs text-ink-muted">{sign}</span>
      <span className="numeric mt-1 text-sm text-gold-soft">{degree}</span>
      <span className="mt-1 rounded-element bg-surface-raised px-2 py-0.5 text-xs text-ink-variant">
        {t('第 {{house}} 宫', { house })}
      </span>
    </div>
  );
}
