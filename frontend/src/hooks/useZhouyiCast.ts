import { useMutation } from '@tanstack/react-query';

import type { ApiError } from '../api/client';
import { castZhouyi } from '../api/zhouyi';
import type { ZhouyiCast, ZhouyiCastRequest } from '../types/zhouyi';

/**
 * Cast a Zhouyi hexagram on demand.
 *
 * A mutation (never a cached query): coin/time casting is random, so each cast must
 * run exactly when the user asks and never be replayed or refetched from cache.
 */
export function useZhouyiCast() {
  return useMutation<ZhouyiCast, ApiError, ZhouyiCastRequest>({
    mutationFn: (request) => castZhouyi(request),
  });
}
