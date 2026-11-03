import { useMemo } from 'react';

import { useI18n } from '../../i18n/context';
import {
  SIGN_GLYPHS,
  aspectStyle,
  planetColor,
  polarToCartesian,
  wheelAngle,
} from '../../lib/astro';
import type { Aspect, AxisPoint, HouseCusp, PlanetPlacement } from '../../types/western';

// --- Wheel geometry (600×600 canvas, centre at 300,300) --------------------
const CX = 300;
const CY = 300;
const R_DECOR = 292; // filled nebula disc
const R_RING_DASH = 289; // dashed outer rim
const R_GLYPH = 272; // zodiac sign glyphs
const R_ZOD_OUT = 255; // zodiac band outer edge
const R_ZOD_IN = 216; // zodiac band inner edge (sign ticks span these)
const R_CUSP_OUT = 216; // house cusp lines reach the zodiac band
const R_CUSP_IN = 54; // house cusp lines start near the centre
const R_ASPECT = 150; // aspect chords live on this inner ring
const R_PLANET_A = 196; // planet marker radius (stagger outer)
const R_PLANET_B = 174; // planet marker radius (stagger inner)
const R_AXIS_BADGE = 202; // ASC/DES/MC/IC badges
const R_CENTER = 44; // astrolabe pivot

const DISPLAY_FONT = "'Noto Serif SC', 'Noto Serif', serif";
const NUMERIC_FONT = "'Space Grotesk', sans-serif";

interface AstroWheelProps {
  planets: PlanetPlacement[];
  axes: AxisPoint[];
  houses: HouseCusp[];
  aspects: Aspect[];
}

/**
 * Natal astro-wheel (天球黄道命盘轮图).
 *
 * A real, computed chart wheel: the Ascendant is fixed at 9 o'clock and every
 * sign boundary, house cusp, axis, aspect chord and planet marker is plotted
 * from the ephemeris longitudes returned by the backend. Planets are sorted by
 * wheel angle and alternately staggered onto two radii so adjacent bodies do not
 * overlap. Exact degrees live in the ephemeris table, keeping the wheel legible.
 */
