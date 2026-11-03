import { annotateGenderTerms } from '../../../lib/gender';
import { useI18n } from '../../../i18n/context';
import { wuxingChip } from '../../../lib/wuxing';
import type {
  HehunComplement,
  HehunComplementCell,
  HehunComplementView,
  VigorEdge,
} from '../../../types/baziHehun';

/** 四象限的行（纵轴：这一行对**观看方**是喜是忌）。 */
const ROWS: ReadonlyArray<{ mine: 'favorable' | 'unfavorable'; caption: string }> = [
  { mine: 'favorable', caption: '我喜' },
  { mine: 'unfavorable', caption: '我忌' },
];

/** 四象限的列（横轴：**对方**盘里这一行的旺弱）。契约里没有「平」这一格。 */
const COLUMNS: ReadonlyArray<{ theirs: VigorEdge; caption: string }> = [
  { theirs: '旺', caption: '彼旺' },
  { theirs: '弱', caption: '彼弱' },
];

/**
 * 五行互补的四象限 × 两视角（spec §7.1）。
 *
 * 两张 2×2 并排：左「乾视坤」、右「坤视乾」。同一格在两张里说的是两种气 —— 同一个「金」
 * 可以一边是补（乾喜金、坤金旺）、一边是阙（坤喜金、乾金弱），两行不是双计（§6.2）。
 * 这个并排是那一裁定**唯一**能在页面上看出来的地方，所以两视角不折叠成一张。
 *
 * 格内的比值（`e.ratio.toFixed(4)`）逐字取自响应，页面不重算也不修约：§2.6 的四位读数
 * 是"被判定"与"被画出来"同一个数那条纪律的落点，页面再 `toFixed(2)` 就会把 0.7500 画成
 * 0.75 而读者以为后端判错了。单价 `cell.delta` 与账本里那条同数，也不重算。
 * 空格是「无」而不是缺格（§10.6）。
 */
export function HehunComplementChart({ complement }: { complement: HehunComplement }) {
  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
      {complement.views.map((view) => (
        <ViewBlock key={view.viewer} view={view} />
      ))}
    </div>
  );
}

function ViewBlock({ view }: { view: HehunComplementView }) {
  const { t } = useI18n();
  return (
    <div className="flex flex-col gap-2">
      <span className="label-caps text-gold">{annotateGenderTerms(view.label)}</span>
      <table className="w-full border-separate border-spacing-1 text-xs">
        <caption className="sr-only">{t('{{label}}的五行互补四象限', { label: annotateGenderTerms(view.label) })}</caption>
        <thead>
          <tr>
            <th scope="col" className="label-caps p-2 text-left font-normal text-ink-muted">
              ＼
            </th>
            {COLUMNS.map((column) => (
              <th key={column.theirs} scope="col" className="label-caps p-2 text-left font-normal text-ink-muted">
                {t(column.caption)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {ROWS.map((row) => (
            <tr key={row.mine}>
              <th scope="row" className="label-caps whitespace-nowrap p-2 text-left font-normal text-ink-variant">
                {t(row.caption)}
              </th>
              {COLUMNS.map((column) => (
                <td key={column.theirs} className="p-0 align-top">
                  <QuadrantCell
                    cell={view.cells.find(
                      (candidate) => candidate.mine === row.mine && candidate.theirs === column.theirs,
                    )}
                  />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function QuadrantCell({ cell }: { cell: HehunComplementCell | undefined }) {
  const { t } = useI18n();
  if (!cell) {
    // 契约恒 4 格；真缺了一格是后端违约，此时说得出缺的是哪一格，而不是画一个空格子。
    return <p className="px-3 py-2 text-xs text-wuxing-fire">{t('契约缺格')}</p>;
  }
  return (
    <div className="flex h-full flex-col gap-1.5 rounded-element bg-[var(--field-bg)] p-2.5">
      <div className="flex items-baseline justify-between gap-2">
        <span className="font-display text-sm text-ink">{cell.name}</span>
        <span className={`numeric ${cell.delta < 0 ? 'text-wuxing-fire' : 'text-wuxing-wood'}`}>
          {cell.delta < 0 ? `-${Math.abs(cell.delta).toFixed(1)}` : `+${cell.delta.toFixed(1)}`}
        </span>
      </div>
      {cell.elements.length === 0 ? (
        <span className="text-xs text-ink-muted">{t('无')}</span>
      ) : (
        <ul className="flex flex-wrap gap-1.5">
          {cell.elements.map((element) => (
            <li
              key={element.element}
              className={`rounded-element px-2 py-0.5 text-xs ${wuxingChip(element.element)}`}
            >
              {element.element}
              <span className="numeric ml-1 opacity-80">{element.ratio.toFixed(4)}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
