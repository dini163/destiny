import { useQuery } from '@tanstack/react-query';

import { ApiError } from '../api/client';
import { getTrueSolarTime, type TrueSolarTimeParams } from '../api/meta';
import type { TrueSolarTimeResponse } from '../types/common';

/**
 * Preview the True Solar Time correction for the input console's TST badge.
 *
 * Pass `null` to disable the query until the birth date, time and longitude are all
 * known; the badge then stays hidden rather than showing a partial correction.
 */
export function useTrueSolarTime(params: TrueSolarTimeParams | null) {
  return useQuery<TrueSolarTimeResponse, ApiError>({
    queryKey: ['true-solar-time', params],
    queryFn: ({ signal }) => {
      if (params === null) {
        throw new ApiError(0, 'invalid_input', '真太阳时参数不完整。');
      }
      return getTrueSolarTime(params, signal);
    },
    enabled: params !== null,
  });
}
