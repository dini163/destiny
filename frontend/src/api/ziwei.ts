import type { ZiweiChart, ZiweiRequest } from '../types/ziwei';
import { apiPost } from './client';

/** Compute a 紫微斗数 chart (命宫 / 五行局 / 十四主星 / 四化 / 十二宫 / 大限). */
export function computeZiwei(request: ZiweiRequest, signal?: AbortSignal): Promise<ZiweiChart> {
  return apiPost<ZiweiChart>('/ziwei/chart', request, signal);
}
