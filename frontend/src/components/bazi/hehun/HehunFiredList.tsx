import { formatDelta } from '../../../lib/scoring';
import type { HehunFired } from '../../../types/baziHehun';

/** 五族的中文标题（§6.1 的分组名）。只作呈现，族序跟响应走。 */
const FAMILY_CAPTION: Record<string, string> = {
  relation: '关系',
  group: '合局',
  yongshen: '互济',
  nayin: '年命',
  palace: '婚姻宫',
};

/** 视角的短名，与四象限那两块的标题同一套词。 */
const DIRECTION_CAPTION: Record<string, string> = {
  male_to_female: '乾视坤',
  female_to_male: '坤视乾',
  mutual: '两造',
};

/**
 * 命中清单：账本逐行的可读镜像（spec §5.2、§6.2）。
 *
 * 一行 = 短名 + 视角徽 + 分值 + 判语。分值与展开的赋分账本是同一个数（同一份 `fired` /
 * `factors` 派生），这里不重算也不求和 —— 总分只由 `HehunScoreRing` 那一边印一次。
 *
 * `mutual` 也照常带徽：四族里每一条都是 `mutual`，藏起来会让"只有互济族有视角"这件事
 * 变成要读文档才知道的默契，而并排摆出来一眼就看得出哪几条是两向的（§6.2）。
 */
export function HehunFiredList({ rows }: { rows: HehunFired[] }) {
  if (rows.length === 0) {
    return <p className="text-sm text-ink-muted">两造之间未命中合婚规则表中的任何一条，账本只有基准一行。</p>;
  }

  const families: string[] = [];
  for (const row of rows) {
    if (!families.includes(row.family)) families.push(row.family);
  }

  return (
    <div className="flex flex-col gap-3">
      {families.map((family) => (
        <FamilyBlock key={family} family={family} rows={rows.filter((row) => row.family === family)} />
      ))}
    </div>
  );
}

function FamilyBlock({ family, rows }: { family: string; rows: HehunFired[] }) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="label-caps text-ink-muted">
        {FAMILY_CAPTION[family] ?? family} · {rows.length}条
      </span>
      <ul className="flex flex-col gap-1.5">
        {rows.map((row, index) => (
          <li
            key={`${row.rule}#${index}`}
            className="flex flex-wrap items-baseline gap-x-2 gap-y-1 rounded-element bg-[#0e111a] px-3 py-2 text-xs"
          >
            <span className="text-ink">{row.label}</span>
            <span className="label-caps text-ink-muted">{DIRECTION_CAPTION[row.direction] ?? row.direction}</span>
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
