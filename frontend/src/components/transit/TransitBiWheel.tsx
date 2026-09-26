import {
  SIGN_GLYPHS,
  aspectStyle,
  planetColor,
  polarToCartesian,
  wheelAngle,
} from '../../lib/astro';
import type { CrossAspect, MovingPoint } from '../../types/transit';
import type { WesternChart } from '../../types/western';

// --- Bi-wheel geometry (600×600 canvas, centre at 300,300) -----------------
const CX = 300;
const CY = 300;
const R_DECOR = 292; // filled nebula disc
const R_RING_DASH = 289; // dashed outer rim
const R_GLYPH = 276; // zodiac sign glyphs
const R_ZOD_OUT = 262; // zodiac band outer edge
const R_ZOD_IN = 234; // zodiac band inner edge
const R_MOVE_A = 214; // moving marker radius (stagger outer)
const R_MOVE_B = 194; // moving marker radius (stagger inner)
const R_SPLIT = 180; // boundary: outer moving ring vs inner natal wheel
const R_CUSP_OUT = 180; // natal house cusps reach the split
const R_CUSP_IN = 56; // natal house cusps start near the centre
const R_NATAL_A = 156; // natal marker radius (stagger outer)
const R_NATAL_B = 134; // natal marker radius (stagger inner)
const R_CHORD_MOVE = 182; // cross-aspect chord outer anchor (just inside split)
const R_CHORD_NATAL = 126; // cross-aspect chord inner anchor
const R_CENTER = 40; // astrolabe pivot

const DISPLAY_FONT = "'Noto Serif SC', 'Noto Serif', serif";
const NUMERIC_FONT = "'Space Grotesk', sans-serif";

interface TransitBiWheelProps {
  /** The embedded natal chart: fixes the wheel orientation and the inner ring. */
  natal: WesternChart;
  /** The selected layer's moving bodies, plotted on the outer ring. */
  positions: MovingPoint[];
  /** The selected layer's moving-to-natal aspects, drawn as cross chords. */
  aspects: CrossAspect[];
}

/**
 * Transit bi-wheel (行运双轮盘).
 *
 * A real two-ring computed chart sharing one orientation — the natal Ascendant is
 * fixed at 9 o'clock for both rings, so a straight line from an outer body to an
 * inner one *is* their aspect. The inner disc carries the natal houses, axes and
 * planets; the outer ring carries the selected moving layer (transit / progressed
 * / directed). Cross-aspect chords are drawn moving→natal and coloured by aspect
 * type. Every position and angle comes from the ephemeris via the backend — no
 * value is invented here (PRD no-mock rule).
 */
