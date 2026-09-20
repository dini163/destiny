import { useMutation } from '@tanstack/react-query';

import { computeBaziNatal } from '../api/bazi';
import type { ApiError } from '../api/client';
import type { BaziChart, BaziNatalRequest } from '../types/bazi';

/**
 * Compute a BaZi natal chart on demand.
 *
 * Modelled as a mutation because it is triggered by an explicit "排盘" submit from
 * the birth-data form rather than fetched on render.
 */
export function useBaziNatal() {
  return useMutation<BaziChart, ApiError, BaziNatalRequest>({
    mutationFn: (request) => computeBaziNatal(request),
  });
}
