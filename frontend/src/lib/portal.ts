/**
 * Portal (聚合测算大厅) catalogue — the multi-civilisation entry matrix.
 *
 * This is curated *navigational* content (which systems exist, what each one is),
 * not computed results, so it honours the no-mock rule: every system points at a
 * real route from `nav.ts` (the single source of truth for paths). Blurbs describe
 * each discipline factually; no chart value, reading or almanac verdict is invented
 * here.
 */

import type { IconName } from '../components/ui/Icon';
import { ROUTES } from '../nav';

/** Civilisation groupings, aligned with the secondary nav in `nav.ts`. */
export type PortalCategoryId = 'chinese' | 'western' | 'vedicNorse';

export interface PortalCategory {
  id: PortalCategoryId;
  label: string;
}

/** Filter tabs; counts are derived from the catalogue, never hard-coded. */
export const PORTAL_CATEGORIES: readonly PortalCategory[] = [
  { id: 'chinese', label: '华夏术数' },
  { id: 'western', label: '西洋秘学' },
  { id: 'vedicNorse', label: '吠陀与北欧' },
];

export interface PortalSystem {
  /** Stable slug, matching the nav where the system is navigable. */
  slug: string;
  nameZh: string;
  nameEn: string;
  category: PortalCategoryId;
  /** One-line factual description of the discipline. */
  blurb: string;
  /** One or two short capability tags. */
  highlights: string[];
  /** Call-to-action label (MVP only). */
  cta: string;
  /** Absolute route when live; null marks a Phase-2 system. */
  route: string | null;
  /** Phase-2 build status; null for a live MVP system. */
  status: string | null;
  icon: IconName;
}

/** A system is navigable exactly when it has a real route (the live ones). */
export function isLive(system: PortalSystem): boolean {
  return system.route !== null;
}

/**
 * The full system catalogue. Every entry carries a real route; `LIVE_SYSTEM_COUNT`
 * is derived from this array, so the hero copy never drifts as systems ship.
 */
