import { useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';

import { SiteFooter } from './SiteFooter';
import { SiteHeader } from './SiteHeader';

/**
 * The persistent global App Shell (PRD §2): the top multi-civilization nav and
 * status bar, the routed page through `<Outlet/>`, and the footer disclaimer with
 * its astronomical seals. No sidebar — every destination shares this one chrome.
 */
export function AppShell() {
  const { pathname } = useLocation();

  // Reset scroll on navigation so each destination starts at the top of its chart.
  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [pathname]);

  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <main className="flex-1 pt-28">
        <Outlet />
      </main>
      <SiteFooter />
    </div>
  );
}
