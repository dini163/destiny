import { useMutation } from '@tanstack/react-query';

import type { ApiError } from '../api/client';
import { computeVedicNatal } from '../api/vedic';
import type { VedicChart, VedicNatalRequest } from '../types/vedic';

/**
 * Compute a Vedic (sidereal) natal chart on demand.
 *
 * A mutation because it is triggered by an explicit submit from the birth-data
 * plus target-date console rather than fetched on render.
 */
export function useVedic() {
  return useMutation<VedicChart, ApiError, VedicNatalRequest>({
    mutationFn: (request) => computeVedicNatal(request),
  });
}
