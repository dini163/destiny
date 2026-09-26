import { useQuery } from '@tanstack/react-query';

import type { ApiError } from '../api/client';
import { getKabbalahTree } from '../api/kabbalah';
import type { KabbalahTree } from '../types/kabbalah';

/**
 * Fetch the Tree of Life reference map.
 *
 * A cached query (never a mutation): the map is fixed content that never changes
 * between visits, so it is fetched once and kept warm for the whole session.
 */
export function useKabbalahTree() {
  return useQuery<KabbalahTree, ApiError>({
    queryKey: ['kabbalah-tree'],
    queryFn: ({ signal }) => getKabbalahTree(signal),
    staleTime: Infinity,
  });
}
