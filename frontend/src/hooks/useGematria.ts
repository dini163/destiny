import type { ApiError } from '../api/client';
import { computeGematria } from '../api/kabbalah';
import type { GematriaReading, GematriaRequest } from '../types/kabbalah';
import { useLastSuccessMutation } from './useLastSuccessMutation';

/**
 * Fold a word onto the Tree of Life via gematria, on demand.
 *
 * A mutation: each request weighs a fresh word, so it runs exactly when the user
 * submits rather than being cached under a shared key.
 *
 * Retained across resubmits via {@link useLastSuccessMutation}: the next word is being
 * weighed while the previous reading should still be on screen to compare against.
 */
export function useGematria() {
  return useLastSuccessMutation<GematriaReading, ApiError, GematriaRequest>(computeGematria);
}
