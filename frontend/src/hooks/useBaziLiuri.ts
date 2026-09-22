import { useMutation } from '@tanstack/react-query';

import { fetchBaziLiuri } from '../api/baziLiuri';
import type { ApiError } from '../api/client';
import type { BaziLiuriRequest, BaziLiuriResult } from '../types/baziLiuri';

/**
 * 提交时推演流日矩阵（一段节气月的逐日 + 可选聚焦日详批）。
 *
 * 与 `useBaziTransit` 同口径用 mutation 而不是 query key：这一页由「查询」按钮、
 * 格子点击与段切换三种触发，且两个域错误（`liuri_month_unsupported` /
 * `liuri_focus_out_of_month`）的 `ApiError.context` 要活过「请求—报错—改表单—重发」
 * 这条循环，缓存会把那条链吞掉。副作用是界面不闪：mutation 的 `data` 在下一次
 * `mutate` 完成前一直是上一份响应，旧矩阵继续挂着。
 */
export function useBaziLiuri() {
  return useMutation<BaziLiuriResult, ApiError, BaziLiuriRequest>({
    mutationFn: (request) => fetchBaziLiuri(request),
  });
}
