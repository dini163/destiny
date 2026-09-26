import type { MeihuaCast, MeihuaCastRequest } from '../types/meihua';
import { apiPost } from './client';

/** Raise a Plum Blossom hexagram and read it through 体用生克. */
export function castMeihua(request: MeihuaCastRequest, signal?: AbortSignal): Promise<MeihuaCast> {
  return apiPost<MeihuaCast>('/meihua/cast', request, signal);
}
