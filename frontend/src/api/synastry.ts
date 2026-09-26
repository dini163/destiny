import type { SynastryChart, SynastryRequest } from '../types/synastry';
import { apiPost } from './client';

/** Compare two natal charts: synastry aspects, composite midpoints and 相契度. */
export function computeSynastryChart(
  request: SynastryRequest,
  signal?: AbortSignal,
): Promise<SynastryChart> {
  return apiPost<SynastryChart>('/synastry/chart', request, signal);
}
