import { createBrowserRouter, Navigate } from 'react-router-dom';

import { AppShell } from './components/layout/AppShell';
import { ROUTES } from './nav';
import { BaziLiushiPage } from './pages/BaziLiushiPage';
import { BaziLiuriPage } from './pages/BaziLiuriPage';
import { BaziHehunPage } from './pages/BaziHehunPage';
import { BaziNatalPage } from './pages/BaziNatalPage';
import { BaziTransitPage } from './pages/BaziTransitPage';
import { NamePage } from './pages/NamePage';
import { NorseRunesPage } from './pages/NorseRunesPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { NumerologyPage } from './pages/NumerologyPage';
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
 * any unmatched path falls through to the 404 page. `/bazi-transit` is routed but
 * deliberately absent from the nav bars: it is a sub-page of the BaZi chart, entered
 * from the 大运 block with the birth data carried in the query string (spec 决策 8).
 * `/bazi-hehun` is the one exception in this slice: 合婚 is a system of its own rather
 * than a drill-down under a single chart, so it does ship in `SECONDARY_NAV`
 * (spec 决策 10) and `以此造合婚` is only one optional entry point into it.
 */
export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <Navigate to={ROUTES.overview} replace /> },
      { path: segment(ROUTES.overview), element: <PortalPage /> },
      { path: segment(ROUTES.baziNatal), element: <BaziNatalPage /> },
      { path: segment(ROUTES.baziHehun), element: <BaziHehunPage /> },
      { path: segment(ROUTES.baziTransit), element: <BaziTransitPage /> },
      { path: segment(ROUTES.baziLiuri), element: <BaziLiuriPage /> },
      { path: segment(ROUTES.baziLiushi), element: <BaziLiushiPage /> },
      { path: segment(ROUTES.westernNatal), element: <WesternNatalPage /> },
      { path: segment(ROUTES.tarot), element: <TarotPage /> },
      { path: segment(ROUTES.zhouyi), element: <ZhouyiPage /> },
      { path: segment(ROUTES.nameMetric), element: <NamePage /> },
      { path: segment(ROUTES.numerologyMatrix), element: <NumerologyPage /> },
      { path: segment(ROUTES.norseRunes), element: <NorseRunesPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]);
