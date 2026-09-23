/**
 * 八字合婚契约，镜像 `backend/app/schemas/bazi_hehun.py`（Task 8 收口后的形状）。
 *
 * 字段一律 snake_case、与 JSON 逐字相同，响应过一层映射层就又是另一份真相。四类
 * nullability 是有意分开的，别在页面里"顺手补一个 0"：
 *
 * ① 「非 Optional + 自带默认」的三个入参字段 —— `HehunProfile.calendar`、
 *    `HehunProfile.apply_true_solar_time`、`BaziHehunRequest.axis_years` —— 类型上不给
 *    `null`（`CalendarType` / `boolean` / `int` 都不接受 None），交 `null` 会吃 pydantic
 *    的 422 `{"detail": [...]}`，与域错误那类不同。所以它们是 `?: CalendarType` /
 *    `?: boolean` / `?: number`：缺省就是**不写那个键**。
 * ② 「Optional + 默认 None」的入参才写 `| null`：`city`、`latitude`、`longitude`、`name`、
 *    `reference_date`、`axis_start_year`。`longitude` 的默认是 `None` 而不是 120°E，是有意
 *    为之（与 `types/common.ts` 的 `BirthInput.longitude?: number | null` 同形）：显式经线
 *    一旦有默认值就会在 `profile_longitude` 里恒胜过城市，地理编码永不发生。120°E 那条
 *    标准经线只在**关闭校正**时由 `profile_longitude` 兜底，不在契约里冒名顶替。
 * ③ 结构性可空（响应侧）：`HehunAxisSide.dayun`（童限未起运）、
 *    `HehunPartner.true_solar_time`（该造关了校正）、两侧的 `name`。
 * ④ 空格子是空列表而不是 `null`：矩阵 `hits`、四象限 `elements`、宜忌 `items`。
 *    "查过了、没有"是结论，页面据此画出「无」（spec §10.6）。
 *
 * 三条恒长在契约里写明，页面因此不必防缺段：`matrix` 16 格、`complement.views` 2 视角
 * × `cells` 4 格、`yi_ji.groups` 6 组（§5.2、§10.6）。轴行**不带** `factors`：那是
 * 切片 3 定下的简表约定，明细走轴行那两个岁运下钻链接（§7.3）。
 */

import type { CalendarType, ProvenanceTable } from './common';
import type { DayunStep, WuxingScore } from './bazi';
import type { ScoreValue } from './scoring';

/** 乾/坤。键位即性别，所以档案与 profile 里都没有 `gender` 字段（spec §5.1）。 */
export type HehunSide = 'male' | 'female';

/** 一条账本行的视角：互济族天生两向，其余四族无向（spec §6.2）。 */
export type HehunDirection = 'male_to_female' | 'female_to_male' | 'mutual';

/** 一造盘里某一行的旺弱（spec §2.6 那把尺）。`平` 只出现在描述里，四象限取 旺|弱。 */
export type Vigor = '旺' | '弱' | '平';

/** 四象限横轴的取值面 —— 表里没有「平」这一格，所以类型上先削掉。 */
export type VigorEdge = Extract<Vigor, '旺' | '弱'>;

/** 年命纳音的五行关系，主语固定为乾（spec §7.2）。 */
export type NayinRelation = '生我' | '我生' | '我克' | '克我' | '比和';

/** 轴行两造分数之差的三档（spec §7.3，阈值 8.0 / 20.0）。与合婚四档是两套词汇。 */
export type AxisSync = '同频' | '半同步' | '背离';

/** 宜忌六组的组名，恒 6 组、序即 §7.4 的阅读序。 */
export type YiJiKind = '同宜' | '乾独宜' | '坤独宜' | '同忌' | '乾独忌' | '坤独忌';

/** 一造的全部出生参数。 */
export interface HehunProfile {
  birth_date: string;
  birth_time: string;
  calendar?: CalendarType;
  city?: string | null;
  latitude?: number | null;
  /** 后端 `float | None = Field(default=None, ge=-180, le=180)`；缺省不设经线，见文件头 ②。 */
  longitude?: number | null;
  apply_true_solar_time?: boolean;
  /** 称谓，逐字回显、不进计算（后端 `max_length=40`）。 */
  name?: string | null;
}

