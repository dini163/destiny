import { QueryClient } from '@tanstack/react-query';

/**
 * Application-wide TanStack Query client.
 *
 * Defaults are tuned for a computation API: reads (cities, True Solar Time,
 * health) are cached and never refetched on window focus, while the chart/draw
 * POSTs are modelled as mutations that do not retry automatically — a tarot or
 * Zhouyi result must never be silently re-rolled by a background retry.
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      gcTime: 10 * 60 * 1000,
      refetchOnWindowFocus: false,
      retry: 1,
    },
    mutations: {
      retry: 0,
    },
  },
});
