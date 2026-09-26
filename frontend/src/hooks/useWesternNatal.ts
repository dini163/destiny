import type { ApiError } from '../api/client';
import { computeWesternNatal } from '../api/western';
import type { WesternChart, WesternNatalRequest } from '../types/western';
import { useLastSuccessMutation } from './useLastSuccessMutation';

/**
 * Compute a Western natal chart on demand.
 *
 * Modelled as a mutation because it is triggered by an explicit submit from the
 * birth-data form rather than fetched on render.
 *
 * {@link useLastSuccessMutation} keeps the previous chart on screen while a resubmit is
 * in flight: the house-system and latitude controls recast the whole wheel, so a blank
 * mid-flight wheel is the one state that has no reading value.
 */
export function useWesternNatal() {
  return useLastSuccessMutation<WesternChart, ApiError, WesternNatalRequest>(computeWesternNatal);
}
