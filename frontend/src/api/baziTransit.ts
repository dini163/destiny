import type { BaziTransitRequest, BaziTransitResult } from '../types/baziTransit';
import { apiPost } from './client';

/** 推演一段流年（`focus_year` 所指之年再下钻到十二节气流月）。 */
export function fetchBaziTransit(
  request: BaziTransitRequest,
  signal?: AbortSignal,
): Promise<BaziTransitResult> {
  return apiPost<BaziTransitResult>('/bazi/liuyue', request, signal);
}
