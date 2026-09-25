/**
 * 北欧卢恩契约，镜像 `backend/app/schemas/runes.py`。
 *
 * 字段一律 snake_case、与 JSON 逐字相同 —— 多一层映射就又多一份真相（同
 * `types/numerology.ts` 的口径）。本契约有四条**否定性**纪律，读代码时别顺手加回来：
 *
 * ① **没有 `score`，也没有任何百分比**（决策 6/7）。设计稿在这一页印了五个百分比，
 *    而卢恩铸石不吃出生时间与地点，没有任何输入可以推出那类数字。后端
 *    `tests/test_runes_api.py` 递归扫整棵响应树守这条，前端类型里也不该长出来。
 * ② **没有元素、守护神与「时机窗口」字段**（决策 6/8/10）。设计稿那三套元素归属
 *    彼此矛盾，春分窗口也无从推导。
 * ③ **前端不重算任何配比**（plan T6 Step 4）。`aett_balance` 直接渲染后端下发的那四行；
 *    前端再数一遍，就会在「后端说两枚、页面画三格」时无人能判断谁对。
 * ④ **`shadow_counsel` 是 `null` 而不是 `[]`**（决策 17/23）。一枚可逆符都没抽到时
 *    整块不渲染，而不是留一个空标题。故类型必须带 `| null`，页面据此判空。
 *
 * 三类 nullability 刻意分开，别在页面里「顺手补一个空字符串」：
 *
 * - **入参**：`question` 是 Optional 故写 `?: string | null`；`include_wyrd` 与
 *   `allow_reversed` 是「非 Optional + 有默认值」，交 `null` 会吃 pydantic 的 422，
 *   所以只写 `?: boolean` —— 缺省就是**不写那个键**。
 * - **结构性可空**：`aett` / `aett_zh` / `codepoint` / `unicode_name` 只对空白符为 null
 *   （它不入三组、也没有字形可查）；`reversed_keywords` / `reversed_meaning` 只对八枚
 *   对称符为 null（旋转 180° 后与原形重合，故没有逆位读法，也不给它编一段）。
 * - **空即空值，不是 null**：`keywords`、`upright_keywords`、`shadow_keywords`、
 *   `drawn_keys`、`tables`。而空白符的 `glyph` 是**空字符串**：一块没有刻痕的石就是它
 *   的正确视觉，`''` 在这里是有意义的值而不是缺失。
 *
 * 唯一合法的 `0` 是 `AettCount.count`：某一组这次一枚都没落到时 0 是真实值，那一行照样
 * 下发 —— 少一行会让「没落到」与「引擎忘了算这一组」在页面上长得一样。
 *
 * 键域收窄成联合类型是照 `types/numerology.ts` 的先例：后端那几处声明为 `str` 并把取值
 * 写在 `description` 里，前端按同一份闭集收窄，页面 `switch` 才能穷尽。
 */

import type { ProvenanceTable } from './common';

/** 三种牌阵：单枚 · 诺伦三女神 · 卢恩十字。 */
export type RuneSpreadId = 'single' | 'three' | 'five';

/** 朝向。对称符与空白符恒为 `upright`，后端结构上给不出另一种。 */
export type RuneOrientation = 'upright' | 'reversed';

/** 三组（ætt）的键。分组是传统的，但 ætt 这个称呼与三个名字都是近代且各家不一。 */
export type RuneAett = 'freyja' | 'heimdall' | 'tyr';

/**
 * `aett_balance` 四行的键：三组之外多一个 `wyrd` 桶。
 *
 * 它**不是**第四组。空白符 `aett` 为 null，可抽到的枚数总得有个去处，否则「三组之和
 * 加空白符等于抽到枚数」这条会计等式在开着开关时就不成立。故这里比 `RuneAett` 宽一格，
 * 而 `RuneIdentity.aett` 仍只有三值可空 —— 两个类型分开写，正是为了把这条差别留在类型上。
 */
export type AettBalanceKey = RuneAett | 'wyrd';

/**
 * 一枚符文的身份字段：抽到的那一份与全典里的那一份共用。
 *
 * 继承而非两处各列一遍，理由同 `types/baziLiuri.ts`：同一枚符文的两组事实不该能漂移。
 */
export interface RuneIdentity {
  /** Kylver 序位 1–24；空白符为 25。 */
  order: number;
  key: string;
  /** 符文那一个字符；空白符为 `''`（一块没有刻痕的石）。 */
  glyph: string;
  name: string;
  name_zh: string;
  /** 音译。第三枚是 thorn（þ）而不是 `th`，故前六枚连读是 `fuþark` 六个字母。 */
  transliteration: string;
  /** 原始日耳曼语构拟的名义。`name_meaning_uncertain` 为真时页面须一并标出。 */
  name_meaning: string;
  name_meaning_uncertain: boolean;
  /** 空白符为 null：它不入任何一组。 */
  aett: RuneAett | null;
  aett_zh: string | null;
  /** 八枚旋转对称符为 false：它们没有逆位读法。 */
  reversible: boolean;
  /** 只有空白符为 true。 */
  is_wyrd: boolean;
  /** 条目级出处。`SourceNote` 印第一个全角左括号之前那一段作角标。 */
  source: string;
}

/** 抽进某个位次的一枚符文。 */
export interface DrawnRune extends RuneIdentity {
  /** 该位次在这一阵里的零起序。 */
  position_index: number;
  position_key: string;
  position_label: string;
  position_label_zh: string;
  /** 这个位次揭示什么。 */
  position_meaning: string;
  orientation: RuneOrientation;
  /** **按本次朝向取用后的那一份**关键词，不是两面都给。 */
  keywords: string[];
  /** 同上，本次朝向的释义。想看另一面去 `shadow_counsel`，那里明说是反面参照。 */
  meaning: string;
}