export function AstroWheel({ planets, axes, houses, aspects }: AstroWheelProps) {
  const { t } = useI18n();
  const ascendant = axes.find((axis) => axis.name === 'ASC');
  const ascLon = ascendant?.longitude ?? 0;

  const angleAt = (longitude: number): number => wheelAngle(longitude, ascLon);
  const pointAt = (longitude: number, radius: number) =>
    polarToCartesian(CX, CY, radius, angleAt(longitude));

  // Stable per-planet radius: sort by wheel angle, alternate the two radii.
  const radiusByName = useMemo(() => {
    const sorted = [...planets].sort(
      (a, b) => wheelAngle(a.longitude, ascLon) - wheelAngle(b.longitude, ascLon),
    );
    const map = new Map<string, number>();
    sorted.forEach((planet, index) => {
      map.set(planet.name, index % 2 === 0 ? R_PLANET_A : R_PLANET_B);
    });
    return map;
  }, [planets, ascLon]);

  const longitudeByName = useMemo(() => {
    const map = new Map<string, number>();
    planets.forEach((planet) => map.set(planet.name, planet.longitude));
    return map;
  }, [planets]);

  const axisByName = useMemo(() => {
    const map = new Map<string, AxisPoint>();
    axes.forEach((axis) => map.set(axis.name, axis));
    return map;
  }, [axes]);

  return (
    <svg viewBox="0 0 600 600" className="h-full w-full select-none" role="img" aria-label={t('本命星盘轮图')}>
      <defs>
        <radialGradient id="wheelNebula" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#282a30" stopOpacity="0.55" />
          <stop offset="65%" stopColor="#191b22" stopOpacity="0.95" />
          <stop offset="100%" stopColor="#0c0e14" stopOpacity="1" />
        </radialGradient>
      </defs>

      {/* Background discs */}
      <circle cx={CX} cy={CY} r={R_DECOR} fill="url(#wheelNebula)" />
      <circle cx={CX} cy={CY} r={R_RING_DASH} fill="none" stroke="#4d4635" strokeWidth={1.5} strokeDasharray="3,3" />
      <circle cx={CX} cy={CY} r={R_ZOD_OUT} fill="#14161f" stroke="#d4af37" strokeOpacity={0.4} strokeWidth={1} />
      <circle cx={CX} cy={CY} r={R_ZOD_IN} fill="#111319" stroke="#99907c" strokeOpacity={0.3} strokeWidth={0.75} />
      <circle cx={CX} cy={CY} r={R_ASPECT} fill="#0c0e14" stroke="#4d4635" strokeWidth={1} />

      {/* Zodiac sign ticks (every 30°) */}
      <g stroke="#99907c" strokeOpacity={0.3} strokeWidth={0.75}>
        {Array.from({ length: 12 }, (_, index) => {
          const inner = pointAt(index * 30, R_ZOD_IN);
          const outer = pointAt(index * 30, R_ZOD_OUT);
          return <line key={`tick-${index}`} x1={inner.x} y1={inner.y} x2={outer.x} y2={outer.y} />;
        })}
      </g>

      {/* Zodiac sign glyphs (centred in each 30° sector) */}
      <g fill="#e1c46e" fontFamily={DISPLAY_FONT} fontSize={17} textAnchor="middle" dominantBaseline="central">
        {SIGN_GLYPHS.map((glyph, index) => {
          const point = pointAt(index * 30 + 15, R_GLYPH);
          return (
            <text key={`sign-${glyph}`} x={point.x} y={point.y}>
              {glyph}
            </text>
          );
        })}
      </g>

      {/* House cusp lines */}
      <g stroke="#99907c" strokeOpacity={0.28} strokeWidth={0.75}>
        {houses.map((cusp) => {
          const inner = pointAt(cusp.longitude, R_CUSP_IN);
          const outer = pointAt(cusp.longitude, R_CUSP_OUT);
          return <line key={`cusp-${cusp.house}`} x1={inner.x} y1={inner.y} x2={outer.x} y2={outer.y} />;
        })}
      </g>

      {/* Cardinal axes: ASC–DES and MC–IC */}
      <AxisLine pointAt={pointAt} axisByName={axisByName} a="ASC" b="DES" />
      <AxisLine pointAt={pointAt} axisByName={axisByName} a="MC" b="IC" />

      {/* Aspect chords on the inner ring */}
      <g>
        {aspects.map((aspect, index) => {
          const lon1 = longitudeByName.get(aspect.planet1);
          const lon2 = longitudeByName.get(aspect.planet2);
          if (lon1 == null || lon2 == null) {
            return null;
          }
          const p1 = pointAt(lon1, R_ASPECT);
          const p2 = pointAt(lon2, R_ASPECT);
          const style = aspectStyle(aspect.type);
          return (
            <line
              key={`aspect-${index}`}
              x1={p1.x}
              y1={p1.y}
              x2={p2.x}
              y2={p2.y}
              stroke={style.color}
              strokeOpacity={0.75}
              strokeWidth={aspect.type === 'sextile' ? 1 : 1.3}
              strokeDasharray={aspect.type === 'sextile' ? '4,2' : undefined}
            />
          );
        })}
      </g>

      {/* Axis badges (drawn above chords) */}
      {(['ASC', 'DES', 'MC', 'IC'] as const).map((name) => {
        const axis = axisByName.get(name);
        if (!axis) {
          return null;
        }
        const point = pointAt(axis.longitude, R_AXIS_BADGE);
        return (
          <g key={`badge-${name}`}>
            <rect
              x={point.x - 18}
              y={point.y - 11}
              width={36}
              height={22}
              rx={4}
              fill="#f2ca50"
              stroke="#111319"
              strokeWidth={0.5}
            />
            <text
              x={point.x}
              y={point.y}
              fill="#3c2f00"
              fontFamily={NUMERIC_FONT}
              fontSize={11}
              fontWeight={700}
              textAnchor="middle"
              dominantBaseline="central"
            >
              {name}
            </text>
          </g>
        );
      })}

      {/* Planet markers */}
      {planets.map((planet) => {
        const radius = radiusByName.get(planet.name) ?? R_PLANET_A;
        const marker = pointAt(planet.longitude, radius);
        const anchor = pointAt(planet.longitude, R_ZOD_IN);
        const color = planetColor(planet.name);
        return (
          <g key={`planet-${planet.name}`}>
            <line
              x1={anchor.x}
              y1={anchor.y}
              x2={marker.x}
              y2={marker.y}
              stroke={color}
              strokeOpacity={0.5}
              strokeWidth={1}
            />
            <circle cx={marker.x} cy={marker.y} r={13} fill="#14161f" stroke={color} strokeWidth={1.5} />
            <text
              x={marker.x}
              y={marker.y}
              fill={color}
              fontFamily={DISPLAY_FONT}
              fontSize={14}
              textAnchor="middle"
              dominantBaseline="central"
            >
              {planet.glyph}
            </text>
            {planet.retrograde ? (
              <text
                x={marker.x + 11}
                y={marker.y - 11}
                fill="#ffb4ab"
                fontFamily={NUMERIC_FONT}
                fontSize={9}
                textAnchor="middle"
              >
                ℞
              </text>
            ) : null}
          </g>
        );
      })}

      {/* Centre pivot */}
      <circle cx={CX} cy={CY} r={R_CENTER} fill="#191b22" stroke="#d4af37" strokeOpacity={0.5} strokeWidth={1} />
      <circle cx={CX} cy={CY} r={4} fill="#f2ca50" />
    </svg>
  );
}

/** A bold gold diameter line joining an opposite axis pair (e.g. ASC–DES). */
function AxisLine({
  pointAt,
  axisByName,
  a,
  b,
}: {
  pointAt: (longitude: number, radius: number) => { x: number; y: number };
  axisByName: Map<string, AxisPoint>;
  a: string;
  b: string;
}) {
  const axisA = axisByName.get(a);
  const axisB = axisByName.get(b);
  if (!axisA || !axisB) {
    return null;
  }
  const start = pointAt(axisA.longitude, R_CUSP_OUT);
  const end = pointAt(axisB.longitude, R_CUSP_OUT);
  return <line x1={start.x} y1={start.y} x2={end.x} y2={end.y} stroke="#f2ca50" strokeWidth={1.5} strokeOpacity={0.65} />;
}
