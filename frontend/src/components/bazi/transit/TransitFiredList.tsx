import { formatDelta } from '../../../lib/scoring';
import type { TransitFired } from '../../../types/baziTransit';

/**
 * 九族的中文标题（spec §6.2 的分组名）。
 *
 * 只作呈现：分组顺序与组内顺序都跟响应走，前端不重排族序也不重排行序 —— 账本序就是
 * 规则表序，重排会让页面与展开的赋分账本对不上。未收入此表的族按机器键原样呈现，
 * 新增一族时页面照常可用，只是标题还是键名。
 */
const FAMILY_CAPTION: Record<string, string> = {
  yongshen: '喜忌',
  taisui: '太岁',
  palace: '宫位',
  heyue: '合局',
  ganzhi: '干支',
  fuyin: '伏吟反吟',
  dayun: '大运',
  dishi: '地势',
  shensha: '神煞',
};

/**
 * 命中行按族分组的断语清单。
 *
 * 一行 = 短名 + 分值 + 判语。分值与 `ScoreLedger` 展开后的账本行是同一个数（同一份
 * `fired` / `factors` 派生），这里不重算、不求和 —— 总分只由 `ScoreLedger` 印一次。
 * 月段行的短名自带「（流月）」后缀，与年段行同组并列时可分辨。
 */
export function TransitFiredList({ rows }: { rows: TransitFired[] }) {
  if (rows.length === 0) {
    // 如实说明"查过了、没命中"，而不是留白让人以为是渲染坏了。
    return <p className="text-sm text-ink-muted">此岁未命中岁运规则表中的任何一条，账本只有基准一行。</p>;
  }

  const families: string[] = [];
  for (const row of rows) if (!families.includes(row.family)) families.push(row.family);

  return (
    <div className="flex flex-col gap-3">
      {families.map((family) => (
        <FamilyBlock
          key={family}
          family={family}
          rows={rows.filter((row) => row.family === family)}
        />
      ))}
    </div>
  );
}

/** One family: its caption and hit count, then its rows. */
function FamilyBlock({ family, rows }: { family: string; rows: TransitFired[] }) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="label-caps text-ink-muted">
        {FAMILY_CAPTION[family] ?? family} · {rows.length}条
      </span>
      <ul className="flex flex-col gap-1.5">
        {rows.map((row) => (
          <li
            key={row.key}
            className="flex flex-wrap items-baseline gap-x-2 gap-y-1 rounded-element bg-[#0e111a] px-3 py-2 text-xs"
          >
            <span className="text-ink">{row.label}</span>
            <span className={`numeric ${row.delta < 0 ? 'text-wuxing-fire' : 'text-wuxing-wood'}`}>
              {formatDelta(row.delta)}
            </span>
            <span className="w-full text-ink-variant sm:w-auto sm:max-w-2xl">{row.reading}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
