import type { BaziLiuriRequest, BaziLiuriResult } from '../types/baziLiuri';
import { apiPost } from './client';

/** 推演一整个节气月的逐日矩阵（`focus_date` 所指之日再给三段明细）。 */
export function fetchBaziLiuri(
  request: BaziLiuriRequest,
  signal?: AbortSignal,
): Promise<BaziLiuriResult> {
  return apiPost<BaziLiuriResult>('/bazi/liuri/matrix', request, signal);
}
