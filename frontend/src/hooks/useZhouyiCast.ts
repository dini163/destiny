import type { ApiError } from '../api/client';
import { castZhouyi } from '../api/zhouyi';
import type { ZhouyiCast, ZhouyiCastRequest } from '../types/zhouyi';
import { useLastSuccessMutation } from './useLastSuccessMutation';

/**
 * Cast a Zhouyi hexagram on demand.
 *
 * A mutation (never a cached query): coin/time casting is random, so each cast must
 * run exactly when the user asks and never be replayed or refetched from cache.
 *
 * {@link useLastSuccessMutation} keeps the cast hexagram visible during a re-cast — same
 * ruling as `useRunes`: retaining the last *displayed* result is not replaying it, the
 * next cast is still a fresh shuffle.
 */
export function useZhouyiCast() {
  return useLastSuccessMutation<ZhouyiCast, ApiError, ZhouyiCastRequest>(castZhouyi);
}
