import { QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider } from 'react-router-dom';

import { queryClient } from './api/queryClient';
import { LocaleProvider } from './i18n/context';
import { router } from './router';

/**
 * Application root — mounts the data layer, locale context and the router.
 *
 * `QueryClientProvider` supplies the shared TanStack Query cache used by the API
 * hooks; `LocaleProvider` owns the active UI language and its `destiny.locale.v1`
 * persistence so every chrome element below can pull `t()` from context. The
 * persistent AppShell layout (nav, status bar, footer disclaimer) and all route
 * definitions live in `router.tsx`. The `v7_startTransition` future flag opts
 * into React Router v7's transition-wrapped state updates early (React 18).
 */
export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <LocaleProvider>
        <RouterProvider router={router} />
      </LocaleProvider>
    </QueryClientProvider>
  );
}
