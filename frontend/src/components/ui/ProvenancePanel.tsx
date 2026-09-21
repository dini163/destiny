import { SourceNote } from './SourceNote';
import type { ProvenanceTable } from '../../types/common';

/** 表上方的一行署名事实，如「排盘引擎 · lunar-python」。 */
export interface ProvenanceMeta {
  label: string;
  value: string;
  /** 悬停说明（例如"请求未指定时取服务器当日"）。 */
  title?: string;
}

interface ProvenancePanelProps {
  tables: ProvenanceTable[];
  /** 系统专有的署名事实；姓名学传 Unihan 版本与生成日期。 */
  meta?: ProvenanceMeta[];
  /** 覆盖范围声明：本系统刻意*不*判什么，与判了什么同样是事实。 */
  notes?: string[];
}

export function ProvenancePanel({ tables, meta, notes }: ProvenancePanelProps) {
  return (
    <div className="flex flex-col gap-3">
      {meta?.map((row) => (
        <div key={row.label} className="flex flex-wrap items-baseline justify-between gap-2 text-sm">
          <span className="text-ink">{row.label}</span>
          <span className="numeric text-ink-variant" title={row.title}>
            {row.value}
          </span>
        </div>
      ))}
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
          {tables.map((table) => (
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
      {notes && notes.length > 0 ? (
        <ul className="flex flex-col gap-1 text-xs text-ink-muted">
          {notes.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
