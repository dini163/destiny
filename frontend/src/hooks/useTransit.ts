import type { ApiError } from '../api/client';
import { computeTransitChart } from '../api/transit';
import type { TransitChart, TransitRequest } from '../types/transit';
import { useLastSuccessMutation } from './useLastSuccessMutation';

/**
 * Compute a transit / secondary-progression / solar-arc overlay on demand.
 *
 * A mutation because it is triggered by an explicit submit from the birth-data
 * plus target-date console rather than fetched on render.
 *
 * {@link useLastSuccessMutation} keeps the previous overlay while a new target date is
 * requested: stepping through dates on one page is exactly the case the natal chart and
 * aspect list must not unload between the clicks.
 */
export function useTransit() {
  return useLastSuccessMutation<TransitChart, ApiError, TransitRequest>(computeTransitChart);
}
