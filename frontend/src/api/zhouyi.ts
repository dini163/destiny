import type { ZhouyiCast, ZhouyiCastRequest } from '../types/zhouyi';
import { apiPost } from './client';

export interface YangzhaiMeaning {
  hexagram: string;
  upper_trigram: string;
  lower_trigram: string;
  person_role: string;
  position_direction: string;
  is_name_position_equal: boolean;
  summary: string;
  principle: string;
}

export interface ZhouyiYangzhaiResponse {
  hexagram_name: string;
  meaning: YangzhaiMeaning | null;
}

/** Cast six lines and derive the primary, changed and nuclear hexagrams. */
export function castZhouyi(request: ZhouyiCastRequest, signal?: AbortSignal): Promise<ZhouyiCast> {
  return apiPost<ZhouyiCast>('/zhouyi/cast', request, signal);
}

/** Query the spatial and family position reading for a hexagram (阳宅化命方位取象). */
export function computeZhouyiYangzhai(
  hexagram_name: string,
  signal?: AbortSignal,
): Promise<ZhouyiYangzhaiResponse> {
  return apiPost<ZhouyiYangzhaiResponse>('/zhouyi/yangzhai', { hexagram_name }, signal);
}
