import { planetColor } from '../../lib/astro';
import type { MovingPoint } from '../../types/transit';

interface MovingPointTableProps {
  /** The selected layer's moving bodies (transit / progressed / directed). */
  points: MovingPoint[];
}

/**
 * Moving-layer ephemeris table.
 *
 * Lists each moving body's sign, within-sign degree and — the key overlay datum —
 * which *natal* house it now falls in, plus retrograde status. All values are the
 * backend's real computed positions; nothing is invented here (PRD no-mock rule).
 */
export function MovingPointTable({ points }: MovingPointTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="label-caps text-ink-muted">
            <th className="px-2 py-2 text-left font-normal">星体</th>
            <th className="px-2 py-2 text-left font-normal">星座</th>
            <th className="px-2 py-2 text-right font-normal">黄经度</th>
            <th className="px-2 py-2 text-center font-normal">本命宫</th>
            <th className="px-2 py-2 text-center font-normal">逆行</th>
          </tr>
        </thead>
        <tbody>
          {points.map((point) => {
            const color = planetColor(point.name);
            return (
              <tr key={point.name} className="border-t border-rim-soft">
                <td className="px-2 py-2">
                  <span className="flex items-center gap-2">
                    <span className="text-base leading-none" style={{ color }}>
                      {point.glyph}
                    </span>
                    <span className="text-ink">{point.name_zh}</span>
                  </span>
                </td>
                <td className="px-2 py-2">
                  <span className="flex items-center gap-1.5 text-ink-variant">
                    <span style={{ color }}>{point.sign_glyph}</span>
                    {point.sign_zh}
                  </span>
                </td>
                <td className="numeric px-2 py-2 text-right text-ink">{point.degree_text}</td>
                <td className="numeric px-2 py-2 text-center text-ink-variant">{point.natal_house}</td>
                <td className="px-2 py-2 text-center">
                  {point.retrograde ? (
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
