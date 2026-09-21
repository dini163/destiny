import { SourceNote } from '../ui/SourceNote';
import type { NameChar } from '../../types/name';

interface CharProvenanceTableProps {
  chars: NameChar[];
}

/**
 * 字级溯源：每行的康熙笔画都以「部首画 + 部首外余画」的形式给出算式。
 *
 * 这是整页唯一解释"笔画从哪来"的地方（spec §2.2）。未收录的字如实显示"未收录"，
 * 不补一个看起来像值的数字（决策八）。
 */
export function CharProvenanceTable({ chars }: CharProvenanceTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <caption className="sr-only">逐字康熙笔画核定</caption>
        <thead>
          <tr className="text-left text-ink-muted">
            {['字', '正体', '部首', '算式', '康熙笔画', '拼音声调', '出处'].map((head) => (
              <th
                key={head}
                scope="col"
                className="whitespace-nowrap px-2 py-1.5 font-normal first:pl-0 last:pr-0"
              >
                {head}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {chars.map((item) => (
            <tr key={`${item.char}-${item.resolved}`} className="border-t border-rim">
              <td className="px-2 py-2 pl-0 font-display text-base text-ink last:border-b-0">
                {item.char}
              </td>
              <td className="px-2 py-2 text-ink-variant">{item.resolved}</td>
              <td className="px-2 py-2 text-ink-variant">
                {item.radical_char ? `${item.radical_char}（${item.radical_no}）` : '未收录'}
              </td>
              <td className="numeric px-2 py-2 text-ink">
                {item.radical_strokes === null || item.residual_strokes === null
                  ? '—'
                  : `${item.radical_strokes}+${item.residual_strokes}`}
              </td>
              <td className="numeric px-2 py-2 text-gold-bright">
                {item.kangxi_strokes ?? '未收录'}
              </td>
              <td className="px-2 py-2 text-ink-variant">
                {item.readings.length > 0
                  ? item.readings
                      .map((reading) => `${reading.pinyin}${reading.tone_number}`)
                      .join(' / ')
                  : '—'}
              </td>
              <td className="px-2 py-2 text-right">
                {item.stroke_source ? (
                  <SourceNote source={item.stroke_source} />
                ) : (
                  <span className="text-ink-muted">—</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
