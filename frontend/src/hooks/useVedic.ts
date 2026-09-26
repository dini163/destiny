import type { ApiError } from '../api/client';
import { computeVedicNatal } from '../api/vedic';
import type { VedicChart, VedicNatalRequest } from '../types/vedic';
import { useLastSuccessMutation } from './useLastSuccessMutation';

/**
 * Compute a Vedic (sidereal) natal chart on demand.
 *
 * A mutation because it is triggered by an explicit submit from the birth-data
 * plus target-date console rather than fetched on render.
 *
 * {@link useLastSuccessMutation} keeps the previous 盘 visible during a resubmit — the
 * ayanamsa / zodiac toggles on this console each recast the whole chart, and the reader
 * is flipping them precisely to see what moved.
 */
export function useVedic() {
  return useLastSuccessMutation<VedicChart, ApiError, VedicNatalRequest>(computeVedicNatal);
}
