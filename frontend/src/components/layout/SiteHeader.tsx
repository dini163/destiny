import { useEffect, useRef } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import { ROUTES, SECONDARY_NAV } from '../../nav';
import { useI18n } from '../../i18n/context';
import { Icon } from '../ui/Icon';
import { ThemeToggle } from '../ui/ThemeToggle';
import { BrandMark } from './BrandMark';
import { LocaleSwitcher } from './LocaleSwitcher';

/** Native dialog supplies focus trapping, Escape and focus restoration for the catalogue. */
export function SiteHeader() {
  const dialog = useRef<HTMLDialogElement>(null);
  const location = useLocation();
  const { t } = useI18n();
  useEffect(() => {
    if (dialog.current?.open) dialog.current.close();
  }, [location.pathname, location.hash]);
  return (
    <header className="site-header">
      <Link to={ROUTES.overview} aria-label={t('Destiny 测算大厅')}>
        <BrandMark />
      </Link>
      <nav className="header-primary" aria-label={t('主导航')}>
        <NavLink to={ROUTES.overview}>{t('发现')}</NavLink>
        <Link to={`${ROUTES.overview}#questions`}>{t('从问题开始')}</Link>
        <Link to="/report/r2?sample=1">{t('报告样例')}</Link>
        <button type="button" onClick={() => dialog.current?.showModal()}>
          {t('探索全部体系')} <span aria-hidden="true">↗</span>
        </button>
      </nav>
      <div className="header-actions">
        <LocaleSwitcher />
        <ThemeToggle />
        <Link
          className="archive-link"
          to={ROUTES.profiles}
          aria-label={t('我的档案')}
        >
          <Icon name="vault" size={17} />
          <span>{t('我的档案')}</span>
        </Link>
        <button
          className="catalogue-toggle"
          type="button"
          aria-label={t('打开体系导航')}
          onClick={() => dialog.current?.showModal()}
        >
          <svg
            viewBox="0 0 24 24"
            width="23"
            height="23"
            fill="none"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path d="M4 8h16M4 16h16" />
          </svg>
        </button>
      </div>
      <dialog
        ref={dialog}
        className="catalogue-dialog"
        aria-labelledby="catalogue-title"
      >
        <div className="dialog-heading">
          <h2 id="catalogue-title">{t('以你熟悉的方式，开始探索。')}</h2>
          <button
            type="button"
            aria-label={t('关闭体系导航')}
            onClick={() => dialog.current?.close()}
          >
            <Icon name="close" />
          </button>
        </div>
        <nav aria-label={t('全体系导航')}>
          {/* On mobile the primary bar is hidden; the catalogue dialog is the only
              nav, so surface the two desktop-only destinations here or they become
              unreachable. */}
          <section>
            <h3>{t('快捷入口')}</h3>
            <div className="catalogue-grid">
              <Link to={`${ROUTES.overview}#questions`}>
                {t('从问题开始')}
                <span aria-hidden="true">↗</span>
              </Link>
              <Link to="/report/r2?sample=1">
                {t('报告样例')}
                <span aria-hidden="true">↗</span>
              </Link>
            </div>
          </section>
          {SECONDARY_NAV.map((group) => (
            <section key={group.title}>
              <h3>{t(group.title)}</h3>
              <div className="catalogue-grid">
                {group.items.map((item) => (
                  <NavLink key={item.slug} to={item.to}>
                    {t(item.label)}
                    <span aria-hidden="true">↗</span>
                  </NavLink>
                ))}
              </div>
            </section>
          ))}
        </nav>
      </dialog>
    </header>
  );
}
