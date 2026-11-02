import { QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider } from 'react-router-dom';

import { queryClient } from './api/queryClient';
import { router } from './router';

/**
 * Application root — mounts the data layer and the router.
 *
 * `QueryClientProvider` supplies the shared TanStack Query cache used by the API
 * hooks; the persistent AppShell layout (nav, status bar, footer disclaimer) and
 * all route definitions live in `router.tsx`. The `v7_startTransition` future flag
 * opts into React Router v7's transition-wrapped state updates early (React 18).
 */
export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}