export function TransitBiWheel({ natal, positions, aspects }: TransitBiWheelProps) {
  const ascendant = natal.axes.find((axis) => axis.name === 'ASC');
  const ascLon = ascendant?.longitude ?? 0;

  const angleAt = (longitude: number): number => wheelAngle(longitude, ascLon);
  const pointAt = (longitude: number, radius: number) =>
    polarToCartesian(CX, CY, radius, angleAt(longitude));

  const natalRadiusByName = staggerByName(
    natal.planets.map((p) => ({ name: p.name, longitude: p.longitude })),
    ascLon,
    R_NATAL_A,
    R_NATAL_B,
  );
  const moveRadiusByName = staggerByName(
    positions.map((p) => ({ name: p.name, longitude: p.longitude })),
    ascLon,
    R_MOVE_A,
    R_MOVE_B,
  );

  const natalLonByName = new Map<string, number>();
  natal.planets.forEach((p) => natalLonByName.set(p.name, p.longitude));
  natal.axes.forEach((a) => natalLonByName.set(a.name, a.longitude));

  const axisByName = new Map(natal.axes.map((a) => [a.name, a]));

  return (
    <svg
      viewBox="0 0 600 600"
      className="h-full w-full select-none"
      role="img"
      aria-label="行运双轮盘：内圈本命，外圈移动层"
    >
      <defs>
        <radialGradient id="biWheelNebula" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#282a30" stopOpacity="0.55" />
          <stop offset="65%" stopColor="#191b22" stopOpacity="0.95" />
          <stop offset="100%" stopColor="#0c0e14" stopOpacity="1" />
        </radialGradient>
      </defs>

      {/* Background discs */}
      <circle cx={CX} cy={CY} r={R_DECOR} fill="url(#biWheelNebula)" />
      <circle cx={CX} cy={CY} r={R_RING_DASH} fill="none" stroke="#4d4635" strokeWidth={1.5} strokeDasharray="3,3" />
      <circle cx={CX} cy={CY} r={R_ZOD_OUT} fill="#14161f" stroke="#d4af37" strokeOpacity={0.4} strokeWidth={1} />
      <circle cx={CX} cy={CY} r={R_ZOD_IN} fill="#111319" stroke="#99907c" strokeOpacity={0.3} strokeWidth={0.75} />
      {/* Inner natal disc, split from the moving ring by a brass boundary */}
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

      {/* Natal house cusp lines (inner disc only) */}
      <g stroke="#99907c" strokeOpacity={0.28} strokeWidth={0.75}>
        {natal.houses.map((cusp) => {
          const inner = pointAt(cusp.longitude, R_CUSP_IN);
          const outer = pointAt(cusp.longitude, R_CUSP_OUT);
          return <line key={`cusp-${cusp.house}`} x1={inner.x} y1={inner.y} x2={outer.x} y2={outer.y} />;
        })}
      </g>

      {/* Cardinal axes: ASC–DES and MC–IC */}
      <AxisLine pointAt={pointAt} axisByName={axisByName} a="ASC" b="DES" />
      <AxisLine pointAt={pointAt} axisByName={axisByName} a="MC" b="IC" />

      {/* Cross-aspect chords: outer moving body → inner natal point */}
      <g>
        {aspects.map((aspect, index) => {
          const natalLon = natalLonByName.get(aspect.natal);
          const moveBody = positions.find((p) => p.name === aspect.moving);
          if (natalLon == null || !moveBody) {
            return null;
          }
          const from = pointAt(moveBody.longitude, R_CHORD_MOVE);
          const to = pointAt(natalLon, R_CHORD_NATAL);
          const style = aspectStyle(aspect.type);
          return (
            <line
              key={`xaspect-${index}`}
              x1={from.x}
              y1={from.y}
              x2={to.x}
              y2={to.y}
              stroke={style.color}
              strokeOpacity={0.5}
              strokeWidth={aspect.nature === 'challenging' ? 1.2 : 0.9}
              strokeDasharray={aspect.type === 'sextile' ? '4,2' : undefined}
            />
          );
        })}
      </g>

      {/* Axis badges (drawn above chords) */}
      {(['ASC', 'MC'] as const).map((name) => {
        const axis = axisByName.get(name);
        if (!axis) {
          return null;
        }
        const point = pointAt(axis.longitude, R_SPLIT + 4);
        return (
          <g key={`badge-${name}`}>
            <rect x={point.x - 16} y={point.y - 9} width={32} height={18} rx={3} fill="#f2ca50" stroke="#111319" strokeWidth={0.5} />
            <text
              x={point.x}
              y={point.y}
              fill="#3c2f00"
              fontFamily={NUMERIC_FONT}
              fontSize={10}
              fontWeight={700}
              textAnchor="middle"
              dominantBaseline="central"
            >
              {name}
            </text>
          </g>
        );
      })}

      {/* Natal planet markers (inner ring) */}
      {natal.planets.map((planet) => {
        const radius = natalRadiusByName.get(planet.name) ?? R_NATAL_A;
        const marker = pointAt(planet.longitude, radius);
        const color = planetColor(planet.name);
        return (
          <g key={`natal-${planet.name}`}>
            <circle cx={marker.x} cy={marker.y} r={12} fill="#14161f" stroke={color} strokeWidth={1.5} />
            <text x={marker.x} y={marker.y} fill={color} fontFamily={DISPLAY_FONT} fontSize={13} textAnchor="middle" dominantBaseline="central">
              {planet.glyph}
            </text>
          </g>
        );
      })}

      {/* Moving-layer planet markers (outer ring), leader-lined to the zodiac band */}
      {positions.map((body) => {
        const radius = moveRadiusByName.get(body.name) ?? R_MOVE_A;
        const marker = pointAt(body.longitude, radius);
        const anchor = pointAt(body.longitude, R_ZOD_IN);
        const color = planetColor(body.name);
        return (
          <g key={`move-${body.name}`}>
            <line x1={anchor.x} y1={anchor.y} x2={marker.x} y2={marker.y} stroke={color} strokeOpacity={0.5} strokeWidth={1} />
            {/* Brass halo marks this as a moving-layer body (vs the plain natal ring) */}
            <circle cx={marker.x} cy={marker.y} r={15} fill="none" stroke="#f2ca50" strokeOpacity={0.55} strokeWidth={1} />
            <circle cx={marker.x} cy={marker.y} r={11.5} fill="#12141d" stroke={color} strokeWidth={1.5} />
            <text x={marker.x} y={marker.y} fill={color} fontFamily={DISPLAY_FONT} fontSize={13} textAnchor="middle" dominantBaseline="central">
              {body.glyph}
            </text>
            {body.retrograde ? (
              <text x={marker.x + 12} y={marker.y - 12} fill="#ffb4ab" fontFamily={NUMERIC_FONT} fontSize={9} textAnchor="middle">
                ℞
              </text>
            ) : null}
          </g>
        );
      })}

      {/* Centre pivot */}
      <circle cx={CX} cy={CY} r={R_CENTER} fill="#191b22" stroke="#d4af37" strokeOpacity={0.5} strokeWidth={1} />
      <circle cx={CX} cy={CY} r={4} fill="#f2ca50" />
      <text x={CX} y={CY - 16} fill="#99907c" fontFamily={NUMERIC_FONT} fontSize={9} textAnchor="middle" letterSpacing="0.5">
        NATAL
      </text>
    </svg>
  );
}

/** Alternate bodies onto two radii by wheel angle so adjacent glyphs do not overlap. */
function staggerByName(
  points: Array<{ name: string; longitude: number }>,
  ascLon: number,
  rA: number,
  rB: number,
): Map<string, number> {
  const sorted = [...points].sort((a, b) => wheelAngle(a.longitude, ascLon) - wheelAngle(b.longitude, ascLon));
  const map = new Map<string, number>();
  sorted.forEach((point, index) => map.set(point.name, index % 2 === 0 ? rA : rB));
  return map;
}

/** A bold gold diameter line joining an opposite natal axis pair (e.g. ASC–DES). */
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
  return <line x1={start.x} y1={start.y} x2={end.x} y2={end.y} stroke="#f2ca50" strokeWidth={1.5} strokeOpacity={0.55} />;
}
