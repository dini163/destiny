import { createBrowserRouter, Navigate } from 'react-router-dom';

import { AppShell } from './components/layout/AppShell';
import { ROUTES } from './nav';
import { BaziNatalPage } from './pages/BaziNatalPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { PortalPage } from './pages/PortalPage';
import { TarotPage } from './pages/TarotPage';
import { WesternNatalPage } from './pages/WesternNatalPage';
import { ZhouyiPage } from './pages/ZhouyiPage';

/** Nested child paths are relative; strip the leading slash from absolute ROUTES. */
const segment = (absolutePath: string): string => absolutePath.replace(/^\//, '');

/**
 * Application router.
 *
 * The AppShell is the single layout route, so the persistent nav / status /
 * disclaimer chrome wraps every destination. The index redirects to the portal and
 * any unmatched path falls through to the 404 page.
 */
export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <Navigate to={ROUTES.overview} replace /> },
      { path: segment(ROUTES.overview), element: <PortalPage /> },
      { path: segment(ROUTES.baziNatal), element: <BaziNatalPage /> },
      { path: segment(ROUTES.westernNatal), element: <WesternNatalPage /> },
      { path: segment(ROUTES.tarot), element: <TarotPage /> },
      { path: segment(ROUTES.zhouyi), element: <ZhouyiPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]);
