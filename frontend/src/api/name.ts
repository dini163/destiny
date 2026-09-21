import type { NameAnalysis, NameAnalyzeRequest } from '../types/name';
import { apiPost } from './client';

/** 核定康熙笔画并推出五格 / 三才 / 综合指数。 */
export function analyzeName(
  request: NameAnalyzeRequest,
  signal?: AbortSignal,
): Promise<NameAnalysis> {
  return apiPost<NameAnalysis>('/name/analyze', request, signal);
}
