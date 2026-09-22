import type { BaziLiushiRequest, BaziLiushiResult } from '../types/baziLiushi';
import { apiPost } from './client';

/** 推演一个八字日的十二时辰（`focus_hour_zhi` 所指那一格再给四段明细）。 */
export function fetchBaziLiushi(
  request: BaziLiushiRequest,
  signal?: AbortSignal,
): Promise<BaziLiushiResult> {
  return apiPost<BaziLiushiResult>('/bazi/liushi/day', request, signal);
}
