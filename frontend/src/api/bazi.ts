import type { BaziChart, BaziNatalRequest } from '../types/bazi';
import { apiPost } from './client';

/** Compute a BaZi natal chart from birth data (applies True Solar Time by default). */
export function computeBaziNatal(
  request: BaziNatalRequest,
  signal?: AbortSignal,
): Promise<BaziChart> {
  return apiPost<BaziChart>('/bazi/natal', request, signal);
}
