import { computeBaziNatal } from '../api/bazi';
import type { ApiError } from '../api/client';
import type { BaziChart, BaziNatalRequest } from '../types/bazi';
import { useLastSuccessMutation } from './useLastSuccessMutation';

/**
 * Compute a BaZi natal chart on demand.
 *
 * Modelled as a mutation because it is triggered by an explicit "排盘" submit from
 * the birth-data form rather than fetched on render.
 *
 * {@link useLastSuccessMutation} keeps the chart already on screen while a resubmit is
 * in flight: every console field is an input to the *next* chart, so a reroll should
 * not blank the four pillars the reader is still comparing against.
 */
export function useBaziNatal() {
  return useLastSuccessMutation<BaziChart, ApiError, BaziNatalRequest>(computeBaziNatal);
}
