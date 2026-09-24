/**
 * 毕达哥拉斯数字命理契约，镜像 `backend/app/schemas/numerology.py`。
 *
 * 字段一律 snake_case、与 JSON 逐字相同 —— 多一层映射就又多一份真相（同
 * `types/baziHehun.ts` 的口径）。本契约有三条**否定性**纪律，读代码时别顺手加回来：
 *
 * ① **没有 `score`**（决策 14）。毕达哥拉斯数理没有权威的吉凶总分传统，硬凑一个加权分
 *    等于让系统声称有人替它赋过分。后端 `tests/test_numerology_api.py` 递归扫整个响应
 *    守这条，前端类型里也不该长出任何总分字段。
 * ② **没有任何百分比**（决策 13）。设计稿印的「能量分布均衡度 82%」无权威定义，不实现。
 * ③ **前端不重算任何算术**（决策 5）。约简只有一个入口，在后端；`steps` 是账本，
 *    页面直接渲染它。所以本文件里没有一个函数，`lib/numerology.ts` 也只做展示辅助。
 *
 * 三类 nullability 刻意分开，别在页面里"顺手补一个 0"：
 *
 * - **入参**：`name_zh` / `reference_date` 是「Optional + 默认 None」故写 `| null`；
 *   `y_as_vowel` 是「非 Optional + 默认 False」，交 `null` 会吃 pydantic 的
 *   `{"detail": [...]}` 422，所以只写 `?: boolean` —— 缺省就是**不写那个键**。
 * - **结构性可空**（响应侧）：`CoreNumber` 的 `value`/`root`/`meaning` 等（总和为 0 时
 *   整卡留空，决策 17）、`Pinnacle.end_age`（第四顶峰无终点，不填 999 之类假值）、
 *   `NumerologyInput.age_at_reference`（基准日早于生日时为 null，不填负数或 0）。
 * - **空即空列表，不是 null**：`steps`、`keywords`、`karmic_debts`、`tokens`、
 *   `karmic_lessons`、`missing`、`digits`、`skipped_chars`。"查过了、没有"是结论，
 *   页面据此画出「无」。
 *
 * 唯一合法的 `0` 有两处，都是值域的真实成员而不是缺失：`Challenge.value`（月日年约简后
 * 同值时四挑战必然全 0）与 `GridCell.count`（姓名九宫里 0 次本身就是业力课）。
 *
 * 键域收窄成联合类型是照 `types/name.ts:NameGridKey` 的先例：后端那几处声明为 `str`
 * 并把取值写在 `description` 里，前端按同一份闭集收窄，页面 `switch` 才能穷尽。
 */

import type { ProvenanceTable } from './common';

/** 六个核心数的固定序（后端保证，前端不再排序）。 */
export type CoreNumberKey =
  | 'life_path'
  | 'expression'
  | 'soul_urge'
  | 'personality'
  | 'birthday'
  | 'maturity';

/** 四程顶峰。 */
export type PinnacleKey = 'first' | 'second' | 'third' | 'fourth';

/** 四挑战。`main` 即贯穿一生的主挑战，故与顶峰的 `third` 不同名。 */
export type ChallengeKey = 'first' | 'second' | 'main' | 'fourth';

/** 个人周期的五个键：流年三轮 + 流月 + 流日。 */
export type PersonalCycleKey = 'previous_year' | 'year' | 'next_year' | 'month' | 'day';

/** 洛书八平面（决策 12：构成数字恒为真洛书的一条线）。 */
export type LoshuPlaneKey =
  | 'mental'
  | 'emotional'
  | 'practical'
  | 'thought'
  | 'will'
  | 'action'
  | 'silver_yog'
  | 'golden_yog';

/** 约简账本的一行。`expression` 是读者能照着按计算器的那一串。 */
export interface ReductionStep {
  /** 这一行算的是什么：年 / 月 / 日 / 元音 / 辅音 / 相加 … */
  label: string;
  expression: string;
  /** 该算式的和，如约简前的 23。 */
  total: number;
  /** 约简结果；主数原样保留（挑战链除外）。 */
  reduced: number;
  /** `total` 是否落在 13/14/16/19 上；只在生命灵数链上判（spec §6.8）。 */
  karmic_debt: boolean;
}

