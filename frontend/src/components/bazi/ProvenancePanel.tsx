import { SourceNote } from '../ui/SourceNote';
import type { Provenance } from '../../types/bazi';

/**
 * The audit footer: engine, the date the luck-pillar cutoff was taken from, and
 * every table the response drew on with its own citation.
 *
 * The two fixed notes below are coverage statements, not interpretation: what
 * the engine deliberately does *not* decide is as much a fact as what it does.
 */
const SCOPE_NOTES = [
  '格局未纳入从格与合化（spec §6.4 的口径边界）。',
  'design 稿的干支示例与实算不符时，一律以引擎输出为准（spec §2.1）。',
];

export function ProvenancePanel({ provenance }: { provenance: Provenance }) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-baseline justify-between gap-2 text-sm">
        <span className="text-ink">排盘引擎</span>
        <span className="text-gold-soft">{provenance.engine}</span>
      </div>
      <div className="flex flex-wrap items-baseline justify-between gap-2 text-sm">
        <span className="text-ink">大运参照日</span>
        <span className="numeric text-ink-variant" title="请求未指定时取服务器当日">
          {provenance.reference_date}
        </span>
      </div>
      <table className="w-full text-xs">
        <caption className="sr-only">本响应引用的数据表</caption>
        <thead>
          <tr className="text-left text-ink-muted">
            <th scope="col" className="font-normal">
              表名
            </th>
            <th scope="col" className="font-normal">
              版本
            </th>
            <th scope="col" className="text-right font-normal">
              出处
            </th>
          </tr>
        </thead>
        <tbody>
          {provenance.tables.map((table) => (
            <tr key={table.name} className="border-t border-rim">
              <td className="py-1.5 text-ink-variant">{table.name}</td>
              <td className="numeric py-1.5 text-ink-muted">{table.version}</td>
              <td className="py-1.5 text-right">
                <SourceNote source={table.source} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <ul className="flex flex-col gap-1 text-xs text-ink-muted">
        {SCOPE_NOTES.map((note) => (
          <li key={note}>{note}</li>
        ))}
      </ul>
    </div>
  );
}
