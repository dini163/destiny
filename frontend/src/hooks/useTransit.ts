import { useMutation } from '@tanstack/react-query';

import type { ApiError } from '../api/client';
import { computeTransitChart } from '../api/transit';
import type { TransitChart, TransitRequest } from '../types/transit';

/**
 * Compute a transit / secondary-progression / solar-arc overlay on demand.
 *
 * A mutation because it is triggered by an explicit submit from the birth-data
 * plus target-date console rather than fetched on render.
 */
export function useTransit() {
  return useMutation<TransitChart, ApiError, TransitRequest>({
    mutationFn: (request) => computeTransitChart(request),
  });
}
