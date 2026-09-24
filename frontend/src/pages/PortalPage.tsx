import { useState } from 'react';
import { Link } from 'react-router-dom';

import { DailyTimePanel } from '../components/portal/DailyTimePanel';
import { SystemCard } from '../components/portal/SystemCard';
import { Icon } from '../components/ui/Icon';
import { SegmentedControl } from '../components/ui/SegmentedControl';
import { LIVE_SYSTEM_COUNT, PORTAL_CATEGORIES, PORTAL_SYSTEMS } from '../lib/portal';
import type { PortalCategoryId } from '../lib/portal';
import { ROUTES } from '../nav';

/** The matrix filter: every system, or one civilisation grouping. */
type SystemFilter = PortalCategoryId | 'all';

/**
 * Filter tabs with live counts derived from the catalogue (never hard-coded), so
 * adding a Phase-2 system updates the totals automatically.
 */
const FILTER_OPTIONS: ReadonlyArray<{ value: SystemFilter; label: string }> = [
  { value: 'all', label: `全体系 (${PORTAL_SYSTEMS.length})` },
  ...PORTAL_CATEGORIES.map((category) => ({
    value: category.id,
    label: `${category.label} (${PORTAL_SYSTEMS.filter((s) => s.category === category.id).length})`,
  })),
];

/**
 * Portal / 聚合测算大厅 — the observatory's front door.
 *
 * Section 1 pairs an atmospheric gateway headline with the live astronomical time
 * broadcast (`DailyTimePanel`, fed by the real meta true-solar-time + health
 * endpoints). Section 2 is the 16-system entry matrix: the live systems are real
 * links, the Phase-2 ones carry an honest build status; a category filter narrows
 * the grid. Neither count is written down here — `LIVE_SYSTEM_COUNT` derives them
 * from the catalogue, so wiring a new system cannot leave this note lying.
 *
 * The mockup's fabricated 今日天象 pillars (岁次干支 / 月相 / 行星落座 / 黄历宜忌)
 * and its 命盘收藏 / 历史记录 vault are intentionally omitted — those engines and
 * the client-side vault are not built in Phase 1, and the no-mock rule forbids
 * inventing them. The global `SiteFooter` already carries the integrity seals.
 */
export function PortalPage() {
  const [filter, setFilter] = useState<SystemFilter>('all');

  const systems =
    filter === 'all'
      ? PORTAL_SYSTEMS
      : PORTAL_SYSTEMS.filter((system) => system.category === filter);

  return (
    <div className="mx-auto flex w-full max-w-[1536px] flex-col gap-8 px-gutter py-8">
      <section className="grid grid-cols-1 items-stretch gap-gutter lg:grid-cols-12">
        <div className="lg:col-span-7">
          <Hero />
        </div>
        <div className="lg:col-span-5">
          <DailyTimePanel />
        </div>
      </section>

      <section id="matrix-section" className="flex scroll-mt-32 flex-col gap-6">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div className="flex flex-col gap-1.5">
            <span className="label-caps flex items-center gap-1.5 text-gold">
              <Icon name="seal" size={16} />
              MULTIVERSE ESOTERIC SYSTEMS
            </span>
            <h2 className="font-display text-2xl font-semibold text-ink sm:text-3xl">
              四大文明体系聚合矩阵
            </h2>
            <p className="max-w-2xl text-sm leading-relaxed text-ink-muted">
              集成华夏术数、西洋星历、印度吠陀与北欧如尼符文，{PORTAL_SYSTEMS.length} 维矩阵纵览命运坐标；当前{' '}
              <span className="text-gold-soft">{LIVE_SYSTEM_COUNT} 大核心体系</span> 已可真实起盘。
            </p>
          </div>
          <SegmentedControl
            options={FILTER_OPTIONS}
            value={filter}
            onChange={setFilter}
            ariaLabel="体系类目筛选"
          />
        </div>

        <div className="grid grid-cols-1 gap-gutter sm:grid-cols-2 lg:grid-cols-4">
          {systems.map((system) => (
            <SystemCard key={system.slug} system={system} />
          ))}
        </div>
      </section>
    </div>
  );
}

/** The atmospheric gateway headline with a decorative astrolabe and CTAs. */
function Hero() {
  return (
    <div className="panel-raised relative flex h-full flex-col justify-between gap-8 overflow-hidden p-6 sm:p-8">
      <Astrolabe />

      <div className="relative z-10 flex flex-col gap-4">
        <span className="label-caps inline-flex w-fit items-center gap-1.5 rounded-full border border-rim bg-gold/10 px-3 py-1 text-gold">
          <Icon name="sparkle" size={14} />
          瑞士星历 pyswisseph · 实时真太阳时校准
        </span>

        <div className="flex flex-col gap-2">
          <span className="label-caps">CELESTIAL HARMONY &amp; DIVINATION PORTAL</span>
          <h1 className="font-display text-4xl font-semibold leading-tight tracking-tight text-ink sm:text-5xl">
            洞见命运的几何密码
            <br />
            <span className="text-gold-bright text-glow-gold">探寻多重文明智慧</span>
          </h1>
        </div>

        <p className="max-w-xl text-base leading-relaxed text-ink-variant">
          跨越东方天干地支、西方黄道星历、古印度吠陀乔蒂什与北欧卢恩铭文。以数理严密校验古籍天机，拒绝模糊算力，呈现最精确的本命全息坐标。
        </p>
      </div>

      <div className="relative z-10 flex flex-col items-stretch gap-3 sm:flex-row sm:items-center">
        <Link to={ROUTES.baziNatal} className="btn-primary">
          <Icon name="compass" size={18} />
          一键快速起盘
        </Link>
        <a href="#matrix-section" className="btn-ghost">
          探索全部 {PORTAL_SYSTEMS.length} 大秘术类目
          <Icon name="chevronDown" size={16} />
        </a>
      </div>
    </div>
  );
}

/** Decorative wireframe astrolabe, positioned behind the hero copy. */
function Astrolabe() {
  return (
    <svg
      viewBox="0 0 200 200"
      fill="none"
      stroke="currentColor"
      aria-hidden="true"
      className="pointer-events-none absolute -bottom-24 -right-24 h-96 w-96 text-gold opacity-10"
    >
      <circle cx="100" cy="100" r="95" strokeDasharray="2 3" strokeWidth="0.75" />
      <circle cx="100" cy="100" r="82" strokeWidth="0.5" />
      <circle cx="100" cy="100" r="64" strokeWidth="1" />
      <circle cx="100" cy="100" r="38" strokeDasharray="4 2" strokeWidth="0.5" />
      <path d="M100 5 V195 M5 100 H195 M33 33 L167 167 M33 167 L167 33" strokeWidth="0.5" />
      <polygon
        points="100,20 120,60 170,70 130,105 140,155 100,130 60,155 70,105 30,70 80,60"
        strokeWidth="0.5"
      />
    </svg>
  );
}
