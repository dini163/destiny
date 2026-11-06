import type { BaziChart, BaziNatalRequest } from '../types/bazi';
import { apiPost } from './client';

export interface BaziZangfuItem {
  type: string;
  label: string;
  organs: string;
  meridians: string;
  focus: string;
  advice: string;
}

export interface BaziZangfuResponse {
  items: BaziZangfuItem[];
}

/** Compute a BaZi natal chart from birth data (applies True Solar Time by default). */
export function computeBaziNatal(
  request: BaziNatalRequest,
  signal?: AbortSignal,
): Promise<BaziChart> {
  return apiPost<BaziChart>('/bazi/natal', request, signal);
}

/** Compute meridian and organ guidance (子午流注) from the four pillars' branches. */
export function computeBaziZangfu(
  branches: string[],
  signal?: AbortSignal,
): Promise<BaziZangfuResponse> {
  return apiPost<BaziZangfuResponse>('/bazi/zangfu', { branches }, signal);
}