export const PORTAL_SYSTEMS: readonly PortalSystem[] = [
  {
    slug: 'bazi-natal',
    nameZh: '八字命理',
    nameEn: 'BAZI NATAL',
    category: 'chinese',
    blurb: '《渊海子平》正宗四柱推演，以天干地支五行生克制化，厘定身强身弱与十神大运走势。',
    highlights: ['十神精微', '真太阳时'],
    cta: '立即排盘',
    route: ROUTES.baziNatal,
    status: null,
    icon: 'timeline',
  },
  {
    slug: 'zhouyi-divination',
    nameZh: '周易六爻',
    nameEn: 'I CHING',
    category: 'chinese',
    blurb: '文王六十四卦精研，京房纳甲卦变。铜钱三掷起卦，定世应六亲六神，附通行本卦爻辞原文。',
    highlights: ['古籍原文', '世应动爻'],
    cta: '摇铜求卦',
    route: ROUTES.zhouyi,
    status: null,
    icon: 'compass',
  },
  {
    slug: 'western-astrology',
    nameZh: '西洋本命星盘',
    nameEn: 'NATAL CHART',
    category: 'western',
    blurb: '基于普拉西德分宫制与精密黄道，解构日月升、十行星落座落宫、相位与守护格局。',
    highlights: ['瑞士星历', '精密相位'],
    cta: '测绘星图',
    route: ROUTES.westernNatal,
    status: null,
    icon: 'sun',
  },
  {
    slug: 'tarot-oracle',
    nameZh: '经典塔罗神谕',
    nameEn: 'TAROT ORACLE',
    category: 'western',
    blurb: '78 张伟特系大小阿卡纳原生牌阵，凯尔特十字、时间之流与关系牌阵深度洞察。',
    highlights: ['洗牌抽卡', '牌阵解析'],
    cta: '开启抽牌',
    route: ROUTES.tarot,
    status: null,
    icon: 'sparkle',
  },
  {
    slug: 'ziwei-doushu',
    nameZh: '紫微斗数',
    nameEn: 'ZI WEI',
    category: 'chinese',
    blurb: '十二宫垣星曜罗列，紫微天府南北斗交辉，四化飞星直断流年大限气数。',
    highlights: ['十二宫四化体系'],
    cta: '排定命盘',
    route: ROUTES.ziwei,
    status: null,
    icon: 'vault',
  },
  {
    slug: 'qimen-dunjia',
    nameZh: '奇门遁甲',
    nameEn: 'QI MEN',
    category: 'chinese',
    blurb: '帝王之术，九星八门八神九宫定局，天地人神四盘交错，谋定决策时空场。',
    highlights: ['时家转盘法'],
    cta: '起局排盘',
    route: ROUTES.qimen,
    status: null,
    icon: 'gauge',
  },
  {
    slug: 'plum-blossom',
    nameZh: '梅花易数',
    nameEn: 'PLUM BLOSSOM',
    category: 'chinese',
    blurb: '邵康节灵应法门，随感随应、物象心机，报数方位声色皆可起体用卦象。',
    highlights: ['体用互变论'],
    cta: '起卦断体用',
    route: ROUTES.plumBlossom,
    status: null,
    icon: 'seal',
  },
  {
    slug: 'name-metric',
    nameZh: '五格姓名学',
    nameEn: 'NAME METRIC',
    category: 'chinese',
    blurb: '康熙字典原笔画核定，天格地格人格总格外格相生相克数理吉凶。',
    highlights: ['81 数理吉凶表'],
    cta: '核定笔画',
    route: ROUTES.nameMetric,
    status: null,
    icon: 'search',
  },
  {
    slug: 'lenormand-cards',
    nameZh: '雷诺曼神谕',
    nameEn: 'LENORMAND',
    category: 'western',
    blurb: '欧式 36 张生活微观象征图画，大画卷（Grand Tableau）全景排布直析吉凶线索。',
    highlights: ['36 张全景大阵'],
    cta: '洗牌抽牌',
    route: ROUTES.lenormand,
    status: null,
    icon: 'vault',
  },
  {
    slug: 'astrology-transit',
    nameZh: '行运次限推运',
    nameEn: 'TRANSIT & SEC.',
    category: 'western',
    blurb: '外行星过境、太阳弧与次限法双重时间轴对碰，动态叠加本命盘。',
    highlights: ['多盘动态重叠'],
    cta: '叠加行运盘',
    route: ROUTES.transit,
    status: null,
    icon: 'timeline',
  },
  {
    slug: 'numerology-matrix',
    nameZh: '毕达哥拉斯灵数',
    nameEn: 'NUMEROLOGY',
    category: 'western',
    blurb: '生命灵数、表达数与灵魂冲动数，以数字震动频率洞察天赋潜能与流年周期。',
    highlights: ['双九宫矩阵'],
    cta: '推演灵数',
    route: ROUTES.numerologyMatrix,
    status: null,
    icon: 'gauge',
  },
  {
    slug: 'kabbalah-tree',
    nameZh: '卡巴拉生命之树',
    nameEn: 'KABBALAH',
    category: 'western',
    blurb: '十原质（Sephiroth）与 22 条神圣路径，对应塔罗大阿卡纳与希伯来字母创世密源。',
    highlights: ['原质路径升华'],
    cta: '探索生命之树',
    route: ROUTES.kabbalah,
    status: null,
    icon: 'compass',
  },
  {
    slug: 'synastry-composite',
    nameZh: '合盘与相契度',
    nameEn: 'SYNASTRY',
    category: 'western',
    blurb: '双人本命比较盘（Synastry）人对人相位、短弧中点组合盘（Composite）与相契度总分账本，直击两人因缘契合力学。',
    highlights: ['双轮合盘', '相契度账本'],
    cta: '开始合盘',
    route: ROUTES.synastry,
    status: null,
    icon: 'compass',
  },
  {
    slug: 'vedic-astrology',
    nameZh: '吠陀乔蒂什',
    nameEn: 'JYOTISH',
    category: 'vedicNorse',
    blurb: '基于恒星黄道（Lahiri Ayanamsa）及 27 宿（Nakshatras），推演业力因果与达夏大运。',
    highlights: ['南印 / 北印方盘'],
    cta: '排定星盘',
    route: ROUTES.vedic,
    status: null,
    icon: 'sun',
  },
  {
    slug: 'norse-runes',
    nameZh: '北欧卢恩符文',
    nameEn: 'ELDER FUTHARK',
    category: 'vedicNorse',
    blurb: '24 枚古老弗萨克字符石，序位据 Kylver 石碑；单枚启示、诺伦三女神运命之阵与卢恩十字，另可启用现代增补的空白符。',
    highlights: ['三种牌阵', '全典检索'],
    cta: '掷符铸石',
    route: ROUTES.norseRunes,
    status: null,
    icon: 'seal',
  },
];

/** Count of live (MVP) systems, for the hero copy. */
export const LIVE_SYSTEM_COUNT = PORTAL_SYSTEMS.filter(isLive).length;
