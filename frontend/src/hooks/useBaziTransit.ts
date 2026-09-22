import { fetchBaziTransit } from '../api/baziTransit';
import type { ApiError } from '../api/client';
import type { BaziTransitRequest, BaziTransitResult } from '../types/baziTransit';
import { useLastSuccessMutation } from './useLastSuccessMutation';

/**
 * 提交时推演岁运（流年区间，聚焦年再含十二节气月）。
 *
 * 与 `useBaziNatal` 同口径要提交才发：这一页由「查询」按钮与年表的行点击触发，不是
 * 渲染即取。区间不成立时的四类 422 要靠 `ApiError.context` 把上限、本命盘可及年份回填
 * 到提示里，按 query key 缓存会把这条「请求—报错—改表单—重提」的链吞掉。
 * {@link useLastSuccessMutation} 负责让点行的那一年里旧年表先挂着，而不是闪一屏空白
 * （`useNameAnalysis` 一次一发，不需要这层）。
 */
export function useBaziTransit() {
  return useLastSuccessMutation<BaziTransitResult, ApiError, BaziTransitRequest>(
    fetchBaziTransit,
  );
}
