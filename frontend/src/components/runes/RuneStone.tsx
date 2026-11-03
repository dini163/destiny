import { SourceNote } from '../ui/SourceNote';
import { isBlankStone, orientationMeta, shouldRotate } from '../../lib/runes';
import { useI18n } from '../../i18n/context';
import type { DrawnRune } from '../../types/runes';

interface RuneStoneProps {
  /** 落在这个位次上的那一枚。 */
  stone: DrawnRune;
}

/**
 * 一块石碑卡（spec §8、plan T7 Step 1）。保留设计稿的版式：大号字形 + 辉光 + 碑面底部
 * 一行序位与归属，碑下方接名义、要点、释义与位次说明。
 *
 * **碑面上一个数字都不印**（spec §11 偏差 G/H/I）：设计稿在每张卡底下摆了一行
 * 「要素：火/金复合 · 赋能度：94% · 司职：弗蕾亚」，三项互不成体系、五个百分比零个有
 * 权威定义，而符文与元素的对应根本没有单一权威。删掉它们腾出来的位置给了两样有据的：
 * `name_meaning`（原始日耳曼语构拟词义，`name_meaning_uncertain` 为真时另加标记）与
 * `position_meaning`（这一位次读什么，出自牌阵语料）。
 *
 * 三处刻意分开写、别合并：
 *
 * - **逆位就把字形转 180°**。这是 merkstave 的本义（石碑掷出时上下颠倒），不是装饰 ——
 *   转了读者才自己看得出为什么对称符不可能有逆位。转不转由 `shouldRotate` 判，与碑上那枚
 *   「此符对称，无逆位」的角标读同一个 `reversible` 字段，故两者不可能自相矛盾。
 * - **对称符不印朝向角标**。它恒为正位，印一个「正位」会让读者以为还有另一种可能；
 *   改印「此符对称，无逆位」，判据全文（`reversible_note`）由 `RuneStoneGrid` 印一次。
 * - **空白符另是一路**。它 `reversible` 也是 false，但它不是「对称」—— 它压根没有字形。
 *   给它印「此符对称」就是一句假话，故 `is_wyrd` 先判、单独印「空白石 · 现代增补」，
 *   碑面渲染成一块素石（`isBlankStone`），**不印任何字符**：设计稿给它印了 ᛭ U+16ED，
 *   那枚的 Unicode 官方名是 RUNIC CROSS PUNCTUATION，是标点不是字母，更不是「空白」。
 *
 * 字形之外冗余印出 `name` / `name_zh` / `transliteration`（spec §11 残余风险 5）：Runic
 * 区块（U+16A0–U+16FF）不在多数字体里，缺字体时碑面上是一个豆腐块，而那一刻读者手上
 * 剩下的只有这三个字段能告诉他这一块是什么。字形 `aria-hidden`，无障碍也靠它们。
 *
 * 位次序用 `01` 这样的两位阿拉伯数字，不学设计稿的罗马数字：那要一个 `romanNumeral`，
 * 而本仓只有 `lib/tarot.ts` 里有 —— 为了两个装饰性数字去 import 另一个系统的 lib，
 * 与 `orientationMeta` 不复用塔罗那一份是同一条理由。
 */
