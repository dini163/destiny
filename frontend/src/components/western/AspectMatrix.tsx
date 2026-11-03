import { useMemo } from 'react';

import { useI18n } from '../../i18n/context';
import { aspectStyle, planetColor } from '../../lib/astro';
import type { Aspect, PlanetPlacement } from '../../types/western';

interface AspectMatrixProps {
  planets: PlanetPlacement[];
  aspects: Aspect[];
}

/** Format a decimal orb as degrees+minutes, e.g. `2°34'`. */
function formatOrb(orb: number): string {
  const degrees = Math.floor(orb);
  const minutes = Math.round((orb - degrees) * 60);
  return `${degrees}°${String(minutes).padStart(2, '0')}'`;
}

/**
 * Major-aspect grid (关键相位网格).
 *
 * Renders every aspect the engine detected, tightest orb first, using the real
 * body glyphs/names and the aspect angle + orb. Colour and Chinese labels come
 * from the shared aspect style map; no aspect is added or interpreted here.
 */
export function AspectMatrix({ planets, aspects }: AspectMatrixProps) {
  const { t } = useI18n();
  const bodyByName = useMemo(() => {
    const map = new Map<string, PlanetPlacement>();
    planets.forEach((planet) => map.set(planet.name, planet));
    return map;
  }, [planets]);

  if (aspects.length === 0) {
    return <p className="text-sm text-ink-muted">{t('当前星盘未检测到容许度内的主要相位。')}</p>;
  }

  return (
    <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
      {aspects.map((aspect, index) => {
        const body1 = bodyByName.get(aspect.planet1);
        const body2 = bodyByName.get(aspect.planet2);
        const style = aspectStyle(aspect.type);
        return (
          <div
            key={`${aspect.planet1}-${aspect.type}-${aspect.planet2}-${index}`}
            className="flex items-center justify-between gap-2 rounded-element border border-rim-soft bg-surface px-3 py-2"
          >
            <div className="flex min-w-0 items-center gap-2">
              <span className="flex items-center gap-1 truncate text-sm font-medium text-ink">
                <BodyLabel body={body1} fallback={aspect.planet1} />
                <span style={{ color: style.color }} className="text-base">
                  {aspect.glyph}
                </span>
                <BodyLabel body={body2} fallback={aspect.planet2} />
              </span>
            </div>
            <div className="shrink-0 text-right">
              <span className="numeric block text-xs" style={{ color: style.color }}>
                {style.label} {aspect.angle}°
              </span>
              <span className="numeric text-[11px] text-ink-muted">{t('容许度')} {formatOrb(aspect.orb)}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

/** A coloured glyph + Chinese name for one aspect endpoint. */
function BodyLabel({ body, fallback }: { body: PlanetPlacement | undefined; fallback: string }) {
  if (!body) {
    return <span className="text-ink-variant">{fallback}</span>;
  }
  return (
    <span className="flex items-center gap-1">
      <span style={{ color: planetColor(body.name) }}>{body.glyph}</span>
      <span className="text-ink-variant">{body.name_zh}</span>
    </span>
  );
}
