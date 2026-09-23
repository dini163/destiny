import { fetchBaziHehun } from '../api/baziHehun';
import type { ApiError } from '../api/client';
import type { BaziHehunRequest, BaziHehunResult } from '../types/baziHehun';
import { useLastSuccessMutation } from './useLastSuccessMutation';

/**
 * 提交时推演双人合盘。
 *
 * 与 `useBaziLiushi` 同一条纪律：这一页由「查询」、轴长切换与换窗三种触发，而
 * `hehun_axis_out_of_range` 的 `ApiError.context`（五个键：所请起讫、两造可推起、可推终）
 * 要活过「请求—报错—改轴—重发」那条循环。走 {@link useLastSuccessMutation} 而不是裸
 * `useMutation`：后者在重发瞬间清空 `data`，换一次轴长会让九段结果整块卸载两秒 ——
 * 而换轴这个动作恰恰需要上一份轴还在屏幕上，读者才知道新窗接在哪一年后面（决策 11）。
 */
export function useBaziHehun() {
  return useLastSuccessMutation<BaziHehunResult, ApiError, BaziHehunRequest>(fetchBaziHehun);
}
