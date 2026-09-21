import { SourceNote } from '../ui/SourceNote';
import { pillarColumnLabel } from '../../lib/pillars';
import type { HiddenStemWeight } from '../../types/bazi';

/**
 * Every branch's hidden stems with the weight the strength engine actually used
 * (spec §6.6 `hidden_stem_ledger`). One row per stem, grouped by pillar, so the
 * 得地 factor in the strength ledger can be traced to its inputs.
 */
export function HiddenStemTable({ rows }: { rows: HiddenStemWeight[] }) {
  if (rows.length === 0) return null; // 后端未返回该区就不渲染（spec §8.2 规则 3）

  const positions: string[] = [];
  for (const row of rows) if (!positions.includes(row.position)) positions.push(row.position);

  return (
    <div className="flex flex-col gap-3">
      {positions.map((position) => {
        const group = rows.filter((row) => row.position === position);
        // 一柱只有一支：branch 是整组的主语，写进表头，免得"戊辰"被读成一柱干支。
        const heading = `${pillarColumnLabel(position)} · ${group[0]?.branch ?? ''}`;
        return (
          <div key={position} className="flex flex-col gap-1">
            <span className="label-caps text-ink-muted" title={position}>
              {heading}
            </span>
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-ink-muted">
                  <th scope="col" className="font-normal">
                    藏干
                  </th>
                  <th scope="col" className="font-normal">
                    十神
                  </th>
                  <th scope="col" className="font-normal">
                    本中余
                  </th>
                  <th scope="col" className="numeric text-right">
                    权重
                  </th>
                  <th scope="col" className="text-right font-normal">
                    出处
                  </th>
                </tr>
              </thead>
              <tbody>
                {group.map((row) => (
                  <tr key={`${row.position}-${row.stem}`} className="border-t border-rim">
                    <td className="py-1.5 text-ink">{row.stem}</td>
                    <td className="py-1.5 text-ink-variant">{row.ten_god}</td>
                    <td className="py-1.5 text-ink-muted">{row.role}</td>
                    <td className="numeric py-1.5 text-right text-ink">{row.weight.toFixed(2)}</td>
                    <td className="py-1.5 text-right">
                      <SourceNote source={row.source} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      })}
    </div>
  );
}