/** 一组在本次铸石里的实际枚数。四行恒在，`count` 为 0 也照列。 */
export interface AettCount {
  key: AettBalanceKey;
  name: string;
  name_zh: string;
  count: number;
}

/**
 * 一条阴影参照（决策 17）。
 *
 * 这**不是**另算出来的凶兆，只是把语料里本来就有的另一面摊开给读者看。故
 * `drawn_orientation` 必须在场：少了它，读者会把一段反面参照误读成对本次结果的断言。
 */
export interface ShadowNote {
  key: string;
  name: string;
  name_zh: string;
  glyph: string;
  /** 这枚落在哪个位次。 */
  position_key: string;
  position_label_zh: string;
  /** 本次实际给出的朝向。 */
  drawn_orientation: RuneOrientation;
  shadow_keywords: string[];
  shadow_meaning: string;
  /** 明说这是反面参照、不是本次结果的那句话。 */
  note: string;
}

/**
 * 全典抽屉里的一枚：参考资料，不是本次结果。
 *
 * 比 `DrawnRune` 多三样 —— 码位与 Unicode 官方名（出处卡要印「码位锚点」：字形对错
 * 不靠肉眼，读者可以自己拿这两个字段核），以及正逆**两面都带齐**（抽屉是查阅用的，
 * 只带一面就没法当参考）。
 */
export interface CodexRune extends RuneIdentity {
  /** Unicode 码位；空白符为 null（它没有字形）。 */
  codepoint: number | null;
  /** Unicode 官方字符名；空白符为 null。 */
  unicode_name: string | null;
  /** 音值，或一句「这一块没有音」的说明。 */
  phoneme: string;
  upright_keywords: string[];
  /** 八枚对称符为 null。 */
  reversed_keywords: string[] | null;
  upright_meaning: string;
  /** 八枚对称符为 null。 */
  reversed_meaning: string | null;
}

/** 抽屉里的一组。`naming_note` 一并下发：ætt 这个称呼与三组的名字都是近代且各家不一。 */
export interface AettGroup {
  key: RuneAett;
  name: string;
  name_zh: string;
  /** 这一组讲什么的现代解读，不是古文献教义。 */
  theme: string;
  naming_note: string;
  runes: CodexRune[];
}

/**
 * 全典（决策 25）。恒为 25 条，**不随 `include_wyrd` 变**：那个开关管的是抽不抽得着
 * 空白符，不是它在不在典里。抽屉里空白符恒单独成条并标注现代增补。
 */
export interface RuneCodex {
  /** 三组，每组八枚。 */
  aettir: AettGroup[];
  /** 恒在，且它的 `source` 恒标出现代增补。 */
  wyrd: CodexRune;
  total: number;
}

/** 出处卡的数据。每一条都是读者可以拿去核对的，没有一条是装饰。 */
export interface RuneProvenance {
  /** 熵源名，如实为 `secrets`（决策 19）。 */
  rng: string;
  rng_note: string;
  engine: string;
  engine_note: string;
  /** 只印方法标识；设计稿那串流水号无从推导，故没有（决策 18）。 */
  badge: string;
  /** 24，或开着空白符时 25。 */
  deck_size: number;
  /** 本端点真读的那两张表。 */
  tables: ProvenanceTable[];
  /** 抽法口径：牌组、不放回、180° 判据。下发是为了让读者能核对结果。 */
  method: string;
  naming_note: string;
  wyrd_note: string;
  /**
   * 两处真实凭据（Kylver 石碑与 Codex Regius），以及设计稿那两条假声明为何不印。
   * 这一段同时承担「说了什么」与「刻意没说什么」，后者同样是事实。
   */
  manuscript_note: string;
}

/** 一次铸石的入参。 */
export interface RuneCastRequest {
  /** 缺省 `three`（诺伦三女神）。 */
  spread_id?: RuneSpreadId;
  /**
   * 空白符是否入牌组，缺省**关**（决策 3）：它是 1980 年代的商业增补，默认打开等于
   * 默认按现代牌组而不是 Elder Futhark 起卦。
   */
  include_wyrd?: boolean;
  /** 是否允许逆位（merkstave）。对称符无论怎么设都恒正位。 */
  allow_reversed?: boolean;
  /** 所问，上限 120 字；只用于回显与领起直读。 */
  question?: string | null;
}

/** 完整响应。**没有 `score`，也没有任何百分比字段**（决策 6、7）。 */
export interface RuneCastResponse {
  spread_id: RuneSpreadId;
  spread_name: string;
  spread_name_zh: string;
  spread_description: string;
  /** 未附所问时为 null。 */
  question: string | null;

  /** 按牌阵位次序。 */
  stones: DrawnRune[];
  /** 与 `stones` 同序；元素互异（不放回抽取）。 */
  drawn_keys: string[];
  allow_reversed: boolean;
  include_wyrd: boolean;

  /** 四行：三组加空白符桶。是**计数**，不是评分（决策 16）。 */
  aett_balance: AettCount[];
  /** 只由语料文案拼成，不会提到没抽到的符文。 */
  synthesis: string;
  /** 一枚可逆符都没抽到时为 null，整块不渲染（决策 17/23）。 */
  shadow_counsel: ShadowNote[] | null;
  /** 180° 判据的文案，印出来供读者自己核。 */
  reversible_note: string;

  codex: RuneCodex;
  provenance: RuneProvenance;
}
