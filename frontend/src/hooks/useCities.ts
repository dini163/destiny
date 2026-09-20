import { useQuery } from '@tanstack/react-query';

import type { ApiError } from '../api/client';
import { searchCities } from '../api/meta';
import type { City } from '../types/common';

/**
 * Search geocoded cities as the user types in the location picker.
 *
 * Disabled until a non-empty fragment is present; results are cached per term so
 * re-typing a previous fragment is instant.
 */
export function useCities(q: string) {
  const term = q.trim();
  return useQuery<City[], ApiError>({
    queryKey: ['cities', term],
    queryFn: ({ signal }) => searchCities(term, signal),
    enabled: term.length > 0,
  });
}
