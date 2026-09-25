/**
 * 数字命理页面的**展示辅助**。
 *
 * 这里刻意一个算术都没有（plan T6 Step 4、Global Constraints）：约简只有一个入口，
 * 在后端 `app/engines/numerology.py::reduce_number`。前端拿到的每个数都已带自己的
 * `steps` 账本，页面直接渲染即可 —— 一旦前端再算一遍，同一个「11 月」就可能在两处
 * 一处显示 11、一处显示 2，读者无从判断哪个才对（这正是后端 `Challenge` 不带 `steps`
 * 的同一条理由）。
 *
 * 所以下面这些函数做的全是**选**、**摆**与**排版**：从后端已经算好的数组里挑出当前
 * 那一段、把 1..9 升序的九宫按后端下发的洛书摆法排成三行、把主数拆成大小两号字、
 * 把年龄轴拼成一句人话、把看不见的字符换成看得见的写法。没有一个函数会改变任何
 * 数值。（函数个数刻意不写进这段话：多一个函数就少一句真话。）
 */

import type { GridCell, PersonalCycle, PersonalCycles, Pinnacle } from '../types/numerology';

/** 主数的双数字版式拆件。 */
export interface MasterPair {
  /** 大字：主数就是它自己（`11`），非主数即该数（`6`）。 */
  primary: string;
  /** 小字后缀 `/2`；**非主数为 null** —— 印 `6 /6` 是废字，设计稿也只在主数上印。 */
  rootSuffix: string | null;
}

/**
 * 把「值 + 根」拆成设计稿那个双数字版式（`11` 大号 + `/2` 小号）。
 *
 * `value` 为 null 时返回 null（决策 17）：算不出的核心数由卡片改印
 * `unavailable_reason`，而不是印个 0 或空字符串充数。
 */
export function masterPair(
  value: number | null,
  root: number | null,
  isMaster: boolean,
): MasterPair | null {
  if (value === null) return null;
  // 非主数的 `root` 恒等于 `value`（都已约到 1–9），故只有主数才需要后缀。
  if (!isMaster || root === null) return { primary: String(value), rootSuffix: null };
  return { primary: String(value), rootSuffix: `/${root}` };
}

/**
 * 挑出当前所在的那一程顶峰。
 *
 * `is_current` 由后端按 `reference_date` 判（前端没有"今天"的权威口径，也不该有），
 * 这里只是 `find`。第四顶峰 `end_age` 为 null，故基准日再晚也落得进去。
 * 一段都落不到时返回 null —— 那说明基准日早于出生，页面据此不画高亮，而不是硬挑第一段。
 */
export function currentPinnacle(pinnacles: readonly Pinnacle[]): Pinnacle | null {
  return pinnacles.find((item) => item.is_current) ?? null;
}

/**
 * 把 1..9 升序的 `cells` 按后端下发的 `layout` 摆成三行三列。
 *
 * 摆法必须来自后端（决策 12）：真洛书是 `4 9 2 / 3 5 7 / 8 1 6`，八平面正定义在它的
 * 三行三列两对角线上；前端自己按数字升序排就会排出设计稿那个行和 18/15/12 的**非幻方**
 * 摆法，「意志之箭」随之变成三个不相干的数字。
 *
 * 格位是 `GridCell | undefined`：后端保证 `cells` 覆盖 1..9 且 `layout` 是它的一个排列
 * （两边都有测钉住），所以正常恒不 undefined。留这个口子而不是断言非空，是为了跨 HTTP
 * 边界时**看得见**契约破裂 —— 渲染处印一个占位符，好过静默画出一格空白让人以为"这格没数"。
 */
export function arrangeGrid(
  cells: readonly GridCell[],
  layout: readonly (readonly number[])[],
): (GridCell | undefined)[][] {
  const byDigit = new Map(cells.map((cell) => [cell.digit, cell]));
  return layout.map((row) => row.map((digit) => byDigit.get(digit)));
}

/**
 * 一程顶峰的年龄轴文案，如 `0 - 30 岁`；第四顶峰无终点故为 `49 岁起`。
 *
 * `end_age` 为 null 时不填 999 之类的假值（spec §6.3），文案也跟着换成开口式。
 */
export function pinnacleAgeLabel(pinnacle: Pinnacle): string {
  return pinnacle.end_age === null
    ? `${pinnacle.start_age} 岁起`
    : `${pinnacle.start_age} - ${pinnacle.end_age} 岁`;
}

/**
 * 个人流年的三轮（前一年 / 今年 / 后一年），序即阅读序。
 *
 * 后端把三轮平铺成 `PersonalCycles` 的具名字段，页面要的是"今年居中"的一排，
 * 这里只做挑选与排序，不碰 `month` / `day` 那两项。
 */
export function yearRounds(cycles: PersonalCycles): readonly PersonalCycle[] {
  return [cycles.previous_year, cycles.year, cycles.next_year];
}

/** 看不见的那些字符：分隔符（空格、不换行空格、全角空格）、格式符（零宽空格、
 * BOM、零宽连接符）与控制符（制表、换行）。用 Unicode 分类而不是枚举字面量：
 * 枚举永远漏下一个，而漏掉的那个正好也是看不见的 —— 它不会报错，只会静静地
 * 把括号里留白。 */
const NO_GLYPH = /^[\p{Z}\p{Cf}\p{Cc}]$/u;

/**
 * 被跳过字符的**可见**写法。
 *
 * 后端如实报出参与不了计算的字符（决策 8），可「如实报」不等于「报得出来」：主角
 * `LU QINGXUAN` 被跳过的正是名字中间那个空格，直接印就是「（去重后： ）」——
 * 括号里一片空白，看上去像渲染坏了。而这一格恰恰是最该被看见的：它是「为何字母数
 * 比字符数少」的唯一凭据，印成空白就等于把凭据收了回去。故看不见的字符一律改印
 * 码位（读者能自己核），其余原样印出。
 */
export function skippedCharLabel(char: string): string {
  if (!NO_GLYPH.test(char)) return char;
  const code = char.codePointAt(0)?.toString(16).toUpperCase().padStart(4, '0');
  return code === undefined ? '空白字符' : `空白 U+${code}`;
}

/**
 * 一整串被跳过字符的写法，用「、」分隔。
 *
 * 分隔符不能是空格：`[' '].join(' ')` 印出来还是一个空格，正是 `skippedCharLabel`
 * 要治的那个病；两个字符时 `['-', ' '].join(' ')` 更是分不清谁是谁。
 */
export function skippedCharsLabel(chars: readonly string[]): string {
  return chars.map(skippedCharLabel).join('、');
}
