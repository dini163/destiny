import type { BaziHehunRequest, BaziHehunResult } from '../types/baziHehun';
import { apiPost } from './client';

/** 双人合盘（`POST /api/v1/bazi/hehun`）：一次请求给全一页。 */
export function fetchBaziHehun(
  request: BaziHehunRequest,
  signal?: AbortSignal,
): Promise<BaziHehunResult> {
  return apiPost<BaziHehunResult>('/bazi/hehun', request, signal);
}
