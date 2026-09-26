import type { TransitChart, TransitRequest } from '../types/transit';
import { apiPost } from './client';

/** Project transits, secondary progressions and solar arc onto a natal chart. */
export function computeTransitChart(
  request: TransitRequest,
  signal?: AbortSignal,
): Promise<TransitChart> {
  return apiPost<TransitChart>('/transit/chart', request, signal);
}
