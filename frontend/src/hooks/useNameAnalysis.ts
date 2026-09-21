import { useMutation } from '@tanstack/react-query';

import type { ApiError } from '../api/client';
import { analyzeName } from '../api/name';
import type { NameAnalysis, NameAnalyzeRequest } from '../types/name';

/**
 * 提交时核定姓名。
 *
 * 用 mutation 而非缓存 query：一简对多繁的候选要靠 422 的 `context` 回填表单，
 * 请求-错误-重试这条链是交互的一部分，不该被缓存吞掉（与 useZhouyiCast 同口径）。
 */
export function useNameAnalysis() {
  return useMutation<NameAnalysis, ApiError, NameAnalyzeRequest>({
    mutationFn: (request) => analyzeName(request),
  });
}
