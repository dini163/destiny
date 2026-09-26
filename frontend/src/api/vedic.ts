import type { VedicChart, VedicNatalRequest } from '../types/vedic';
import { apiPost } from './client';

/** Compute a Vedic (sidereal) natal chart with nakshatras and Vimshottari dasha. */
export function computeVedicNatal(
  request: VedicNatalRequest,
  signal?: AbortSignal,
): Promise<VedicChart> {
  return apiPost<VedicChart>('/vedic/natal', request, signal);
}
