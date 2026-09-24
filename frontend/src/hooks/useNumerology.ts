import { fetchNumerologyChart } from '../api/numerology';
import type { ApiError } from '../api/client';
import type { NumerologyChart, NumerologyChartRequest } from '../types/numerology';
import { useLastSuccessMutation } from './useLastSuccessMutation';

/**
 * 提交时推出灵数全盘。
 *
 * 走 {@link useLastSuccessMutation} 而不是裸 `useMutation`，理由与合婚页同源：这一页由
 * 「推演」、Y 元音开关与基准日改动三种触发，而裸 `useMutation` 在重发瞬间清空 `data`，
 * 拨一次开关会让六张核心数卡连同两张九宫整块卸载 —— 而 Y 开关这个动作恰恰需要上一份
 * 结果还在屏上，读者才看得出「灵魂冲动数与人格面具数此消彼长、表达数不变」这条不变式
 * 在 UI 上也成立（plan T9 走查第 9 条）。
 *
 * 另一条同源的：纯中文名会回 422 + `numerology_no_latin_letters`，其 `ApiError.context`
 * 带着检测到的字符样本。失败时留住上一份结果，错误提示叠在上面，比只剩一句 422 的空页
 * 好改 —— 用户要做的正是把中文名换成拼音，而参照物最好还在眼前。
 */
export function useNumerology() {
  return useLastSuccessMutation<NumerologyChart, ApiError, NumerologyChartRequest>(
    fetchNumerologyChart,
  );
}
