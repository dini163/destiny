import { useMutation } from '@tanstack/react-query';

import type { ApiError } from '../api/client';
import { castQimen } from '../api/qimen';
import type { QimenChart, QimenRequest } from '../types/qimen';

/**
 * Raise a 奇门遁甲 局 on demand.
 *
 * A mutation (never a cached query): each 起局 runs exactly when the user asks, so the
 * 用事时辰 / 占问 inputs always drive a fresh derivation.
 */
export function useQimen() {
  return useMutation<QimenChart, ApiError, QimenRequest>({
    mutationFn: (request) => castQimen(request),
  });
}
