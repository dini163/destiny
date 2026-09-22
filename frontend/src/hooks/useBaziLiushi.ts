import { fetchBaziLiushi } from '../api/baziLiushi';
import type { ApiError } from '../api/client';
import type { BaziLiushiRequest, BaziLiushiResult } from '../types/baziLiushi';
import { useLastSuccessMutation } from './useLastSuccessMutation';

/**
 * 提交时推演一日十二时辰。
 *
 * 与 `useBaziLiuri` 同一条纪律：这一页由「查询」、格子点击与换日三种触发，两个域错误
 * （`liushi_date_unsupported` / `liushi_hour_out_of_day`）的 `ApiError.context` 要活过
 * 「请求—报错—改表单—重发」那条循环。走 {@link useLastSuccessMutation} 而不是裸
 * `useMutation`：后者在重发瞬间清空 `data`，点一格会让十二格与波形整块卸载两秒。
 */
export function useBaziLiushi() {
  return useLastSuccessMutation<BaziLiushiResult, ApiError, BaziLiushiRequest>(fetchBaziLiushi);
}
