import { useI18n } from '../../../i18n/context';
import { GENDER_LABEL, GENDER_SHORT } from '../../../lib/gender';
import { pillarColumnLabel } from '../../../lib/pillars';
import type { HehunCell } from '../../../types/baziHehun';

/** 矩阵的枚举序，与后端 `POSITIONS` 同词（§2.4 的柱序）。 */
const POSITIONS = ['year', 'month', 'day', 'hour'] as const;

/**
 * 4×4 对冲矩阵（spec §2.4、§10.6）。
 *
 * 行是乾的四柱、列是坤的四柱，16 格恒在：格内没有跨造事实就是「无」，不是消失一格 ——
 * 一张缺格的矩阵读起来像"页面没渲染完"，而一张 16 格的矩阵读起来像"扫过了，这里没有"。
 * 取格按柱位对找而不按下标算，因为下标序是契约里的约定，一旦后端换了枚举序，页面会
 * 画出一张错位而完整的表 —— 那比空一格难查得多。
 *
 * (日, 日) 那一格标「婚姻宫」：它是 §2.9 三级归属的落点，读者要能看出宫位族那两行
 * 字是从哪一格来的。
 */
export function HehunPairMatrix({ cells }: { cells: HehunCell[] }) {
  const { t } = useI18n();
  const cellFor = (male: string, female: string): HehunCell | undefined =>
    cells.find((cell) => cell.male_position === male && cell.female_position === female);

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[46rem] border-separate border-spacing-1 text-xs">
        <caption className="sr-only">
          {t('{{male}}四柱对{{female}}四柱的跨造关系矩阵', { male: t(GENDER_LABEL.male), female: t(GENDER_LABEL.female) })}
        </caption>
        <thead>
          <tr>
            <th scope="col" className="label-caps p-2 text-left font-normal text-ink-muted">
              {t(GENDER_SHORT.male)} ＼ {t(GENDER_SHORT.female)}
            </th>
            {POSITIONS.map((position) => (
              <th key={position} scope="col" className="label-caps p-2 text-left font-normal text-ink-muted">
                {t(pillarColumnLabel(position))}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {POSITIONS.map((male) => (
            <tr key={male}>
              <th scope="row" className="label-caps whitespace-nowrap p-2 text-left font-normal text-gold">
                {t(pillarColumnLabel(male))}
                {male === 'day' ? <span className="ml-1 text-ink-muted">{t('· 婚姻宫在日柱一格')}</span> : null}
              </th>
              {POSITIONS.map((female) => {
                const cell = cellFor(male, female);
                const hits = cell?.hits ?? [];
                const palace = male === 'day' && female === 'day';
                return (
                  <td
                    key={female}
                    className={`align-top rounded-element p-2 ${
                      hits.length > 0 ? 'bg-surface-raised' : 'bg-[var(--field-bg)]'
                    } ${palace ? 'outline outline-1 outline-rim-strong' : ''}`}
                  >
                    {hits.length === 0 ? (
                      <span className="text-ink-muted">{t('无')}</span>
                    ) : (
                      <ul className="flex flex-col gap-1">
                        {hits.map((hit, index) => (
                          <li key={`${hit.rule}#${index}`} className="flex flex-wrap items-baseline gap-x-1.5">
                            <span className="text-ink">{t(hit.kind)}</span>
                            <span className="numeric text-ink-muted">
                              {hit.male_character} × {hit.female_character}
                            </span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