/** 姓名逐字透视的一格。 */
export interface LetterValue {
  /** 大写归一后的字母。 */
  char: string;
  value: number;
  /** 按本次 `y_as_vowel` 判定；决定它进元音和还是辅音和。 */
  is_vowel: boolean;
}

/** 一个核心数，连同释义与完整约简账本。 */
export interface CoreNumber {
  key: CoreNumberKey;
  /** 中英双名，如「生命灵数 Life Path」。 */
  label: string;
  /** 主数原样保留（11 就是 11，不写成 2）；算不出时为 null（决策 17）。 */
  value: number | null;
  /** 数字根，永远是个位数；页面按 `value /root` 双数字版式渲染。 */
  root: number | null;
  is_master: boolean;
  master_title: string | null;
  meaning: string | null;
  keywords: string[];
  talent: string | null;
  challenge: string | null;
  /** 仅当 `value` 为 null 时有值：说清为什么算不出，而不是静默少一张卡。 */
  unavailable_reason: string | null;
  steps: ReductionStep[];
  source: string;
}

/** 生命灵数约简途中撞上的一个业力债数（13/14/16/19）。 */
export interface KarmicDebt {
  number: number;
  /** 它出现在哪一步，如「相加」。 */
  label: string;
  expression: string;
  meaning: string;
  source: string;
}

/** 一程顶峰。 */
export interface Pinnacle {
  index: number;
  key: PinnacleKey;
  label: string;
  value: number;
  root: number;
  is_master: boolean;
  /** 算式，把原值与约简值都印出来，如「月 5 + 日 14→5 = 10 → 1」。 */
  expression: string;
  start_age: number;
  /** 第四顶峰无终点，故为 null；不填 999 之类的假值。 */
  end_age: number | null;
  /** `reference_date` 落在这一段里。判定在后端，前端不重算。 */
  is_current: boolean;
  meaning: string;
  source: string;
}

/**
 * 一个挑战数。刻意**不带 `steps`**：挑战链是全系统唯一把主数约简掉的地方（决策 3 的
 * 例外），整条链压进 `expression` 一个字符串（如 `|月 11→2 − 日 6| = 4`），
 * 例外本身就写在算式上，不必靠读者记住规则。
 */
export interface Challenge {
  index: number;
  key: ChallengeKey;
  label: string;
  /** 值域 0–8；0 是真实值，不是缺失。 */
  value: number;
  expression: string;
  /** 来源给的定性时段文本，**不是**精确年份（spec §5.3）。 */
  duration: string;
  meaning: string;
  source: string;
}

/** 个人流年/流月/流日之一。 */
export interface PersonalCycle {
  key: PersonalCycleKey;
  label: string;
  /** 这一轮覆盖的时段，如 `2026` / `2026-09` / `2026-09-24`。 */
  period: string;
  value: number;
  root: number;
  is_master: boolean;
  meaning: string;
  steps: ReductionStep[];
  source: string;
}

/** 个人年三轮 + 流月 + 流日（决策 11）。 */
export interface PersonalCycles {
  previous_year: PersonalCycle;
  year: PersonalCycle;
  next_year: PersonalCycle;
  month: PersonalCycle;
  day: PersonalCycle;
}

/**
 * 九宫的一格。`tokens` 是"这一格的计数由什么贡献"：姓名九宫里是实际字母，
 * 洛书九宫里是该数字来自生日的哪些位（决策 10：好让计数永远能被生日逐位复核）。
 */
export interface GridCell {
  digit: number;
  /** 0 不是缺失值：姓名九宫里 0 次就是业力课。 */
  count: number;
  tokens: string[];
}

/** 一个数位配一句释义。姓名九宫用作业力课，洛书九宫用作缺数解读。 */
export interface DigitMeaning {
  digit: number;
  meaning: string;
  source: string;
}

/**
 * 姓名天赋九宫。与 `LoshuGrid` **刻意分成两个模型**：输入不同（姓名字母 vs 生日数字）、
 * 传统不同（毕达哥拉斯业力课 vs 洛书平面）、缺数释义也不同。合成一张表就是设计稿犯的
 * 那个错，它因此同时印错了两处（决策 9）。
 */
