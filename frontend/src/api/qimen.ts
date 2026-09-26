import type { QimenChart, QimenRequest } from '../types/qimen';
import { apiPost } from './client';

/** Raise a 奇门遁甲 board for the 用事时辰 (defaults to now). */
export function castQimen(request: QimenRequest, signal?: AbortSignal): Promise<QimenChart> {
  return apiPost<QimenChart>('/qimen/chart', request, signal);
}
