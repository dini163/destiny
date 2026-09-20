import { RouterProvider } from 'react-router-dom';

import { router } from './router';

/**
 * Application root — mounts the router.
 *
 * The persistent AppShell layout (nav, status bar, footer disclaimer) and all
 * route definitions live in `router.tsx`. TanStack Query is layered on in Step 10
 * when the API client and query hooks arrive. The `v7_startTransition` future flag
 * opts into React Router v7's transition-wrapped state updates early (React 18).
 */
export default function App() {
  return <RouterProvider router={router} future={{ v7_startTransition: true }} />;
}
