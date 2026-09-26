import type { ApiError } from '../api/client';
import { drawLenormand } from '../api/lenormand';
import type { LenormandReading, LenormandRequest } from '../types/lenormand';
import { useLastSuccessMutation } from './useLastSuccessMutation';

/**
 * Draw a 雷诺曼 spread on demand.
 *
 * A mutation (never a cached query): each draw runs exactly when the user asks, so
 * the secrets-backed shuffle always produces a fresh spread.
 *
 * {@link useLastSuccessMutation} keeps the previous spread visible during a re-draw —
 * same ruling as `useRunes`: every console control is an input to the *next* draw, so
 * a blank board while in flight buys nothing and throws away what the reader is looking at.
 */
export function useLenormand() {
  return useLastSuccessMutation<LenormandReading, ApiError, LenormandRequest>(drawLenormand);
}
