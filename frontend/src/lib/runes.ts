/**
 * 北欧卢恩页面的**展示辅助**。
 *
 * 这里一个算术都没有，也一个配比都不重算（plan T6 Step 4）：`aett_balance` 后端已经
 * 数好了四行下发，页面照那四行画即可 —— 前端再数一遍，就会在「后端说两枚、页面画三格」
 * 时无人能判断谁对（与 `lib/numerology.ts` 不重算约简同一条纪律）。同理，正逆两面的
 * 释义取哪一面也是后端定的：`DrawnRune.keywords` / `meaning` 已经是**本次朝向的那一份**，
 * 前端只负责渲染，不做「如果是逆位就换成另一段」这类挑选。
 *
 * 所以下面这些函数做的全是**判**与**摆**：这一块石碑该不该转 180°、这块石上有没有刻痕、
 * 抽屉里哪些条目对得上检索词、以及把三组加那一枚单独成条的空白符摊平成一列。
 * （函数个数刻意不写进这段话：多一个函数就少一句真话 —— 数字命理 T7 的教训。）
 */

import type {
  CodexRune,
  DrawnRune,
  RuneCodex,
  RuneIdentity,
  RuneOrientation,
} from '../types/runes';

/** 朝向的中文标签与配色。 */
export interface RuneOrientationMeta {
  label: string;
  /** 走 inline `style` 而不是 Tailwind 工具类：颜色由数据决定，扫不到也无需扫到。 */
  color: string;
}

/**
 * 朝向 → 标签与配色。
 *
 * 两个色值与 `lib/tarot.ts` 的 `orientationMeta` 逐字相同（正位青、逆位绯）：两个神谕页
 * 摆在同一间观测台里，同一个概念换一种颜色就是让读者重学一遍。但**不 import 它** ——
 * 理由同后端 `content/rune_spreads.py` 刻意不 import `tarot_deck`：跨系统引用会把
 * 「塔罗改个名」升级成卢恩的破坏性变更，而两个颜色字面量不值得换这个耦合。
 */
export function orientationMeta(orientation: RuneOrientation): RuneOrientationMeta {
  return orientation === 'reversed'
    ? { label: '逆位', color: '#F43F5E' }
    : { label: '正位', color: '#2DD4BF' };
}

/**
 * 这一枚该不该把字形转 180°。
 *
 * 逆位（merkstave）的本义就是石碑上下颠倒，所以「转」不是装饰，是把朝向画出来 ——
 * 读者自己就能看出为什么对称符不可能有逆位。
 *
 * 条件里带上 `reversible` 并不是防后端：引擎结构上给不出「对称符 + 逆位」（只有
 * `allow_reversed and rune.reversible and not rune.is_wyrd` 三条都成立才去抽朝向）。
 * `tests/test_runes.py` 对此有两道测，强的一道不靠统计：它塞一个假 RNG 进去，断言对称符
 * 连 `choice` 都没被调用过（`choice_calls == 0`）—— 若哪天有人把守卫挪成「先抽朝向、
 * 输出前再过滤」，统计测毫无感觉，这道当场红。带上它是为了**让页面上两件事出自
 * 同一个字段**：石碑转不转，与对称符卡上印不印「此符对称，无逆位」（`reversible_note`），
 * 都读 `reversible`。只判 `orientation` 的话，这两处就能各自漂移，而漂出来的样子最难查 ——
 * 一个字形转了 180°，旁边一行字说它没有逆位。
 */
export function shouldRotate(stone: Pick<DrawnRune, 'reversible' | 'orientation'>): boolean {
  return stone.reversible && stone.orientation === 'reversed';
}

