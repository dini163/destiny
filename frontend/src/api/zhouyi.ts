import type { ZhouyiCast, ZhouyiCastRequest } from '../types/zhouyi';
import { apiPost } from './client';

/** Cast six lines and derive the primary, changed and nuclear hexagrams. */
export function castZhouyi(request: ZhouyiCastRequest, signal?: AbortSignal): Promise<ZhouyiCast> {
  return apiPost<ZhouyiCast>('/zhouyi/cast', request, signal);
}
