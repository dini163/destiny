import type { WesternChart, WesternNatalRequest } from '../types/western';
import { apiPost } from './client';

/** Compute a Western natal chart (planets, houses, angles, aspects). */
export function computeWesternNatal(
  request: WesternNatalRequest,
  signal?: AbortSignal,
): Promise<WesternChart> {
  return apiPost<WesternChart>('/western/natal', request, signal);
}
