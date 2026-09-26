import { useMutation } from '@tanstack/react-query';

import type { ApiError } from '../api/client';
import { drawLenormand } from '../api/lenormand';
import type { LenormandReading, LenormandRequest } from '../types/lenormand';

/**
 * Draw a 雷诺曼 spread on demand.
 *
 * A mutation (never a cached query): each draw runs exactly when the user asks, so
 * the secrets-backed shuffle always produces a fresh spread.
 */
export function useLenormand() {
  return useMutation<LenormandReading, ApiError, LenormandRequest>({
    mutationFn: (request) => drawLenormand(request),
  });
}
