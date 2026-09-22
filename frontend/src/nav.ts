/**
 * Global navigation model for the persistent App Shell.
 *
 * Mirrors the multi-civilization nav in the design mockups: a primary bar of the
 * Phase-1 destinations plus a secondary, categorized bar spanning the full
 * 16-system roadmap. Only the five Phase-1 routes plus 姓名学 are navigable;
 * every other system is declared here with `to: null` so the "全域" nav is
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
  /** 岁运推演（切片 2）。刻意不进 `SECONDARY_NAV` 与 `PORTAL_SYSTEMS`：它是主盘之外的
   * 子页，不是一新一大体系，列进去会让"几大核心体系"这个数字虚增一格（spec 决策 8）。 */
  baziTransit: '/bazi-transit',
  /** 全月流日矩阵（切片 3）。与 `baziTransit` 同一条理由不进导航：它是岁运页月卡的下钻，
   * 无生辰即无意义，不是一新一大体系（spec 决策 8）。 */
  baziLiuri: '/bazi-liuri',
  // 岁运 → 流日 → 流时的下钻终点，不进 SECONDARY_NAV：无生辰即无意义。
  baziLiushi: '/bazi-liushi',
  westernNatal: '/western-astrology',
  tarot: '/tarot-oracle',
  zhouyi: '/zhouyi-divination',
  nameMetric: '/name-metric',
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
      { slug: 'ziwei-doushu', label: '紫微斗数', to: null },
      { slug: 'qimen-dunjia', label: '奇门遁甲', to: null },
      { slug: 'zhouyi-divination', label: '文王六爻', to: ROUTES.zhouyi },
      { slug: 'plum-blossom', label: '梅花易数', to: null },
      { slug: 'name-metric', label: '五格姓名学', to: ROUTES.nameMetric },
    ],
  },
  {
    title: '西洋秘学',
    items: [
      { slug: 'western-astrology', label: '本命星盘', to: ROUTES.westernNatal },
      { slug: 'astrology-transit', label: '行运推运', to: null },
      { slug: 'tarot-oracle', label: '经典塔罗', to: ROUTES.tarot },
      { slug: 'lenormand-cards', label: '雷诺曼', to: null },
      { slug: 'kabbalah-tree', label: '卡巴拉', to: null },
    ],
  },
  {
    title: '吠陀与北欧',
    items: [
      { slug: 'vedic-astrology', label: '吠陀乔蒂什', to: null },
      { slug: 'norse-runes', label: '北欧卢恩', to: null },
      { slug: 'numerology-matrix', label: '毕氏灵数', to: null },
    ],
  },
];
