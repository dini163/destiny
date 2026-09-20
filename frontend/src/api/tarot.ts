import type { TarotSpreadRequest, TarotSpreadResponse } from '../types/tarot';
import { apiPost } from './client';

/** Draw and interpret a tarot spread using a cryptographically secure shuffle. */
export function drawTarotSpread(
  request: TarotSpreadRequest,
  signal?: AbortSignal,
): Promise<TarotSpreadResponse> {
  return apiPost<TarotSpreadResponse>('/tarot/spread', request, signal);
}
