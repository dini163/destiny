import {
  NORTH_HOUSES,
  grahaColor,
  planetsInHouse,
  polygonCentroid,
  rashiNumber,
  signIndexOfHouse,
  toPointsAttr,
} from '../../lib/vedic';
import type { VedicChart } from '../../types/vedic';

interface NorthIndianChartProps {
  chart: VedicChart;
}

/**
 * North-Indian rashi chart.
 *
 * The twelve HOUSES occupy fixed polygons (house 1 is always the top-centre diamond)
 * while the sign numbers rotate with the Lagna. Each region shows its rashi number and
 * the grahas within it; the Lagna house is highlighted. Purely positional — every sign
 * and planet is the backend's real sidereal computation (PRD no-mock rule).
 */
export function NorthIndianChart({ chart }: NorthIndianChartProps) {
  return (
    <div className="relative mx-auto aspect-square w-full max-w-[560px] rounded-element border border-rim-soft bg-[#0b0e16] p-1">
      <svg viewBox="0 0 400 400" className="h-full w-full" role="img" aria-label="北印盘">
        {NORTH_HOUSES.map((house) => {
          const signIndex = signIndexOfHouse(house.house, chart.lagna_index);
          const centroid = polygonCentroid(house.points);
          const planets = planetsInHouse(chart.planets, house.house);
          const isLagna = house.house === 1;
          return (
            <g key={house.house}>
              <polygon
                points={toPointsAttr(house.points)}
                fill={isLagna ? 'rgba(242,202,80,0.10)' : 'transparent'}
                stroke="rgba(226,226,235,0.20)"
                strokeWidth="1"
              />
              {isLagna ? (
                <text
                  x={centroid.x}
                  y={centroid.y - 26}
                  textAnchor="middle"
                  fontSize="9"
                  letterSpacing="1"
                  fill="#f2ca50"
                >
                  命 LAGNA
                </text>
              ) : null}
              <text
                x={centroid.x}
                y={centroid.y - (isLagna ? 12 : 14)}
                textAnchor="middle"
                fontSize="12"
                fill={isLagna ? '#f2ca50' : '#8b8fa3'}
              >
                {rashiNumber(signIndex)}
              </text>
              {planets.map((planet, index) => (
                <text
                  key={planet.name}
                  x={centroid.x + (index % 2 === 0 ? -13 : 13)}
                  y={centroid.y + 6 + Math.floor(index / 2) * 18}
                  textAnchor="middle"
                  fontSize="15"
                  fill={grahaColor(planet.name)}
                >
                  {planet.glyph}
                  {planet.retrograde ? '℞' : ''}
                </text>
              ))}
            </g>
          );
        })}
      </svg>
    </div>
  );
}
