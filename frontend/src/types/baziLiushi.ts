/**
 * 流时（一个八字日的十二时辰）契约，镜像 `backend/app/schemas/bazi_liushi.py`。
 *
 * 一页流时 = 命局摘要 + 日头回显 + 十二格简表 + 至多一格全明细。可空即 `T | null`，两处
 * 都是结构性的：`dayun_ganzhi`（童年段未起运）、`focused`（未请求聚焦时辰）。
 * `value` 永不为 null；`hour_hits` 可以是空数组 —— 时段一条未中本身就是「这一格没有可记
 * 的账」，是结论不是缺数据，此时该格分值等于 `day_score.value`。
 *
 * 简表格**不含判语全文**（spec §2.5：一格详批实测 ≥ 13.1 KB，12 份全文不可发）。判语是
 * 规则表的静态文本，聚焦卡逐行给全即可。`qi_strength` 是日主临时支的十二长生，只作描述：
 * 纵轴上从头到尾只有 `value` 一把尺（决策 3），它不参与账本、也不参与波形的任何一次高度。
 *
 * 十二格共用一根日柱（决策 1），所以年/月/日三段在格间逐字相同 —— 它们只在 `day_score`
 * 与 `day_fired` 里出现一次，要看某一格的整本账有 `focused.score`。
 */

import type {
  BaziNatalRequest,
  BaziPillar,
  BranchGroup,
  Provenance,
  RelationPair,
  ShenShaEntry,
} from './bazi';
import type { AlmanacYiJi } from './baziLiuri';
import type { TransitFired, TransitTenGod } from './baziTransit';
import type { ScoreValue } from './scoring';

/** 十二地支时辰，序即响应里 `hours` 的序（0 = 子，首格落在当日 23:00）。 */
export const HOUR_BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'] as const;
export type HourBranch = (typeof HOUR_BRANCHES)[number];

/** 流时页入参：命盘入参 + 两个可空件（哪一天、聚焦哪个时辰）。 */
export interface BaziLiushiRequest extends BaziNatalRequest {
  /** 八字日；缺省 = 参考日。23:00 起属次日，所以它不是钟面上的那一天。 */
  solar_date?: string | null;
  /** 地支单字；给出则该时辰升级为全明细，不合十二支即 `liushi_hour_out_of_day`。 */
  focus_hour_zhi?: string | null;
}

/** 一格上的时辰段命中：账本行的可读镜像，判语全文在聚焦卡。 */
export interface TransitHourHit {
  /** 带 `shi.` 前缀的规则键，与 `ScoreFactor.rule` 逐字相等。 */
  key: string;
  /** 短名 +「（流时）」后缀。 */
  label: string;
  /** 九族之一，与 `TransitFired.family` 同源。 */
  family: string;
  /** 本行分值，与账本里那一条同一个数。 */
  delta: number;
}

/** 十二格之一。钟面区间由服务端给（含 23:00 那格），前端不推算时辰边界。 */
export interface TransitHourCell {
  /** 0 = 子时首格，与 `HOUR_BRANCHES` 同序。 */
  index: number;
  zhi: HourBranch;
  /** 时柱，五鼠遁自当日日干。 */
  ganzhi: string;
  /** 北京钟面起（HH:MM）；时辰划分不做真太阳时校正（决策 6）。 */
  start_clock: string;
  end_clock: string;
  /** 四段账本的 value，逐字取自账本而不是另算。 */
  value: number;
  /** 顺 / 平 / 滞，与 `value` 同出一份账本。 */
  tier: string;
  /** 日主临时支的十二长生（长生 / 帝旺 / 墓 / 绝 …），纯描述。 */
  qi_strength: string;
  /** 只含 `shi.` 行；一条未中是 `[]`，那是结论不是缺数据。 */
  hour_hits: TransitHourHit[];
}

/** 聚焦时辰 = 简表行 + 全部明细。继承而非另立字段表，同刻事实不可能漂移。 */
export interface TransitHourDetail extends TransitHourCell {
  /** 合成时柱，`position` 为 `transit_hour`。 */
  pillar: BaziPillar;
  /** 流时之干对日主的十神：只作释义，不参与账本。 */
  ten_god: TransitTenGod;
  /** 四段账本：年段无前缀 / `yue.` / `ri.` / `shi.`。 */
  score: ScoreValue;
  /** 四段命中 + 判语全文。 */
  fired: TransitFired[];
  /** 命中判语连缀；一条未中时是空串。 */
  narrative: string;
  relations: RelationPair[];
  shensha: ShenShaEntry[];
  branch_groups: BranchGroup[];
}

/** 一个八字日的完整流时页：命局摘要 + 日头回显 + 十二格 + 可选聚焦时辰明细。 */
export interface BaziLiushiResult {
  // 命局摘要：只带这一页要用的那九件，字段名与 `BaziTransitResult` / `BaziLiuriResult` 逐字相同
  four_pillars: string;
  pillars: BaziPillar[];
  day_master: string;
  day_master_element: string;
  /** 喜用：三法合并结果，流时不重判。 */
  favorable_elements: string[];
  unfavorable_elements: string[];
  true_solar_time: string | null;
  tst_applied: boolean;
  longitude: number;

  // 日头回显：即流日矩阵同日那一份，逐字（§9.2 第 1 条红线）
  solar_date: string;
  /** 0 = 周一 … 6 = 周日。 */
  weekday: number;
  lunar_day: string;
  day_ganzhi: string;
  year: number;
  year_ganzhi: string;
  year_age: number;
  dayun_index: number;
  dayun_ganzhi: string | null;
  /** 0 = 寅月（正月），与 lunar-python 的 `LiuYue.getIndex()` 同序。 */
  month_index: number;
  month_in_chinese: string;
  month_ganzhi: string;
  month_start_solar: string;
  month_end_solar: string;
  /** 三段账本（年 + 月 + 日）：十二格共同的那半份账。 */
  day_score: ScoreValue;
  day_fired: TransitFired[];
  /** 日粒度历注，页头一句带过，不挂到时辰上（决策 13）。 */
  day_almanac: AlmanacYiJi;

  /** 恒 12 格，子时首格在 0。 */
  hours: TransitHourCell[];
  /** 仅 `focus_hour_zhi` 所指那一格给出，其余为 null。 */
  focused: TransitHourDetail | null;
  /** `tables` = 主命盘八张 + 岁运两张 + 历注一张 = 11，与流日页同源。 */
  provenance: Provenance;
}
