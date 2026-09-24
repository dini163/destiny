import type { LetterMapGroup, LetterValue, NumerologyInput } from '../../types/numerology';

interface LetterMapTableProps {
  /** 九列映射表，后端下发（spec §5.1）；本组件不携带任何字母常量。 */
  columns: readonly LetterMapGroup[];
  /** 姓名逐字透视，序即姓名里的出现序。 */
  letters: readonly LetterValue[];
  /** 回显块：计数与三个总和都由后端给出，此处只印不算。 */
  input: NumerologyInput;
}

/**
 * 毕达哥拉斯 1–9 字母映射表（九列）+ 姓名逐字透视条（spec §2.5、§8）。
 *
 * 九列的字母**一个都不在本文件里写死**：`columns` 由后端下发。A–Z 的映射是权威内容，
 * 后端已有 `LETTER_VALUES` 与 `VALUE_GROUPS` 两处并由语料测双向锁死，前端再抄一份就是
 * 第三处真相 —— 而三处一旦漂移，这张表会与同一屏上的逐字透视条自相矛盾，读者无从判断
 * 哪个才对。故本组件只做两件事：把九列摆出来，把姓名里的字母在表上点亮。
 *
 * 逐字透视条**不还原被跳过的字符位置**：后端给的是去重后的字符清单（决策 8：如实报数，
 * 不偷偷当 0），不是逐位标记，所以设计稿那种在词间插一个 `•` 的画法在这里画不出来 ——
 * 要画就得猜空格在第几位。宁可少一个装饰，也不印一个猜出来的位置。
 *
 * 宽表纪律（Global Constraints）：外层 `overflow-x-auto`、内层 `min-w-[40rem]`，
 * 九列在窄屏上横向滚动而不是挤成不可读的一条，与 `HehunPairMatrix` 同一套做法。
 */
export function LetterMapTable({ columns, letters, input }: LetterMapTableProps) {
  const inName = new Set(letters.map((letter) => letter.char));

  return (
    <div className="flex flex-col gap-4">
      <div className="overflow-x-auto">
        <div className="grid min-w-[40rem] grid-cols-9 gap-2">
          {columns.map((column) => (
            <div
              key={column.value}
              className="flex flex-col items-center gap-1 rounded-element border border-rim bg-[#0e111a] p-2"
            >
              <span className="numeric text-xl font-semibold text-gold-bright">{column.value}</span>
              <span aria-hidden="true" className="h-px w-6 bg-gold/25" />
              <ul className="flex flex-col items-center gap-0.5">
                {column.letters.map((char) => (
                  <li
                    key={char}
                    className={`numeric text-sm ${
                      inName.has(char) ? 'font-semibold text-gold' : 'text-ink-muted'
                    }`}
                  >
                    {char}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-2 rounded-card border border-rim bg-surface p-3">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <span className="label-caps text-gold">
            姓名逐字数理透视 · {input.full_name}
            {input.name_zh ? `（${input.name_zh}，仅回显）` : ''}
          </span>
          <span className="numeric text-xs text-ink-variant">
            共 {input.letter_count} 个字母计入
            {input.skipped_count > 0
              ? ` · 跳过 ${input.skipped_count} 个非字母字符（${input.skipped_chars.join(' ')}）`
              : ' · 无跳过字符'}
          </span>
        </div>

        <ul className="flex flex-wrap items-center gap-1.5">
          {letters.map((letter, index) => (
            // 同一个字母会在姓名里重复出现（`LU QINGXUAN` 有两个 U、两个 N），故 key 带序号。
            <li
              key={`${letter.char}#${index}`}
              className={`flex flex-col items-center rounded-element border px-2 py-1 ${
                letter.is_vowel
                  ? 'border-gold/40 bg-gold/10'
                  : 'border-rim bg-surface-raised'
              }`}
              title={letter.is_vowel ? '本次判定为元音' : '本次判定为辅音'}
            >
              <span className="numeric text-[11px] text-ink-muted">{letter.char}</span>
              <span
                className={`numeric text-sm font-semibold ${
                  letter.is_vowel ? 'text-gold-bright' : 'text-ink'
                }`}
              >
                {letter.value}
              </span>
            </li>
          ))}
        </ul>

        <p className="numeric text-[11px] leading-relaxed text-ink-muted">
          元音和 {input.vowel_total} + 辅音和 {input.consonant_total} = 全字母和
          {` ${input.letter_total}`}。
          <span className="ml-1 text-ink-variant">
            这三个是<strong className="text-ink">约简前的总和</strong>，不是那三个数本身 ——
            各自约简后才是灵魂冲动数、人格面具数与
            表达数，约简过程印在对应卡片的账本里，此处不重算。金色为本次判定下的元音；
            Y 的归属由输入台的开关决定，改动会让两个分和各移一笔而总和不动。
          </span>
        </p>
      </div>
    </div>
  );
}
