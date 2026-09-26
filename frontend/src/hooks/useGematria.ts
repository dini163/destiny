import { useMutation } from '@tanstack/react-query';

import type { ApiError } from '../api/client';
import { computeGematria } from '../api/kabbalah';
import type { GematriaReading, GematriaRequest } from '../types/kabbalah';

/**
 * Fold a word onto the Tree of Life via gematria, on demand.
 *
 * A mutation: each request weighs a fresh word, so it runs exactly when the user
 * submits rather than being cached under a shared key.
 */
export function useGematria() {
  return useMutation<GematriaReading, ApiError, GematriaRequest>({
    mutationFn: (request) => computeGematria(request),
  });
}
