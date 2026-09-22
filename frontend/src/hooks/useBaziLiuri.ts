import { fetchBaziLiuri } from '../api/baziLiuri';
import type { ApiError } from '../api/client';
import type { BaziLiuriRequest, BaziLiuriResult } from '../types/baziLiuri';
import { useLastSuccessMutation } from './useLastSuccessMutation';

/**
 * 提交时推演流日矩阵（一段节气月的逐日 + 可选聚焦日详批）。
 *
 * 与 `useBaziTransit` 同口径：这一页由「查询」按钮、格子点击与段切换三种触发，
 * 且两个域错误（`liuri_month_unsupported` / `liuri_focus_out_of_month`）的
 * `ApiError.context` 要活过「请求—报错—改表单—重发」这条循环，按 query key 缓存会把
 * 那条链吞掉。走 {@link useLastSuccessMutation} 而不是裸 `useMutation`：`useMutation`
 * 在重发瞬间就把 `data` 清空，点一格会让 29 格矩阵整块卸载两秒。
 */
export function useBaziLiuri() {
  return useLastSuccessMutation<BaziLiuriResult, ApiError, BaziLiuriRequest>(fetchBaziLiuri);
}
