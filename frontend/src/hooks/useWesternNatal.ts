import { useMutation } from '@tanstack/react-query';

import type { ApiError } from '../api/client';
import { computeWesternNatal } from '../api/western';
import type { WesternChart, WesternNatalRequest } from '../types/western';

/**
 * Compute a Western natal chart on demand.
 *
 * Modelled as a mutation because it is triggered by an explicit submit from the
 * birth-data form rather than fetched on render.
 */
export function useWesternNatal() {
  return useMutation<WesternChart, ApiError, WesternNatalRequest>({
    mutationFn: (request) => computeWesternNatal(request),
  });
}
