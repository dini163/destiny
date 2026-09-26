import {
  SIGN_GLYPHS,
  aspectStyle,
  planetColor,
  polarToCartesian,
  wheelAngle,
} from '../../lib/astro';
import type { SynastryAspect } from '../../types/synastry';
import type { WesternChart } from '../../types/western';

// --- Bi-wheel geometry (600×600 canvas, centre at 300,300) -----------------
const CX = 300;
const CY = 300;
const R_DECOR = 292; // filled nebula disc
const R_RING_DASH = 289; // dashed outer rim
const R_GLYPH = 276; // zodiac sign glyphs
const R_ZOD_OUT = 262; // zodiac band outer edge
const R_ZOD_IN = 234; // zodiac band inner edge
const R_B_OUT = 218; // person B marker radius (stagger outer)
const R_B_IN = 200; // person B marker radius (stagger inner)
const R_SPLIT = 186; // boundary: outer person-B ring vs inner person-A wheel
const R_CUSP_OUT = 186; // person-A house cusps reach the split
const R_CUSP_IN = 56; // person-A house cusps start near the centre
const R_A_OUT = 162; // person A marker radius (stagger outer)
const R_A_IN = 142; // person A marker radius (stagger inner)
const R_CHORD_B = 194; // chord outer anchor (person B side)
const R_CHORD_A = 134; // chord inner anchor (person A side)
const R_CENTER = 40; // astrolabe pivot

const DISPLAY_FONT = "'Noto Serif SC', 'Noto Serif', serif";
const NUMERIC_FONT = "'Space Grotesk', sans-serif";
const AXIS_COLOR = '#f2ca50';

/** A point one chart offers the wheel: a planet (with glyph) or the ASC/MC angle. */
interface RingPoint {
  name: string;
  glyph: string;
  longitude: number;
  isAxis: boolean;
}

/** Ten planets plus ASC and MC — exactly the points the synastry aspects reference. */
function ringPoints(chart: WesternChart): RingPoint[] {
  const points: RingPoint[] = chart.planets.map((planet) => ({
    name: planet.name,
    glyph: planet.glyph,
    longitude: planet.longitude,
    isAxis: false,
  }));
  for (const axis of chart.axes) {
    if (axis.name === 'ASC' || axis.name === 'MC') {
      points.push({ name: axis.name, glyph: axis.name, longitude: axis.longitude, isAxis: true });
    }
  }
  return points;
}

interface SynastryBiWheelProps {
  /** Person A fixes the orientation (their ASC at 9 o'clock) and the inner ring. */
  chartA: WesternChart;
  /** Person B rides the outer ring, sharing person A's orientation. */
  chartB: WesternChart;
  /** Person-to-person aspects; only the counted ones are drawn as chords. */
  aspects: SynastryAspect[];
  nameA: string;
  nameB: string;
}

/**
 * Synastry bi-wheel (合盘双轮盘).
 *
 * Two real natal wheels sharing one orientation — person A's Ascendant is fixed at
 * 9 o'clock for both rings, so a straight line from an outer (B) point to an inner
 * (A) point *is* their aspect. The inner disc carries person A's houses, axes and
 * planets; the outer ring carries person B's. Chords are drawn only for the aspects
 * that count toward the score (both endpoints personal), core bonds heavier, so the
 * wheel shows exactly the relationships the ledger pays for. Every longitude comes
 * from the ephemeris via the backend — nothing is invented here (PRD no-mock rule).
 */