export interface NumberGrid {
  /** 按 1..9 升序；摆成洛书方阵是 `layout` 的事。 */
  cells: GridCell[];
  /** 显示摆法（洛书 `4 9 2 / 3 5 7 / 8 1 6`）。由后端下发，免得前端排出稿子那个非幻方的升序摆法。 */
  layout: number[][];
  /** 计数合计，恒等于参与计算的字母数。 */
  total: number;
  /** `count == 0` 的数位。 */
  karmic_lessons: DigitMeaning[];
  source: string;
}

/** 洛书的一条线（行/列/对角线），即一个平面或箭矢。 */
export interface LoshuPlane {
  key: LoshuPlaneKey;
  name_zh: string;
  name_en: string;
  /** 构成数字，恒为洛书的一条线。 */
  cells: number[];
  /** 三数是否齐备。 */
  complete: boolean;
  /** 缺哪几个；齐备时为空列表。 */
  missing: number[];
  /** 齐 → `present_text`，缺 → `missing_text`；后端只选句，不组句。 */
  text: string;
  source: string;
}

/** 生辰洛书九宫与八平面。 */
export interface LoshuGrid {
  cells: GridCell[];
  layout: number[][];
  /** 计数合计，恒等于生日里非 0 数字字符的个数。 */
  total: number;
  /** 生日里 0 的个数。洛书无 0 格，故不计入 `total`。 */
  zero_count: number;
  /** 生日取出的全部数字字符（含 0），供逐位复核。 */
  digits: number[];
  /** `count == 0` 的数位及其洛书解读。 */
  missing: DigitMeaning[];
  planes: LoshuPlane[];
  /** 八条线各自的和，恒为 15 —— 幻方性质在响应里就可核对（决策 12）。 */
  line_sums: number[];
  source: string;
}

/** 回显与计数：让读者先看清"到底算了什么"，再看结果。 */
export interface NumerologyInput {
  full_name: string;
  /** 仅回显，不参与任何计算（决策 1）。 */
  name_zh: string | null;
  /** ISO `yyyy-mm-dd`。 */
  birth_date: string;
  reference_date: string;
  y_as_vowel: boolean;
  /** 基准日时的周岁；基准日早于生日时为 null。 */
  age_at_reference: number | null;
  letter_count: number;
  /** 被跳过的非字母字符数（决策 8：如实报，不偷偷算 0）。 */
  skipped_count: number;
  /** 去重后的被跳过字符，供用户看出漏了什么。 */
  skipped_chars: string[];
  /** 元音值总和（表达数不变式的一侧）。 */
  vowel_total: number;
  consonant_total: number;
  /** 全字母值总和，恒 == 元音和 + 辅音和。 */
  letter_total: number;
}

/** 溯源。**没有综合评分、没有均衡度百分比**（决策 13/14）。 */
export interface NumerologyProvenance {
  reference_date: string;
  /** 算法来源声明；本系统无历法库、无星历、无随机。 */
  engine: string;
  /** 档案号，只印方法标识（决策 16：流水号无推导依据，不编）。 */
  badge: string;
  /** 本端点真读到的四张语料表，不多不少。 */
  tables: ProvenanceTable[];
  /** 算法口径叙述：把规则原文下发，读者才能拿它核对响应里的数字。 */
  method: string;
}

/** 完整响应。 */
export interface NumerologyChart {
  input: NumerologyInput;
  letters: LetterValue[];
  /** 固定序：生命灵数 → 表达 → 灵魂冲动 → 人格面具 → 生日 → 成熟。 */
  core: CoreNumber[];
  /** 生命灵数账本里查出的业力债；无债时为空列表（不给缺省，由后端显式递出）。 */
  karmic_debts: KarmicDebt[];
  pinnacles: Pinnacle[];
  challenges: Challenge[];
  personal_cycles: PersonalCycles;
  name_grid: NumberGrid;
  loshu_grid: LoshuGrid;
  provenance: NumerologyProvenance;
}

/** `POST /numerology/chart` 入参。 */
export interface NumerologyChartRequest {
  /** 拉丁字母全名（拼音或英文名），后端限 1–80 字符。 */
  full_name: string;
  /** 中文名，仅回显，后端限 ≤20 字符。 */
  name_zh?: string | null;
  /** ISO `yyyy-mm-dd`。 */
  birth_date: string;
  /** 缺省取今天；不写这个键即缺省（决策 11）。 */
  reference_date?: string | null;
  /** Y 是否计入元音（决策 7）。默认 false；非 Optional，故不接受 null。 */
  y_as_vowel?: boolean;
}
