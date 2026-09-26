import { computeSynastryChart } from '../api/synastry';
import type { ApiError } from '../api/client';
import type { SynastryChart, SynastryRequest } from '../types/synastry';
import { useLastSuccessMutation } from './useLastSuccessMutation';

/**
 * 提交时推演双人西洋合盘（人对人相位 + 组合盘 + 相契度）。
 *
 * 与 `useBaziHehun` 同一条纪律，走 {@link useLastSuccessMutation} 而不是裸
 * `useMutation`：这一页由「查询」与「改一造生辰重发」两种触发，后者在重发瞬间若清空
 * `data`，整块双轮盘与组合盘会先卸载再挂回，读者看到的是两秒空白 —— 而微调生辰这个
 * 动作恰恰需要上一份盘还在屏幕上，才看得出改了哪一处。
 */
export function useSynastry() {
  return useLastSuccessMutation<SynastryChart, ApiError, SynastryRequest>(computeSynastryChart);
}