export function SynastryBiWheel({ chartA, chartB, aspects, nameA, nameB }: SynastryBiWheelProps) {
  const ascA = chartA.axes.find((axis) => axis.name === 'ASC');
  const ascLon = ascA?.longitude ?? 0;

  const angleAt = (longitude: number): number => wheelAngle(longitude, ascLon);
  const pointAt = (longitude: number, radius: number) =>
    polarToCartesian(CX, CY, radius, angleAt(longitude));

  const pointsA = ringPoints(chartA);
  const pointsB = ringPoints(chartB);

  const radiusA = staggerByName(pointsA, ascLon, R_A_OUT, R_A_IN);
  const radiusB = staggerByName(pointsB, ascLon, R_B_OUT, R_B_IN);

  const lonA = new Map<string, number>(pointsA.map((p) => [p.name, p.longitude]));
  const lonB = new Map<string, number>(pointsB.map((p) => [p.name, p.longitude]));

  const axisByNameA = new Map(chartA.axes.map((axis) => [axis.name, axis]));
  const counted = aspects.filter((aspect) => aspect.counted);

  return (
    <svg
      viewBox="0 0 600 600"
      className="h-full w-full select-none"
      role="img"
      aria-label={`合盘双轮盘：内圈${nameA}，外圈${nameB}`}
    >
      <defs>
        <radialGradient id="synastryNebula" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#282a30" stopOpacity="0.55" />
          <stop offset="65%" stopColor="#191b22" stopOpacity="0.95" />
          <stop offset="100%" stopColor="#0c0e14" stopOpacity="1" />
        </radialGradient>
      </defs>

      {/* Background discs */}
      <circle cx={CX} cy={CY} r={R_DECOR} fill="url(#synastryNebula)" />
      <circle cx={CX} cy={CY} r={R_RING_DASH} fill="none" stroke="#4d4635" strokeWidth={1.5} strokeDasharray="3,3" />
      <circle cx={CX} cy={CY} r={R_ZOD_OUT} fill="#14161f" stroke="#d4af37" strokeOpacity={0.4} strokeWidth={1} />
      <circle cx={CX} cy={CY} r={R_ZOD_IN} fill="#111319" stroke="#99907c" strokeOpacity={0.3} strokeWidth={0.75} />
      {/* Inner person-A disc, split from person-B ring by a brass boundary */}
      <circle cx={CX} cy={CY} r={R_SPLIT} fill="#0c0e14" stroke="#d4af37" strokeOpacity={0.5} strokeWidth={1.25} />

      {/* Zodiac sign ticks (every 30°) */}
      <g stroke="#99907c" strokeOpacity={0.3} strokeWidth={0.75}>
        {Array.from({ length: 12 }, (_, index) => {
          const inner = pointAt(index * 30, R_ZOD_IN);
          const outer = pointAt(index * 30, R_ZOD_OUT);
          return <line key={`tick-${index}`} x1={inner.x} y1={inner.y} x2={outer.x} y2={outer.y} />;
        })}
      </g>

      {/* Zodiac sign glyphs (centred in each 30° sector) */}
      <g fill="#e1c46e" fontFamily={DISPLAY_FONT} fontSize={16} textAnchor="middle" dominantBaseline="central">
        {SIGN_GLYPHS.map((glyph, index) => {
          const point = pointAt(index * 30 + 15, R_GLYPH);
          return (
            <text key={`sign-${glyph}`} x={point.x} y={point.y}>
              {glyph}
            </text>
          );
        })}
      </g>

      {/* Person-A house cusp lines (inner disc only) */}
      <g stroke="#99907c" strokeOpacity={0.28} strokeWidth={0.75}>
        {chartA.houses.map((cusp) => {
          const inner = pointAt(cusp.longitude, R_CUSP_IN);
          const outer = pointAt(cusp.longitude, R_CUSP_OUT);
          return <line key={`cusp-${cusp.house}`} x1={inner.x} y1={inner.y} x2={outer.x} y2={outer.y} />;
        })}
      </g>

      {/* Person-A cardinal axes: ASC–DES and MC–IC */}
      <AxisLine pointAt={pointAt} axisByName={axisByNameA} a="ASC" b="DES" />
      <AxisLine pointAt={pointAt} axisByName={axisByNameA} a="MC" b="IC" />

      {/* Counted synastry chords: outer person B → inner person A */}
      <g>
        {counted.map((aspect, index) => {
          const la = lonA.get(aspect.point_a);
          const lb = lonB.get(aspect.point_b);
          if (la == null || lb == null) {
            return null;
          }
          const from = pointAt(lb, R_CHORD_B);
          const to = pointAt(la, R_CHORD_A);
          const style = aspectStyle(aspect.type);
          return (
            <line
              key={`chord-${index}`}
              x1={from.x}
              y1={from.y}
              x2={to.x}
              y2={to.y}
              stroke={style.color}
              strokeOpacity={aspect.core_bond ? 0.85 : 0.5}
              strokeWidth={aspect.core_bond ? 1.8 : 1}
              strokeDasharray={aspect.type === 'sextile' ? '4,2' : undefined}
            />
          );
        })}
      </g>

      {/* Person-A axis badges (drawn above chords, at the split) */}
      {(['ASC', 'MC'] as const).map((name) => {
        const axis = axisByNameA.get(name);
        if (!axis) {
          return null;
        }
        const point = pointAt(axis.longitude, R_SPLIT + 4);
        return (
          <g key={`badgeA-${name}`}>
            <rect x={point.x - 16} y={point.y - 9} width={32} height={18} rx={3} fill={AXIS_COLOR} stroke="#111319" strokeWidth={0.5} />
            <text x={point.x} y={point.y} fill="#3c2f00" fontFamily={NUMERIC_FONT} fontSize={10} fontWeight={700} textAnchor="middle" dominantBaseline="central">
              {name}
            </text>
          </g>
        );
      })}

      {/* Person-A markers (inner ring) */}
      {pointsA.map((point) => (
        <Marker key={`A-${point.name}`} point={point} at={pointAt} radius={radiusA.get(point.name) ?? R_A_OUT} outer={false} />
      ))}

      {/* Person-B markers (outer ring) */}
      {pointsB.map((point) => (
        <Marker key={`B-${point.name}`} point={point} at={pointAt} radius={radiusB.get(point.name) ?? R_B_OUT} outer />
      ))}

      {/* Centre pivot */}
      <circle cx={CX} cy={CY} r={R_CENTER} fill="#191b22" stroke="#d4af37" strokeOpacity={0.5} strokeWidth={1} />
      <circle cx={CX} cy={CY} r={4} fill={AXIS_COLOR} />
      <text x={CX} y={CY - 14} fill="#99907c" fontFamily={NUMERIC_FONT} fontSize={9} textAnchor="middle" letterSpacing="0.5">
        SYNASTRY
      </text>
    </svg>
  );
}

