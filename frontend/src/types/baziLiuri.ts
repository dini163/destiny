/**
 * 流日（全月逐日）契约，镜像 `backend/app/schemas/bazi_liuri.py`。
 *
 * 一页流日 = 命局摘要 + 段回显 + 逐日简表，聚焦日再多带一段明细。可空即 `T | null`，
 * 且三处都是结构性的而非兜底：`focus_date`（只要矩阵）、`dayun_ganzhi`（童年段未起运）、
 * `true_solar_time`（关闭校正）。`value` 永不为 null；`day_hits` 可以是空数组 —— 一条
 * 都没中本身就是「这一天没有可记的账」，是结论不是缺数据。
 *
 * 简表格**不含判语全文**：实测 29 格 27.6 KB，逐格补 `reading` 则 47.3 KB，而判语是规则表
 * 的静态文本，聚焦卡逐行给全就够（spec §2.5）。`TransitDayHit` 因而是 `TransitFired`
 * 去掉 `reading` 的形状，四个同名字段逐字相等由后端测试钉住。
 *
 * 两个日期在请求侧都可空，缺省补齐由服务端做一次并原样回显（`anchor_date` 缺省 = 参考日
 * 所在的节气月段，于是「打开页面就是本月」不需要前端传任何东西）。段推不出、聚焦日越界都是
 * 域错误：422 带 `error.code` 与 `error.context`（`liuri_month_unsupported` /
 * `liuri_focus_out_of_month`），提示里的日期取自 `context`，不是前端二次推算。
 */

import type {
  BaziNatalRequest,
  BaziPillar,
  BranchGroup,
  Provenance,
  RelationPair,
  ShenShaEntry,
} from './bazi';
import type { TransitFired, TransitTenGod } from './baziTransit';
import type { ScoreValue } from './scoring';

/** 流日页入参：命盘入参 + 两个可空日期（段定位在服务端）。 */
export interface BaziLiuriRequest extends BaziNatalRequest {
  /** 段内任一日；缺省 = 参考日所在的节气月段。切段时把上一段的次日交回去。 */
  anchor_date?: string | null;
  /** 给出则额外返回该日详批，必须落在解析出的段内，否则 `liuri_focus_out_of_month`。 */
  focus_date?: string | null;
}

/** 历注宜忌：外部历法库所藏通书内容，不参与任何计分，所以与 `value` 不同源。 */
export interface AlmanacYiJi {
  /** 宜，全量数组，顺序即库给顺序；可为空数组（库给的空，服务端不代填）。 */
  yi: string[];
  /** 忌，全量数组。 */
  ji: string[];
}

/** 矩阵格上的一条日段命中：账本行的可读镜像，判语全文在聚焦卡。 */
export interface TransitDayHit {
  /** 带 `ri.` 前缀的规则键，与 `ScoreFactor.rule` 逐字相等。 */
  key: string;
  /** 短名 +「（流日）」后缀。 */
  label: string;
  /** 九族之一，与 `TransitFired.family` 同源。 */
  family: string;
  /** 本行分值，与账本里那一条同一个数。 */
  delta: number;
}

/** 矩阵里的一格。判语全文不在这里，见 `TransitDayDetail.fired`（spec §2.5 的体积实测）。 */
export interface TransitDayCell {
  /** ISO 日期。 */
  solar_date: string;
  /** 0 = 周一 … 6 = 周日。前导空格数就取这个数，前端不做 `new Date()` 的星期推算。 */
  weekday: number;
  /** 农历日串，月名 + 日名，闰月由库自带「闰」字（腊十九 / 闰五初二）。 */
  lunar_day: string;
  /** 日柱干支，平柱。 */
  ganzhi: string;
  value: number;
  /** 顺 / 平 / 滞，与 `value` 同出一份账本。 */
  tier: string;
  /** 只含 `ri.` 行；一条未中是 `[]`，那是结论不是缺数据。 */
  day_hits: TransitDayHit[];
  almanac: AlmanacYiJi;
}

/** 聚焦日 = 简表行 + 全部明细。继承而非另立字段表：同一天的两组事实不可能漂移。 */
export interface TransitDayDetail extends TransitDayCell {
  /** 合成日柱，`position` 为 `transit_day`。 */
  pillar: BaziPillar;
  /** 流日之干对日主的十神：只作释义，不参与账本。 */
  ten_god: TransitTenGod;
  /** 三段账本：年段无前缀 / 月段 `yue.` / 日段 `ri.`。 */
  score: ScoreValue;
  /** 三段命中 + 判语全文。 */
  fired: TransitFired[];
  /** 命中判语连缀；一条未中时是空串。 */
  narrative: string;
  /** 只含岁运落点（一端为 `extra0`）的关系；命局自有的不在此列。 */
  relations: RelationPair[];
  /** 只含落点在 `extra0` 的条目；中性者亦呈现，只是不定价。 */
  shensha: ShenShaEntry[];
  /** 只含带 `extra0` 成员的局，是 `heyue` 族各行的凭据。 */
  branch_groups: BranchGroup[];
}

/** 一整段流日矩阵：命局摘要 + 段回显 + 逐日格 + 可选聚焦日明细。 */
export interface BaziLiuriResult {
  // 命局摘要：只带这一页要用的那九件，字段名与 `BaziTransitResult` 逐字相同
  four_pillars: string;
  /** 命局四柱：据此把 `extra0` 的落点标回是哪一柱。 */
  pillars: BaziPillar[];
  day_master: string;
  day_master_element: string;
  /** 喜用：三法合并结果，流日不重判。 */
  favorable_elements: string[];
  unfavorable_elements: string[];
  true_solar_time: string | null;
  tst_applied: boolean;
  longitude: number;

  // 段回显：请求里的空值已由服务端补齐，端点与月段账本都取自那一次定位
  anchor_date: string;
  /** 段所属流年；段尾跨年时与 `month_end_solar` 的年不同。 */
  year: number;
  year_ganzhi: string;
  /** 该年虚岁，由 lunar-python 的 `LiuNian.getAge()` 给。 */
  year_age: number;
  /** 所从出的大运段序号（0 为未起运的童年段）。 */
  dayun_index: number;
  dayun_ganzhi: string | null;
  /** 0 = 寅月（正月），与 lunar-python 的 `LiuYue.getIndex()` 同序。 */
  month_index: number;
  /** 月名：正 / 二 / … / 冬 / 腊。 */
  month_in_chinese: string;
  month_ganzhi: string;
  /** 交节日（ISO）：立春起寅月，不是农历初一。 */
  month_start_solar: string;
  /** 下一交节前一日（ISO）。 */
  month_end_solar: string;
  /** 两段账本（年段 + 月段），逐字等于岁运页同段月卡。 */
  month_score: ScoreValue;
  month_fired: TransitFired[];

  days: TransitDayCell[];
  /** 仅 `focus_date` 所指之日给出，其余为 null。 */
  focused: TransitDayDetail | null;
  /** `tables` = 主命盘九张 + 岁运两张 + 历注一张 = 12。 */
  provenance: Provenance;
}
