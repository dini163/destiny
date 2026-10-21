/**
 * 岁运（流年 / 流月）契约，镜像 `backend/app/schemas/bazi_transit.py`。
 *
 * 一页岁运 = 命局摘要 + 区间回显 + 逐年账本，聚焦年再多带十二节气月。可空即 `T | null`，
 * 且四处都是结构性的而非兜底：`focus_year`（只要年表）、`months`（未请求聚焦年）、
 * `dayun_ganzhi`（童年段未起运）、`true_solar_time`（关闭校正）。`score` 永不为 null ——
 * 一条都没命中时账本只剩基准 50 分 / 档「平」，那本身是可核对的结论。
 *
 * 区间三个字段在请求侧全部可空，缺省补齐由服务端做一次并原样回显，前端不再二次推算；
 * 区间不成立时是域错误：422 带 `error.code` 与 `error.context`（倒序 / 过宽 / 本命盘
 * 不可及 / 聚焦年越界四个码），提示里的数字取自 `context`，不是把「最多 10 年」写死。
 */

import type {
  BaziNatalRequest,
  BaziPillar,
  BranchGroup,
  DayunStep,
  Provenance,
  RelationPair,
  ShenShaEntry,
} from './bazi';
import type { PlainSection } from './common';
import type { ScoreValue } from './scoring';

/** 岁运页入参：命盘入参 + 三个可空年份（补齐在服务端）。 */
export interface BaziTransitRequest extends BaziNatalRequest {
  /** 区间起始年（含）。缺省 = 参考日所在年，或 `end_year - 4`。 */
  start_year?: number | null;
  /** 区间结束年（含）。缺省 = `start_year + 4`；跨度上限 10 年。 */
  end_year?: number | null;
  /** 给出则额外展开该年十二节气流月，须落在区间之内。 */
  focus_year?: number | null;
}

/** 一条命中的岁运规则：账本行 + 它自己的判语。 */
export interface TransitFired {
  /** 与 `ScoreFactor.rule` 逐字相等；月段带 `yue.` 前缀。 */
  key: string;
  /** 短名，如 冲太岁；月段加「（流月）」后缀。 */
  label: string;
  /** 九族之一（yongshen / taisui / …），分组序沿用响应序。 */
  family: string;
  delta: number;
  /** 单句判语，古籍引文在句内，末尾自署书名或「本系统」。 */
  reading: string;
}

/** 岁运之干对日主的十神：只作释义，不参与账本。 */
export interface TransitTenGod {
  god: string;
  /** 《渊海子平》原句，引擎不组句。 */
  meaning: string;
  source: string;
}

/** 一个节气月：两段账本（年段 + 月段）。 */
export interface TransitMonth {
  /** 0 = 寅月（正月），与 lunar-python 的 `LiuYue.getIndex()` 同序。 */
  index: number;
  /** 月名：正 / 二 / … / 冬 / 腊。 */
  month_in_chinese: string;
  ganzhi: string;
  /** 合成月柱，`position` 为 `transit_month`。 */
  pillar: BaziPillar;
  /** 交节日（ISO）：立春起寅月，不是农历初一。 */
  start_solar: string;
  /** 下一交节前一日（ISO）。 */
  end_solar: string;
  /** 该流年全部命中行 + 该流月命中行。 */
  score: ScoreValue;
  /** 年段行无 `yue.` 前缀，月段行带。 */
  fired: TransitFired[];
}

/** 一个流年：合成柱、单段账本与三张岁运扫描明细。 */
export interface TransitYear {
  year: number;
  /** 该年虚岁。 */
  age: number;
  /** 流年合成柱，`position` 为 `transit_year`。 */
  pillar: BaziPillar;
  /** 所从出的大运段序号（0 为未起运的童年段）。 */
  dayun_index: number;
  dayun_ganzhi: string | null;
  ten_god: TransitTenGod;
  /** 单段（岁）账本；`Σ factors[].delta == value`。 */
  score: ScoreValue;
  fired: TransitFired[];
  /** 命中判语连缀；月卡不重复此句（月段断语逐行可展开）。 */
  narrative: string;
  /** 只含岁运落点（一端为 `extra0`）的关系；命局自有的不在此列。 */
  relations: RelationPair[];
  /** 只含落点在 `extra0` 的条目；中性者亦呈现，只是不定价。 */
  shensha: ShenShaEntry[];
  /** 只含带 `extra0` 成员的局，是 `heyue` 族各行的凭据。 */
  branch_groups: BranchGroup[];
  /** 仅 `focus_year` 所指之年给出，其余年为 null。 */
  months: TransitMonth[] | null;
}

/** 一整页岁运推演。 */
export interface BaziTransitResult {
  // 命局摘要：只带这一页要用的那几件
  four_pillars: string;
  /** 命局四柱：据此把 `extra0` 的落点标回是哪一柱。 */
  pillars: BaziPillar[];
  day_master: string;
  day_master_element: string;
  /** 喜用：三法合并结果，岁运不重判。 */
  favorable_elements: string[];
  unfavorable_elements: string[];
  true_solar_time: string | null;
  tst_applied: boolean;
  longitude: number;

  // 区间回显：请求里的空值已由服务端补齐
  start_year: number;
  end_year: number;
  focus_year: number | null;
  /** 区间跨过的运程，跨年段时可能两段；`is_current` 与主命盘同源。 */
  dayun_covered: DayunStep[];
  years: TransitYear[];

  /** 页级整体白话（批次二 spec §5–§7）；顺序与节名由后端定，前端不补算也不改写。 */
  plain: PlainSection[];
  /** `tables` = 主命盘九张 + 岁运两张（`bazi_changsheng`、`bazi_transit_rules`）。 */
  provenance: Provenance;
}
