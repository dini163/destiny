import { lazy, Suspense, type ReactNode } from 'react';
import { RouteError } from './components/ui/RouteError';
import { createBrowserRouter, Navigate } from 'react-router-dom';

import { AppShell } from './components/layout/AppShell';
import { ROUTES } from './nav';
const BaziLiushiPage = lazy(() =>
  import('./pages/BaziLiushiPage').then((module) => ({
    default: module.BaziLiushiPage,
  })),
);
const BaziLiuriPage = lazy(() =>
  import('./pages/BaziLiuriPage').then((module) => ({
    default: module.BaziLiuriPage,
  })),
);
const BaziHehunPage = lazy(() =>
  import('./pages/BaziHehunPage').then((module) => ({
    default: module.BaziHehunPage,
  })),
);
const BaziNatalPage = lazy(() =>
  import('./pages/BaziNatalPage').then((module) => ({
    default: module.BaziNatalPage,
  })),
);
const BaziTransitPage = lazy(() =>
  import('./pages/BaziTransitPage').then((module) => ({
    default: module.BaziTransitPage,
  })),
);
const KabbalahPage = lazy(() =>
  import('./pages/KabbalahPage').then((module) => ({
    default: module.KabbalahPage,
  })),
);
const LenormandPage = lazy(() =>
  import('./pages/LenormandPage').then((module) => ({
    default: module.LenormandPage,
  })),
);
const NamePage = lazy(() =>
  import('./pages/NamePage').then((module) => ({ default: module.NamePage })),
);
const NorseRunesPage = lazy(() =>
  import('./pages/NorseRunesPage').then((module) => ({
    default: module.NorseRunesPage,
  })),
);
const NotFoundPage = lazy(() =>
  import('./pages/NotFoundPage').then((module) => ({
    default: module.NotFoundPage,
  })),
);
const NumerologyPage = lazy(() =>
  import('./pages/NumerologyPage').then((module) => ({
    default: module.NumerologyPage,
  })),
);
const PlumBlossomPage = lazy(() =>
  import('./pages/PlumBlossomPage').then((module) => ({
    default: module.PlumBlossomPage,
  })),
);
const PortalPage = lazy(() =>
  import('./pages/PortalPage').then((module) => ({
    default: module.PortalPage,
  })),
);
const ProfilesPage = lazy(() =>
  import('./pages/ProfilesPage').then((module) => ({
    default: module.ProfilesPage,
  })),
);
const QimenPage = lazy(() =>
  import('./pages/QimenPage').then((module) => ({ default: module.QimenPage })),
);
const ReportPage = lazy(() =>
  import('./pages/ReportPage').then((module) => ({
    default: module.ReportPage,
  })),
);
const SynastryPage = lazy(() =>
  import('./pages/SynastryPage').then((module) => ({
    default: module.SynastryPage,
  })),
);
const TarotPage = lazy(() =>
  import('./pages/TarotPage').then((module) => ({ default: module.TarotPage })),
);
const TransitPage = lazy(() =>
  import('./pages/TransitPage').then((module) => ({
    default: module.TransitPage,
  })),
);
const VedicPage = lazy(() =>
  import('./pages/VedicPage').then((module) => ({ default: module.VedicPage })),
);
const WesternNatalPage = lazy(() =>
  import('./pages/WesternNatalPage').then((module) => ({
    default: module.WesternNatalPage,
  })),
);
const ZiweiPage = lazy(() =>
  import('./pages/ZiweiPage').then((module) => ({ default: module.ZiweiPage })),
);
const ZhouyiPage = lazy(() =>
  import('./pages/ZhouyiPage').then((module) => ({
    default: module.ZhouyiPage,
  })),
);

/** Nested child paths are relative; strip the leading slash from absolute ROUTES. */
const segment = (absolutePath: string): string =>
  absolutePath.replace(/^\//, '');

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
const loading = (
  <p className="page-loading" role="status">
    正在打开页面…
  </p>
);
const deferred = (element: ReactNode) => (
  <Suspense fallback={loading}>{element}</Suspense>
);

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    errorElement: <RouteError />,
    children: [
      { index: true, element: <Navigate to={ROUTES.overview} replace /> },
      { path: segment(ROUTES.overview), element: deferred(<PortalPage />) },
      { path: segment(ROUTES.baziNatal), element: deferred(<BaziNatalPage />) },
      { path: segment(ROUTES.baziHehun), element: deferred(<BaziHehunPage />) },
      {
        path: segment(ROUTES.baziTransit),
        element: deferred(<BaziTransitPage />),
      },
      { path: segment(ROUTES.baziLiuri), element: deferred(<BaziLiuriPage />) },
      {
        path: segment(ROUTES.baziLiushi),
        element: deferred(<BaziLiushiPage />),
      },
      {
        path: segment(ROUTES.westernNatal),
        element: deferred(<WesternNatalPage />),
      },
      { path: segment(ROUTES.transit), element: deferred(<TransitPage />) },
      { path: segment(ROUTES.synastry), element: deferred(<SynastryPage />) },
      { path: segment(ROUTES.tarot), element: deferred(<TarotPage />) },
      { path: segment(ROUTES.lenormand), element: deferred(<LenormandPage />) },
      { path: segment(ROUTES.kabbalah), element: deferred(<KabbalahPage />) },
      { path: segment(ROUTES.zhouyi), element: deferred(<ZhouyiPage />) },
      { path: segment(ROUTES.ziwei), element: deferred(<ZiweiPage />) },
      { path: segment(ROUTES.qimen), element: deferred(<QimenPage />) },
      {
        path: segment(ROUTES.plumBlossom),
        element: deferred(<PlumBlossomPage />),
      },
      { path: segment(ROUTES.nameMetric), element: deferred(<NamePage />) },
      {
        path: segment(ROUTES.numerologyMatrix),
        element: deferred(<NumerologyPage />),
      },
      {
        path: segment(ROUTES.norseRunes),
        element: deferred(<NorseRunesPage />),
      },
      { path: segment(ROUTES.vedic), element: deferred(<VedicPage />) },
      { path: segment(ROUTES.profiles), element: deferred(<ProfilesPage />) },
      { path: '/report/:product', element: deferred(<ReportPage />) },
      { path: '*', element: deferred(<NotFoundPage />) },
    ],
  },
]);
