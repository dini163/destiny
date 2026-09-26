import type { LenormandReading, LenormandRequest } from '../types/lenormand';
import { apiPost } from './client';

/** Draw and read a Lenormand spread (single / line / box / grand tableau). */
export function drawLenormand(request: LenormandRequest, signal?: AbortSignal): Promise<LenormandReading> {
  return apiPost<LenormandReading>('/lenormand/draw', request, signal);
}
