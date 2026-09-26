import { Fragment } from 'react';
import { Link, NavLink } from 'react-router-dom';

import { PRIMARY_NAV, ROUTES, SECONDARY_NAV, type NavGroup, type NavItem } from '../../nav';
import { Icon, type IconName } from '../ui/Icon';
import { BrandMark } from './BrandMark';
import { EpochBadge, UtcClock } from './StatusClock';

/**
 * Persistent top navigation (PRD §2): brand, primary Phase-1 bar, live status
 * telemetry and utility shortcuts on row 1; the full multi-civilization catalog on
 * row 2. Fixed to the viewport so every route shares one chrome.
 */
export function SiteHeader() {
  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-rim bg-void/90 shadow-[0_4px_24px_rgba(0,0,0,0.45)] backdrop-blur-xl">
      <div className="mx-auto flex h-28 w-full max-w-[1536px] flex-col justify-between px-gutter">
        <div className="flex h-16 items-center justify-between gap-gutter">
          <Link to={ROUTES.overview} className="shrink-0" aria-label="Destiny 测算大厅">
            <BrandMark />
          </Link>

          <nav className="hidden items-center gap-1 xl:flex" aria-label="主导航">
            {PRIMARY_NAV.map((item) => (
              <PrimaryLink key={item.slug} item={item} />
            ))}
          </nav>

          <div className="flex shrink-0 items-center gap-3">
            <UtcClock />
            <UtilityButton icon="history" label="历史测算记录" />
            <UtilityButton icon="vault" label="命盘收藏夹" />
          </div>
        </div>

        <div className="flex h-12 items-center justify-between gap-gutter">
          <nav
            className="flex items-center gap-1 overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
            aria-label="全体系导航"
          >
            {SECONDARY_NAV.map((group, index) => (
              <SecondaryGroup key={group.title} group={group} first={index === 0} />
            ))}
          </nav>
          <EpochBadge />
        </div>
      </div>
    </header>
  );
}

const PRIMARY_BASE = 'rounded-element px-3 py-1.5 text-sm transition-colors';
const PRIMARY_ACTIVE = 'bg-gold/15 font-semibold text-gold-bright';
const PRIMARY_IDLE = 'text-ink-variant hover:bg-surface-raised hover:text-ink';

function PrimaryLink({ item }: { item: NavItem }) {
  if (item.to === null) return null;
  return (
    <NavLink
      to={item.to}
      className={({ isActive }) => `${PRIMARY_BASE} ${isActive ? PRIMARY_ACTIVE : PRIMARY_IDLE}`}
    >
      {item.label}
    </NavLink>
  );
}

function SecondaryGroup({ group, first }: { group: NavGroup; first: boolean }) {
  return (
    <Fragment>
      {!first && <span className="mx-1.5 h-3.5 w-px shrink-0 bg-gold/25" />}
      <span className="label-caps mr-1.5 shrink-0 select-none font-bold text-gold">
        {group.title}
      </span>
      {group.items.map((item) => (
        <SecondaryLink key={item.slug} item={item} />
      ))}
    </Fragment>
  );
}

const SECONDARY_BASE = 'shrink-0 rounded-element px-2 py-1 text-xs transition-colors';
const SECONDARY_ACTIVE = 'bg-surface-raised font-medium text-gold-soft';
const SECONDARY_IDLE = 'text-ink-variant hover:bg-surface-raised hover:text-ink';

function SecondaryLink({ item }: { item: NavItem }) {
  if (item.to === null) {
    return (
      <span
        className={`${SECONDARY_BASE} cursor-not-allowed text-ink-muted/50`}
        title="二期上线 · 敬请期待"
      >
        {item.label}
      </span>
    );
  }
  return (
    <NavLink
      to={item.to}
      className={({ isActive }) =>
        `${SECONDARY_BASE} ${isActive ? SECONDARY_ACTIVE : SECONDARY_IDLE}`
      }
    >
      {item.label}
    </NavLink>
  );
}

function UtilityButton({ icon, label }: { icon: IconName; label: string }) {
  return (
    <button
      type="button"
      disabled
      title={`${label} · 二期上线`}
      aria-label={label}
      className="flex h-9 w-9 items-center justify-center rounded-element border border-rim bg-surface/60 text-ink-muted transition-colors disabled:cursor-not-allowed disabled:opacity-60"
    >
      <Icon name={icon} size={18} />
    </button>
  );
}
