/**
 * Global navigation model for the persistent App Shell.
 *
 * Mirrors the multi-civilization nav in the design mockups: a primary bar of the
 * Phase-1 destinations plus a secondary, categorized bar spanning the full
 * 16-system roadmap. Only the five Phase-1 routes plus 姓名学、数字命理 and 北欧卢恩 are
 * navigable; every other system is declared here with `to: null` so the "全域" nav is
 * complete now and a later phase merely points a slug at a real route — no shell
 * re-architecture.
 *
 * `ROUTES` is the single source of truth for router paths, shared by the nav, the
 * router and in-app links so they can never drift apart.
 */

/** Canonical absolute router paths for every navigable destination. */
export const ROUTES = {
  overview: '/overview',
  baziNatal: '/bazi-natal',
  /** 岁运推演（切片 2）。本命盘之外的流年/流月时间轴，不是独立新体系；v1 起纳入
   * `SECONDARY_NAV` 华夏术数组方便直达（原先刻意收在本命页内，入口过深）。 */
  baziTransit: '/bazi-transit',
  /** 全月流日矩阵（切片 3）。与 `baziTransit` 同一条理由不进导航：它是岁运页月卡的下钻，
   * 无生辰即无意义，不是一新一大体系（spec 决策 8）。 */
  baziLiuri: '/bazi-liuri',
  // 岁运 → 流日 → 流时的下钻终点，不进 SECONDARY_NAV：无生辰即无意义。
  baziLiushi: '/bazi-liushi',
  /** 双人合盘（切片 5）。与岁运/流日/流时不同，它进 `SECONDARY_NAV`：合婚不挂在任何
   * 单造命盘之下，是一档独立的体系入口，`以此造合婚` 只是它的一个可选起点（决策 10）。 */
  baziHehun: '/bazi-hehun',
  westernNatal: '/western-astrology',
  /** 行运次限推运（西洋秘学）。在本命盘之上叠行运/次限/太阳弧三层动态时间轴。 */
  transit: '/astrology-transit',
  /** 双人合盘（西洋秘学）。两张本命盘同屏：人对人相位、短弧中点组合盘与相契度总分。
   * 与八字合婚同为一档独立体系入口，故进 `SECONDARY_NAV`；不挂在任何单造星盘之下。 */
  synastry: '/astrology-synastry',
  tarot: '/tarot-oracle',
  /** 雷诺曼（西洋秘学）。36 张生活象征牌，一律正位、以组合直读见长，大桌全景尽铺三十六张。 */
  lenormand: '/lenormand-cards',
  /** 卡巴拉生命之树（西洋秘学）。十原质与 22 路径之黄金黎明对应图，可 gematria 折入。 */
  kabbalah: '/kabbalah-tree',
  zhouyi: '/zhouyi-divination',
  /** 紫微斗数（华夏术数）。以农历生月生时安命身二宫，纳音定五行局，布十四主星与生年四化。 */
  ziwei: '/ziwei-doushu',
  /** 奇门遁甲（华夏术数）。以用事时辰定阴阳遁与局数，转天盘九星、人盘八门、神盘八神入洛书九宫。 */
  qimen: '/qimen-dunjia',
  /** 梅花易数（华夏术数）。以体用生克直断，起卦纯为确定性推算，与六爻纳甲并列。 */
  plumBlossom: '/plum-blossom',
  nameMetric: '/name-metric',
  /** 毕达哥拉斯数字命理（切片 6）。列在「西洋秘学」而不是它原先待的「吠陀与北欧」：
   * `lib/portal.ts` 早已把它归为 `category: 'western'`，设计稿的次级导航也把它印在
   * 「西洋秘学」下 —— 三者里两处说 western，而毕达哥拉斯数理本就不是吠陀或北欧体系。 */
  numerologyMatrix: '/numerology-matrix',
  /** 吠陀占星（吠陀与北欧）。以拉希里岁差之恒星黄道排盘，九曜、二十七宿与 Vimshottari 大运。 */
  vedic: '/vedic-astrology',
  /** 北欧卢恩（切片 7）。归在「吠陀与北欧」：该组本就有这一格（与吠陀乔蒂什同组），
   * 故不必为它新开一个只有一个成员的组 —— 设计稿把它放在「北欧符文与吠陀」下，同一个意思。 */
  norseRunes: '/norse-runes',
  /** 我的档案：本机 localStorage 里的人名生辰档案库，供各测算控制台一键填充。 */
  profiles: '/profiles',
} as const;

/** A single navigation entry. `to === null` marks a roadmap system not yet built. */
export interface NavItem {
  /** Stable slug; used as the React key and matching the router path segment. */
  slug: string;
  /** Chinese label rendered in the bar. */
  label: string;
  /** Absolute router path when the destination exists, otherwise null. */
  to: string | null;
}

/** A civilization grouping in the secondary nav bar. */
export interface NavGroup {
  /** Grouping caption, e.g. 华夏术数. */
  title: string;
  items: NavItem[];
}

/** Primary bar — the Phase-1 entry points, all navigable. */
export const PRIMARY_NAV: NavItem[] = [
  { slug: 'overview', label: '测算大厅', to: ROUTES.overview },
  { slug: 'bazi-natal', label: '八字排盘', to: ROUTES.baziNatal },
  { slug: 'western-astrology', label: '西洋占星', to: ROUTES.westernNatal },
  { slug: 'tarot-oracle', label: '塔罗神谕', to: ROUTES.tarot },
  { slug: 'zhouyi-divination', label: '周易六爻', to: ROUTES.zhouyi },
];

/** Secondary bar — the full catalog grouped by civilization (Phase-2 disabled). */
export const SECONDARY_NAV: NavGroup[] = [
  {
    title: '华夏术数',
    items: [
      { slug: 'bazi-natal', label: '八字命理', to: ROUTES.baziNatal },
      { slug: 'bazi-transit', label: '岁运推演', to: ROUTES.baziTransit },
      { slug: 'ziwei-doushu', label: '紫微斗数', to: ROUTES.ziwei },
      { slug: 'qimen-dunjia', label: '奇门遁甲', to: ROUTES.qimen },
      { slug: 'zhouyi-divination', label: '文王六爻', to: ROUTES.zhouyi },
      { slug: 'plum-blossom', label: '梅花易数', to: ROUTES.plumBlossom },
      { slug: 'bazi-hehun', label: '八字合婚', to: ROUTES.baziHehun },
      { slug: 'name-metric', label: '五格姓名学', to: ROUTES.nameMetric },
    ],
  },
  {
    title: '西洋秘学',
    items: [
      { slug: 'western-astrology', label: '本命星盘', to: ROUTES.westernNatal },
      { slug: 'astrology-transit', label: '行运推运', to: ROUTES.transit },
      { slug: 'astrology-synastry', label: '双人合盘', to: ROUTES.synastry },
      { slug: 'tarot-oracle', label: '经典塔罗', to: ROUTES.tarot },
      { slug: 'lenormand-cards', label: '雷诺曼', to: ROUTES.lenormand },
      { slug: 'kabbalah-tree', label: '卡巴拉', to: ROUTES.kabbalah },
      { slug: 'numerology-matrix', label: '毕氏灵数', to: ROUTES.numerologyMatrix },
    ],
  },
  {
    title: '吠陀与北欧',
    items: [
      { slug: 'vedic-astrology', label: '吠陀乔蒂什', to: ROUTES.vedic },
      { slug: 'norse-runes', label: '北欧卢恩', to: ROUTES.norseRunes },
    ],
  },
];
