import type { ApiError } from '../api/client';
import { castQimen } from '../api/qimen';
import type { QimenChart, QimenRequest } from '../types/qimen';
import { useLastSuccessMutation } from './useLastSuccessMutation';

/**
 * Raise a 奇门遁甲 局 on demand.
 *
 * A mutation (never a cached query): each 起局 runs exactly when the user asks, so the
 * 用事时辰 / 占问 inputs always drive a fresh derivation.
 *
 * {@link useLastSuccessMutation} keeps the previous 局 on the 九宫格 while the next cast
 * runs — changing the 时辰 changes every board, so the old one is the only reference
 * the reader has left mid-flight.
 */
export function useQimen() {
  return useLastSuccessMutation<QimenChart, ApiError, QimenRequest>(castQimen);
}