/** 合婚页入参：两造生辰 + 参考日 + 轴的起点与年数。 */
export interface BaziHehunRequest {
  male: HehunProfile;
  female: HehunProfile;
  /** 只解析一次：定当前大运与缺省轴起点（切片 0 的纪律）。 */
  reference_date?: string | null;
  /** 缺省 = `max(较晚出生年, 参考日所在年)`；越界即 `hehun_axis_out_of_range`（§9.3）。 */
  axis_start_year?: number | null;
  /** 1–30，后端默认 21。越界走 pydantic 的 `{"detail": [...]}`，与域错误分两类。 */
  axis_years?: number;
}

/** 矩阵一格里扫到的一条跨造事实。 */
export interface HehunCellHit {
  /** 关系中文名，与 `RELATION_TABLES` 的 kind 同词。 */
  kind: string;
  /** 乾那一根的干、支或整柱（伏吟/反吟论整柱）。 */
  male_character: string;
  female_character: string;
  /** 该 kind 的账本键；矩阵是呈现层，键只作标识与对拍。 */
  rule: string;
  /** 格内一律 `mutual`：字段在，是为了与 `HehunFired` 共用一个渲染器。 */
  direction: HehunDirection;
}

/** (乾一根柱) × (坤一根柱) 的一格；恒 16 格，空格 `hits` 为空列表。 */
export interface HehunCell {
  male_position: string;
  female_position: string;
  hits: HehunCellHit[];
}

/** 一条命中的合婚规则：账本行的可读镜像，与 `ScoreFactor` 同键同 delta。 */
export interface HehunFired {
  rule: string;
  label: string;
  /** 五族之一：relation | group | yongshen | nayin | palace。 */
  family: string;
  direction: HehunDirection;
  delta: number;
  /** 单句判语；借古籍的那半句与自造的那半句同在一句里（§6.3）。 */
  reading: string;
}

/** 象限里的一个五行：只带名字与该造的旺弱读数，规则与单价在同级那一格上。 */
export interface HehunComplementElement {
  element: string;
  /** 该行加权量对**该造自身五行均值**的比值，四位小数（§2.6）。 */
  ratio: number;
}

/** 四象限的一格（§7.1）：纵轴是观看方的喜/忌，横轴是对方的旺/弱。 */
export interface HehunComplementCell {
  rule: string;
  /** 单字格名：补 | 阙 | 冲 | 安。 */
  name: string;
  mine: 'favorable' | 'unfavorable';
  /** 横轴只有旺/弱：`平` 不落象限（§7.1），所以这里是 `VigorEdge` 而不是 `Vigor`。 */
  theirs: VigorEdge;
  delta: number;
  /** 落在本格的五行，序为观看方喜忌集自身的序；空格是空列表。 */
  elements: HehunComplementElement[];
}

/** 一个视角的四象限。 */
export interface HehunComplementView {
  viewer: HehunSide;
  /** 「乾视坤」短名，与账本行 `label` 里那一处同源。 */
  label: string;
  cells: HehunComplementCell[];
}

/** 五行互补：四象限 × 两视角，与互济族账本出自同一次判定（§7.1）。 */
export interface HehunComplement {
  views: HehunComplementView[];
}

/** 一造的年命纳音：名、五行、取象原文逐字取自 `NayinCorpus`。 */
export interface HehunNayinSide {
  ganzhi: string;
  nayin: string;
  /** 纳音五行 —— 生克论的是这个，不是日主五行。 */
  element: string;
  /** 《三命通会》取象原文首句，引擎不改写。 */
  imagery: string;
  source: string;
}

/** 年命纳音（§7.2）：一对纳音只出一个关系、只入一行账。 */
export interface HehunNayin {
  male: HehunNayinSide;
  female: HehunNayinSide;
  relation: NayinRelation;
  /** 三字生克句：水生木 / 木克土 / 木与木同气。 */
  phrase: string;
  rule: string;
  delta: number;
  reading: string;
}