/** Alternate points onto two radii by wheel angle so adjacent glyphs do not overlap. */
function staggerByName(points: RingPoint[], ascLon: number, rA: number, rB: number): Map<string, number> {
  const sorted = [...points].sort((a, b) => wheelAngle(a.longitude, ascLon) - wheelAngle(b.longitude, ascLon));
  const map = new Map<string, number>();
  sorted.forEach((point, index) => map.set(point.name, index % 2 === 0 ? rA : rB));
  return map;
}

/** A single body/angle marker; the outer person gets a brass halo to tell the rings apart. */
function Marker({
  point,
  at,
  radius,
  outer,
}: {
  point: RingPoint;
  at: (longitude: number, radius: number) => { x: number; y: number };
  radius: number;
  outer: boolean;
}) {
  const marker = at(point.longitude, radius);
  const color = point.isAxis ? AXIS_COLOR : planetColor(point.name);

  if (point.isAxis) {
    return (
      <g>
        {outer ? <circle cx={marker.x} cy={marker.y} r={15} fill="none" stroke={AXIS_COLOR} strokeOpacity={0.4} strokeWidth={1} /> : null}
        <rect x={marker.x - 15} y={marker.y - 8} width={30} height={16} rx={3} fill="#12141d" stroke={color} strokeWidth={1.25} />
        <text x={marker.x} y={marker.y} fill={color} fontFamily={NUMERIC_FONT} fontSize={9} fontWeight={700} textAnchor="middle" dominantBaseline="central">
          {point.name}
        </text>
      </g>
    );
  }

  return (
    <g>
      {outer ? <circle cx={marker.x} cy={marker.y} r={15} fill="none" stroke={AXIS_COLOR} strokeOpacity={0.4} strokeWidth={1} /> : null}
      <circle cx={marker.x} cy={marker.y} r={12} fill="#14161f" stroke={color} strokeWidth={1.5} />
      <text x={marker.x} y={marker.y} fill={color} fontFamily={DISPLAY_FONT} fontSize={13} textAnchor="middle" dominantBaseline="central">
        {point.glyph}
      </text>
    </g>
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
  axisByName: Map<string, { longitude: number }>;
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
  return <line x1={start.x} y1={start.y} x2={end.x} y2={end.y} stroke={AXIS_COLOR} strokeWidth={1.5} strokeOpacity={0.55} />;
}
