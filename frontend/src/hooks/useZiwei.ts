import { useMutation } from '@tanstack/react-query';

import { computeZiwei } from '../api/ziwei';
import type { ApiError } from '../api/client';
import type { ZiweiChart, ZiweiRequest } from '../types/ziwei';

/**
 * Compute a 紫微斗数 chart on demand.
 *
 * A mutation (never a cached query): the board is cast exactly when the user
 * submits the birth-data console, so every chart reflects the current inputs.
 */
export function useZiwei() {
  return useMutation<ZiweiChart, ApiError, ZiweiRequest>({
    mutationFn: (request) => computeZiwei(request),
  });
}