/** 一造在某一年的分数与档位 —— 与岁运年表同一条装配路径（§10.5）。 */
export interface HehunAxisSide {
  value: number;
  /** 岁运四档：顺 | 平 | 滞。与合婚总分的四档是两套词汇（§6.4）。 */
  tier: string;
  /** 该年所从出的大运干支；起运前为 `null`，页面标「童限」。 */
  dayun: string | null;
  dayun_start_age: number;
}

/** 轴的一年：两造各自的分数 + 它们之差。简表不带判语（§5.2，继承切片 3）。 */
export interface HehunAxisRow {
  year: number;
  ganzhi: string;
  male: HehunAxisSide;
  female: HehunAxisSide;
  /** |乾分 - 坤分|。 */
  gap: number;
  sync: AxisSync;
}

/** 一段大运边界切出来的区间（§7.3）。 */
export interface HehunAxisSegment {
  start_year: number;
  end_year: number;
  /** 只写事实本身，家族称谓不另立表 —— 轴的段就是大运段。 */
  label: string;
}

/** 同频演进轴：一轴一次算，不给任何一格展开明细（§7.3）。 */
export interface HehunAxis {
  start_year: number;
  end_year: number;
  rows: HehunAxisRow[];
  /** 段的并集恰好覆盖 `rows`，序与轴同向。 */
  segments: HehunAxisSegment[];
}

/** 一个五行的通说配属（方位 / 五色 / 四时）。 */
export interface HehunYiJiItem {
  element: string;
  direction: string;
  color: string;
  season: string;
}

/** 宜忌的一组。 */
export interface HehunYiJiGroup {
  kind: YiJiKind;
  items: HehunYiJiItem[];
}

/** 宜忌（§7.4）：唯一输入是两造本命盘的喜用与忌神。 */
export interface HehunYiJi {
  groups: HehunYiJiGroup[];
  /** 逐字取自后端声明句，前端不补算也不改写。 */
  declaration: string;
}

/** 双人页上的一柱：只到"这一柱是谁"为止，藏干与地势是本命盘的事。 */
export interface HehunPartnerPillar {
  position: string;
  label: string;
  ganzhi: string;
  /** 该柱天干对**本造**日主的十神；日柱本身为「日主」。 */
  shishen_gan: string;
  nayin: string;
}

/** 一造的精简档案（§5.2）。刻意不是 `/natal` 的副本。 */
export interface HehunPartner {
  side: HehunSide;
  name: string | null;
  /** 空格连写的四柱，如 戊辰 甲寅 庚子 丁亥。 */
  four_pillars: string;
  zodiac: string;
  day_master: string;
  day_master_element: string;
  /** 喜用神，逐字取该造本命盘（决策 3：合婚不重判）。 */
  favorable_elements: string[];
  unfavorable_elements: string[];
  /** 五行分布，木火土金水序；复用命盘的 `WuxingScore`，因此带 `count`。 */
  elements: WuxingScore[];
  pillars: HehunPartnerPillar[];
  /** 该造的大运步表（含 index 0 的童限段），因此带 `xun` / `is_current`。 */
  dayun: DayunStep[];
  /** 该造起柱所用的真太阳时；关闭校正时为 `null`。 */
  true_solar_time: string | null;
  /** 各造一份，不共用（§5.1）。 */
  tst_applied: boolean;
}

/** 合婚页自带的溯源。 */
export interface HehunProvenance {
  reference_date: string;
  engine: string;
  /** 规则表条数（29）：页面上"每条命中都可核对"那一句话的数目。 */
  rule_count: number;
  tables: ProvenanceTable[];
  /** 方法声明：四档命名、旺弱尺与自造判语的出处口径。 */
  method: string;
}

/** 合婚一页的全部（§5.2）：一次请求给全，段与段之间互相自洽。 */
export interface BaziHehunResult {
  male: HehunPartner;
  female: HehunPartner;
  /** 契合度总分与 29 条族账本（`Σ factors[].delta === value`，含截断行）。 */
  score: ScoreValue;
  matrix: HehunCell[];
  fired: HehunFired[];
  complement: HehunComplement;
  nayin: HehunNayin;
  axis: HehunAxis;
  yi_ji: HehunYiJi;
  provenance: HehunProvenance;
}
