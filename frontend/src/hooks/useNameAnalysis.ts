import type { ApiError } from '../api/client';
import { analyzeName } from '../api/name';
import type { NameAnalysis, NameAnalyzeRequest } from '../types/name';
import { useLastSuccessMutation } from './useLastSuccessMutation';

/**
 * 提交时核定姓名。
 *
 * 用 mutation 而非缓存 query：一简对多繁的候选要靠 422 的 `context` 回填表单，
 * 请求-错误-重试这条链是交互的一部分，不该被缓存吞掉（与 useZhouyiCast 同口径）。
 *
 * 走 {@link useLastSuccessMutation}：改字重提时上一份五格还在屏上，简繁候选回填前后的
 * 笔画差异才有参照；422 叠在旧结果上面，也比一句报错的空页好改。
 */
export function useNameAnalysis() {
  return useLastSuccessMutation<NameAnalysis, ApiError, NameAnalyzeRequest>(analyzeName);
}
