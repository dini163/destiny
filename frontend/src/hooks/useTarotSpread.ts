import { useMutation } from '@tanstack/react-query';

import type { ApiError } from '../api/client';
import { drawTarotSpread } from '../api/tarot';
import type { TarotSpreadRequest, TarotSpreadResponse } from '../types/tarot';

/**
 * Draw a tarot spread on demand.
 *
 * A mutation (never a cached query): each draw is an independent cryptographically
 * secure shuffle, so it must run exactly when the user asks and never be replayed
 * or refetched from cache.
 */
export function useTarotSpread() {
  return useMutation<TarotSpreadResponse, ApiError, TarotSpreadRequest>({
    mutationFn: (request) => drawTarotSpread(request),
  });
}
