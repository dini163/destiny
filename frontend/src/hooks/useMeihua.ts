import type { ApiError } from '../api/client';
import { castMeihua } from '../api/meihua';
import type { MeihuaCast, MeihuaCastRequest } from '../types/meihua';
import { useLastSuccessMutation } from './useLastSuccessMutation';

/**
 * Raise a 梅花易数 hexagram on demand.
 *
 * A mutation (never a cached query): each raise runs exactly when the user asks,
 * so the 报数 / 时间 inputs always drive a fresh derivation.
 *
 * {@link useLastSuccessMutation} keeps the previous 卦 visible while the next cast is in
 * flight; the 体用 ledger below the board is only readable against what came before.
 */
export function useMeihua() {
  return useLastSuccessMutation<MeihuaCast, ApiError, MeihuaCastRequest>(castMeihua);
}
