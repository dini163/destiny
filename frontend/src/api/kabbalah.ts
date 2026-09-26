import type { GematriaReading, GematriaRequest, KabbalahTree } from '../types/kabbalah';
import { apiGet, apiPost } from './client';

/** Fetch the complete Tree of Life reference map (fixed Golden Dawn content). */
export function getKabbalahTree(signal?: AbortSignal): Promise<KabbalahTree> {
  return apiGet<KabbalahTree>('/kabbalah/tree', undefined, signal);
}

/** Fold a word onto the Tree via English gematria. */
export function computeGematria(request: GematriaRequest, signal?: AbortSignal): Promise<GematriaReading> {
  return apiPost<GematriaReading>('/kabbalah/gematria', request, signal);
}