/**
 * 这块石上是不是没有刻痕可印。
 *
 * 两个条件问的其实是两件事：`is_wyrd` 是语义（这是那枚 1980 年代增补的空白符），
 * `glyph === ''` 是视觉（没有字形可渲染）。今天它们指的是同一枚 —— 空白符的 `glyph`
 * 就是空字符串，一块没有刻痕的石正是它该有的样子，`''` 在这里是有意义的值而不是缺失。
 * 写成析取是为了让调用处只需问一句「有没有字」，不必知道空白符是怎么被标出来的。
 *
 * 判成真的时候，`RuneStone` 渲染的是一块素石并标注现代增补，**不是**一个占位字符：
 * 设计稿给空白符印了 ᛭（U+16ED，官方名 RUNIC CROSS PUNCTUATION），那是标点不是字母，
 * 更不是「空白」（spec §2.3 修正 E）。
 */
export function isBlankStone(rune: Pick<RuneIdentity, 'is_wyrd' | 'glyph'>): boolean {
  return rune.is_wyrd || rune.glyph === '';
}

/**
 * 把全典摊平成一列：三组按序，末尾接上单独成条的空白符。
 *
 * 抽屉平时按三组分栏（8+8+8，Dagaz 在位），可检索框要的是跨组的一列结果。后端已经把
 * 组按 Kylver 序下发、组内也按序，所以摊平后仍是序位升序，末一项是空白符（序位 25，
 * 它不入任何一组，故 `RuneCodex` 里它跟 `aettir` 平级）。
 *
 * 全典恒为 25 条，**不随 `include_wyrd` 变** —— 那个开关管的是抽不抽得着空白符，
 * 不是它在不在典里（决策 25）。
 */
export function flattenCodex(codex: RuneCodex): readonly CodexRune[] {
  return [...codex.aettir.flatMap((group) => group.runes), codex.wyrd];
}

/**
 * 一条全典条目对不对得上检索词（spec §8：按名 / 音译 / 词义过滤）。
 *
 * 空检索词（含只有空白的）命中全部：抽屉打开时框里是空的，那一刻该看见的是整部典，
 * 而不是一片空白。大小写不敏感 —— 语料里 `name` 一律写成 `Fehu` 这种首字母大写的形式，
 * 读者打 `fehu` 也该命中。
 *
 * 搜的字段逐个列在下面而不是一句「所有字符串字段」，是为了让「将来多一个字段」变成一次
 * 显式决定：漏掉新字段，检索就会静默地搜不到它。
 *
 * 刻意**不**搜的四类，各有各的理由：
 * - `unicode_name`：24 个官方名一律以 `RUNIC LETTER` 开头，读者打一个 `r` 就命中整部典，
 *   过滤器随之失去分辨力。要核码位去出处卡，那里印的是 `codepoint` 与官方名的对照。
 * - `codepoint`：读者按名字找符文，不按十六进制找。
 * - `source`：同一张表的条目共用一句出处，命中即全命中，同上。
 * - `aett`：抽屉本来就按组分栏，检索框再按组过滤就是两套分组互相打架。
 *
 * 音译里的 þ 不必单独归一成 `th`：第三枚的 `name` 写作 `Thurisaz`，打 `th` 从名那一栏
 * 就命中了。
 */
export function codexMatches(rune: CodexRune, query: string): boolean {
  const needle = query.trim().toLowerCase();
  if (needle === '') return true;
  const fields: string[] = [
    rune.key,
    rune.name,
    rune.name_zh,
    rune.transliteration,
    rune.phoneme,
    rune.name_meaning,
    rune.upright_meaning,
    ...rune.upright_keywords,
  ];
  // 对称符没有逆位面，故这两项可空。空的意思是「没有这一面」，不是「匹配不上」——
  // 语料绝不给它们编一句逆位释义来凑满，这里也就不把 null 当成空字符串塞进去搜。
  if (rune.reversed_meaning !== null) fields.push(rune.reversed_meaning);
  if (rune.reversed_keywords !== null) fields.push(...rune.reversed_keywords);
  return fields.some((field) => field.toLowerCase().includes(needle));
}
