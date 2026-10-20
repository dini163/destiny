/**
 * 奇门遁甲 (Qi Men Dun Jia) API types mirroring `backend/app/schemas/qimen.py`.
 * snake_case is preserved end-to-end. 奇门 is time-based divination, not a natal
 * chart: the 用事时辰 fixes 阴阳遁 + 局数, the 地盘三奇六仪 is laid by 局数, and the
 * 天盘九星 / 人盘八门 / 神盘八神 are rotated into the 洛书九宫.
 */

import type { PlainSection, ProvenanceTable } from './common';

/** Input for a 奇门遁甲 起局. */
export interface QimenRequest {
  /** 用事时刻, ISO `yyyy-mm-ddTHH:mm:ss`; defaults to now when omitted. */
  cast_time?: string | null;
  /** 占问事项, echoed back only. */
  question?: string | null;
}

/** One 九星 seated on the 天盘, with its 五行·吉凶·类象. */
export interface StarInfo {
  name: string;
  element: string;
  /** 吉 | 凶 | 中平. */
  luck: string;
  nature: string;
  /** 此星为本局值符星。 */
  is_zhifu: boolean;
}

/** One 八门 seated on the 人盘. */
export interface DoorInfo {
  name: string;
  element: string;
  /** 吉 | 凶 | 中平. */
  luck: string;
  nature: string;
  /** 此门为本局值使门。 */
  is_zhishi: boolean;
}

/** One 八神 seated on the 神盘. */
export interface GodInfo {
  name: string;
  /** 吉 | 凶. */
  luck: string;
  nature: string;
}

/** One 洛书宫 cell of the board (中五宫 carries only its 地盘干). */
export interface QimenPalace {
  /** 洛书数 1-9. */
  number: number;
  gua: string;
  direction: string;
  element: string;
  /** 所纳地支；中宫为空。 */
  zhi: string;
  /** 3×3 grid row (南上北下), 0-based. */
  row: number;
  /** 3×3 grid column, 0-based. */
  col: number;
  /** 中五宫（无门无神，天禽寄坤二）。 */
  is_center: boolean;
  /** 地盘干（固定，由局数布）。 */
  dipan_gan: string;
  /** 天盘干（旋转后落此宫；坤二寄中宫干时可两枚）。 */
  tianpan_gan: string[];
  /** 天盘九星（天禽寄坤二时可两枚）。 */
  stars: StarInfo[];
  /** 人盘八门；中宫为 null。 */
  door: DoorInfo | null;
  /** 神盘八神；中宫为 null。 */
  god: GodInfo | null;
  /** 此宫地支落旬空。 */
  kong: boolean;
  /** 此宫地支落驿马。 */
  ma: boolean;
  /** 值符星落此宫。 */
  is_zhifu_palace: boolean;
  /** 值使门落此宫。 */
  is_zhishi_palace: boolean;
  plain: string;
}

/** Chart provenance — engine, corpus version and the school notes. */
export interface QimenProvenance {
  engine: string;
  content_version: string;
  source: string;
  school_note: string;
  tables: ProvenanceTable[];
}

/** Complete 奇门遁甲 局 produced by the backend engine. */
export interface QimenChart {
  question: string | null;
  cast_time: string;

  /** 四柱干支. */
  year_ganzhi: string;
  month_ganzhi: string;
  day_ganzhi: string;
  time_ganzhi: string;

  /** 定局. */
  jieqi: string;
  /** 上元 | 中元 | 下元（日干支符头定）. */
  yuan: string;
  /** 阳遁 | 阴遁. */
  dun: string;
  ju_number: number;
  ju_name: string;

  /** 值符值使. */
  xunshou: string;
  xunshou_yi: string;
  zhifu_star: string;
  zhishi_door: string;
  zhifu_palace: number;
  zhishi_palace: number;
  /** 旬空二支, e.g. 寅卯. */
  kongwang: string;
  /** 驿马地支, e.g. 巳. */
  yima: string;

  /** 洛书九宫，按 1-9 排列. */
  palaces: QimenPalace[];

  /** 全局白话：值符主线、值使门线、时干落宫、旬空与驿马四节。 */
  plain: PlainSection[];

  engine: string;
  provenance: QimenProvenance;
}
