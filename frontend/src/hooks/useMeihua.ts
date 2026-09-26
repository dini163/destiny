import { useMutation } from '@tanstack/react-query';

import type { ApiError } from '../api/client';
import { castMeihua } from '../api/meihua';
import type { MeihuaCast, MeihuaCastRequest } from '../types/meihua';

/**
 * Raise a 梅花易数 hexagram on demand.
 *
 * A mutation (never a cached query): each raise runs exactly when the user asks,
 * so the 报数 / 时间 inputs always drive a fresh derivation.
 */
export function useMeihua() {
  return useMutation<MeihuaCast, ApiError, MeihuaCastRequest>({
    mutationFn: (request) => castMeihua(request),
  });
}