export function RuneStone({ stone }: RuneStoneProps) {
  const { t } = useI18n();
  const blank = isBlankStone(stone);
  const rotate = shouldRotate(stone);
  const orientation = orientationMeta(stone.orientation);

  return (
    <article className="group relative flex flex-col gap-4 overflow-hidden rounded-card border border-rim bg-surface-raised/70 p-4 backdrop-blur-xl sm:p-5">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-10 -top-10 h-32 w-32 rounded-full bg-gold/10 blur-2xl transition-colors group-hover:bg-gold/20"
      />

      <header className="relative flex flex-wrap items-center justify-between gap-2">
        <span className="flex items-center gap-2">
          <span aria-hidden="true" className="h-2 w-2 shrink-0 rounded-full bg-gold" />
          <span className="numeric text-[11px] font-semibold tracking-widest text-gold-soft">
            {String(stone.position_index + 1).padStart(2, '0')}
          </span>
          <span className="text-sm font-medium text-ink">{stone.position_label_zh}</span>
        </span>
        <span className="label-caps rounded-element border border-rim bg-[var(--field-bg)] px-2 py-0.5 text-ink-muted">
          {stone.position_label}
        </span>
      </header>

      <div className="relative flex justify-center py-1">
        <div
          className="relative flex h-52 w-40 shrink-0 flex-col items-center justify-center rounded-card bg-[#0c0e14] transition-transform duration-500 group-hover:scale-[1.03]"
          style={{
            boxShadow:
              '0 14px 34px -14px rgba(0,0,0,0.92), inset 0 1px 0 rgba(245,215,127,0.14)',
          }}
        >
          {blank ? (
            <span className="flex h-24 w-24 items-center justify-center rounded-full border border-dashed border-rim-strong">
              <span className="label-caps px-2 text-center text-[10px] leading-tight text-ink-muted">
                {t('无刻痕')}
              </span>
            </span>
          ) : (
            <span
              aria-hidden="true"
              className={`select-none text-[74px] leading-none text-gold-bright transition-transform duration-500 ${
                rotate ? 'rotate-180' : ''
              }`}
              style={{ filter: 'drop-shadow(0 0 16px rgba(242,202,80,0.55))' }}
            >
              {stone.glyph}
            </span>
          )}

          <span className="numeric mt-2 text-[11px] tracking-[0.16em] text-ink-muted">
            {blank ? t('WYRD · 现代增补') : `${stone.name.toUpperCase()} · ${orientation.label}`}
          </span>

          <div className="absolute inset-x-3 bottom-2 flex items-center justify-between gap-2">
            <span className="label-caps truncate text-[10px] text-ink-muted">
              {stone.aett_zh ?? t('不入三组')}
            </span>
            <span className="numeric shrink-0 text-[10px] text-ink-muted">
              #{String(stone.order).padStart(2, '0')} · {stone.name_zh}
            </span>
          </div>
        </div>
      </div>

      <div className="relative flex flex-col gap-2">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="font-display text-base font-semibold text-ink">
            {blank ? null : (
              <span aria-hidden="true" className="mr-1.5 text-gold-bright">
                {stone.glyph}
              </span>
            )}
            {stone.name} · {stone.name_zh}
            <span className="numeric ml-1.5 text-xs font-normal tracking-widest text-ink-muted">
              {stone.transliteration === '' ? t('无音译') : stone.transliteration}
            </span>
          </h3>
          {stone.is_wyrd ? (
            <span className="label-caps rounded-element border border-arcane/40 bg-arcane/10 px-1.5 py-0.5 text-[#c7cbff]">
              {t('空白石 · 现代增补')}
            </span>
          ) : stone.reversible ? (
            <span
              className="label-caps rounded-element px-1.5 py-0.5 font-semibold"
              style={{ color: orientation.color, backgroundColor: `${orientation.color}1f` }}
            >
              {orientation.label}
            </span>
          ) : (
            <span className="label-caps rounded-element border border-rim bg-surface px-1.5 py-0.5 text-ink-muted">
              {t('此符对称，无逆位')}
            </span>
          )}
        </div>

        <p className="text-xs leading-relaxed text-ink-variant">
          <span className="label-caps mr-1.5 text-ink-muted">{t('名义')}</span>
          {stone.name_meaning}
          {stone.name_meaning_uncertain ? (
            <span className="label-caps ml-1.5 rounded-element border border-gold/40 bg-gold/10 px-1.5 py-0.5 text-gold-soft">
              {t('名义不确定')}
            </span>
          ) : null}
        </p>

        {stone.keywords.length > 0 ? (
          <ul className="flex flex-wrap gap-1.5">
            {stone.keywords.map((keyword) => (
              <li
                key={keyword}
                className="rounded-element border border-rim bg-surface px-1.5 py-0.5 text-[11px] text-ink-variant"
              >
                {keyword}
              </li>
            ))}
          </ul>
        ) : null}

        <p className="text-sm leading-relaxed text-ink">{stone.meaning}</p>

        <p className="rounded-element border border-rim bg-[var(--field-bg)] p-2.5 text-xs leading-relaxed text-ink-muted">
          <span className="label-caps mr-1.5 text-gold-soft">{t('位次')}</span>
          {stone.position_meaning}
        </p>
      </div>

      <div className="relative mt-auto pt-1">
        <SourceNote source={stone.source} />
      </div>
    </article>
  );
}
