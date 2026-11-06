import type { ZiweiAnalysisRequest, ZiweiAnalysisResponse, ZiweiChart, ZiweiRequest } from '../types/ziwei';
import { apiPost } from './client';

/** Compute a 紫微斗数 chart (命宫 / 五行局 / 十四主星 / 四化 / 十二宫 / 大限). */
export function computeZiwei(request: ZiweiRequest, signal?: AbortSignal): Promise<ZiweiChart> {
  return apiPost<ZiweiChart>('/ziwei/chart', request, signal);
}

/** Compute 紫微斗数 13 维度深度详批与断语 (14主星×13宫位、24双星、168主辅煞矩阵). */
export function computeZiweiAnalysis(
  request: ZiweiAnalysisRequest,
  signal?: AbortSignal
): Promise<ZiweiAnalysisResponse> {
  return apiPost<ZiweiAnalysisResponse>('/ziwei/analysis', request, signal);
}

