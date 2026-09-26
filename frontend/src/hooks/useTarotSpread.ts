import type { ApiError } from '../api/client';
import { drawTarotSpread } from '../api/tarot';
import type { TarotSpreadRequest, TarotSpreadResponse } from '../types/tarot';
import { useLastSuccessMutation } from './useLastSuccessMutation';

/**
 * Draw a tarot spread on demand.
 *
 * A mutation (never a cached query): each draw is an independent cryptographically
 * secure shuffle, so it must run exactly when the user asks and never be replayed
 * or refetched from cache.
 *
 * {@link useLastSuccessMutation} keeps the drawn spread visible while a re-draw is in
 * flight — same ruling as `useRunes`: retention is a display concern, not a replay, so
 * the next draw is still a fresh CSPRNG shuffle.
 */
export function useTarotSpread() {
  return useLastSuccessMutation<TarotSpreadResponse, ApiError, TarotSpreadRequest>(
    drawTarotSpread,
  );
}
