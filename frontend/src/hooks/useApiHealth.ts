import { useQuery } from '@tanstack/react-query';

import type { ApiError } from '../api/client';
import { getHealth } from '../api/meta';
import type { HealthResponse } from '../types/common';

/**
 * Poll the backend liveness probe so the portal can surface engine status.
 *
 * Refreshes once a minute; a failure is not fatal — the caller simply reports the
 * computation API as unreachable instead of blocking the UI.
 */
export function useApiHealth() {
  return useQuery<HealthResponse, ApiError>({
    queryKey: ['health'],
    queryFn: ({ signal }) => getHealth(signal),
    staleTime: 30_000,
    refetchInterval: 60_000,
  });
}
