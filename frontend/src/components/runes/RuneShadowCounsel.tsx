import { ResultCard } from '../ui/ResultCard';
import { orientationMeta } from '../../lib/runes';
import type { ShadowNote } from '../../types/runes';

interface RuneShadowCounselProps {
  /** 一枚可逆符都没抽到时后端给 `null`。 */
  notes: ShadowNote[] | null;
}

/**
 * 阴影参照清单（spec §8、plan T7 Step 5；决策 17/23）。
 *
 * `null` 时**整块不渲染** —— 不是渲染一个「本次无阴影参照」的空卡。留一个空标题会让读者
 * 以为这一格本该有内容而这次没算出来；而「一枚可逆符都没抽到」本来就是这次铸石的一个正常
 * 结果，不值得为它开一块版面。
 *
 * 下面那个 `length === 0` 的分支并不是不信后端：`engines/runes.py` 的 `_shadow_counsel`
 * 收尾写的是 `return notes or None`，空列表在源头就被折成了 `None`，`[]` 到不了这里。写着它
 * 是为了让「后端哪天把 `or None` 去掉」不至于变成页面上一块有标题没内容的卡 —— 那正是本组件
 * 唯一要防的样子。
 *
 * 这一块**不是另算出来的凶兆**，只是把语料里本来就有的另一面摊开：`shadow_meaning` 与
 * `shadow_keywords` 逐字取自那枚符文的逆位条目，引擎没有为它写过一句话。所以每条都必带
 * `drawn_orientation`，并且把后端那句 `note` 逐字印出来 —— 那句话按本次朝向分两种写法
 * （正位时说「此条是它的反面参照，不是本次结果」，已抽到逆位时说「此条与卡面所读同文」），
 * 少了它，一段反面参照就会被读成对本次结果的第二次断言。
 */
export function RuneShadowCounsel({ notes }: RuneShadowCounselProps) {
  if (notes === null || notes.length === 0) return null;

  return (
    <ResultCard title="阴影参照" eyebrow="MERKSTAVE" icon="alert">
      <p className="text-xs leading-relaxed text-ink-muted">
        只列本次抽到的可逆符，逐条标明它是参照还是本次结果。八枚对称符与空白符没有另一面，
        故不在这里 —— 判据全文在碑阵底下。
      </p>

      <ul className="flex flex-col gap-3">
        {notes.map((note) => {
          const orientation = orientationMeta(note.drawn_orientation);
          return (
            <li
              key={`${note.position_key}:${note.key}`}
              className="flex flex-col gap-2.5 rounded-element border border-rim bg-surface p-4"
            >
              <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1.5">
                <span
                  aria-hidden="true"
                  className="font-display text-3xl leading-none text-gold-bright"
                >
                  {note.glyph}
                </span>
                <span className="font-display text-base text-ink">
                  {note.name} · {note.name_zh}
                </span>
                <span className="label-caps text-ink-muted">{note.position_label_zh}</span>
                <span
                  className="label-caps rounded-element px-1.5 py-0.5 font-semibold"
                  style={{ color: orientation.color, backgroundColor: `${orientation.color}1f` }}
                >
                  本次{orientation.label}
                </span>
              </div>

              {note.shadow_keywords.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {note.shadow_keywords.map((keyword) => (
                    <span
                      key={keyword}
                      className="label-caps rounded-element border border-rim bg-[#0e111a] px-1.5 py-0.5 text-ink-muted"
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
              ) : null}

              <p className="text-sm leading-relaxed text-ink-variant">{note.shadow_meaning}</p>

              <p className="rounded-element border border-rim-soft bg-[#0e111a] p-2.5 text-xs leading-relaxed text-ink-muted">
                {note.note}
              </p>
            </li>
          );
        })}
      </ul>
    </ResultCard>
  );
}
