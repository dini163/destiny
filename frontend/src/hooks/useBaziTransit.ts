import { useMutation } from '@tanstack/react-query';

import { fetchBaziTransit } from '../api/baziTransit';
import type { ApiError } from '../api/client';
import type { BaziTransitRequest, BaziTransitResult } from '../types/baziTransit';

/**
 * 提交时推演岁运（流年区间，聚焦年再含十二节气月）。
 *
 * 与 `useBaziNatal` 同口径用 mutation：这一页由「查询」按钮与年表的行点击触发，不是
 * 渲染即取。区间不成立时的四类 422 要靠 `ApiError.context` 把上限、本命盘可及年份回填
 * 到提示里，缓存会把这条「请求—报错—改表单—重提」的链吞掉（`useNameAnalysis` 同理）。
 */
export function useBaziTransit() {
  return useMutation<BaziTransitResult, ApiError, BaziTransitRequest>({
    mutationFn: (request) => fetchBaziTransit(request),
  });
}
