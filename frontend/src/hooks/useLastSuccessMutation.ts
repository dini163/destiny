import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';

/** {@link useLastSuccessMutation} 交给页面的那一小份视图。 */
export interface LastSuccessMutation<TData, TError, TVariables> {
  /** 最近一次成功的响应；重发在途与这一次失败期间都仍是它。 */
  readonly data: TData | undefined;
  /** 最近一次的失败，成功响应回来时清零。 */
  readonly error: TError | null;
  readonly isPending: boolean;
  readonly mutate: (variables: TVariables) => void;
}

/**
 * 让上一次成功的响应留在页面上的 mutation。
 *
 * `useMutation` 自己的 `data` 撑不过重发：query-core 的 reducer 在 `pending` 与
 * `error` 两个 action 里都把它清成 `undefined`，于是「点一格看当日详批」「上一段 /
 * 下一段」这类同页重发的症状是整块结果先卸载、等响应回来再挂回去 —— 用户看到的
 * 是一屏空白。把最后一次成功的结果另存进本地 state，页面在途期间就还挂着旧矩阵。
 *
 * 失败时旧结果同样留着，错误提示由页面叠在上面：只剩一句 422 的空页更难读，而且
 * 域错误的改正路径（换段、换日）本来就需要上一份结果还看得见。
 */
export function useLastSuccessMutation<TData, TError, TVariables>(
  mutationFn: (variables: TVariables) => Promise<TData>,
): LastSuccessMutation<TData, TError, TVariables> {
  const [lastSuccess, setLastSuccess] = useState<TData | undefined>(undefined);
  const mutation = useMutation<TData, TError, TVariables>({
    // 只把 variables 递出去：query-core 的第二个实参是 mutation context，而各
    // `fetch*` 函数的第二位是 `signal?: AbortSignal`，直传函数名会把前者塞进后者，
    // 症状是 fetch 在读 signal 时直接抛错。
    mutationFn: (variables) => mutationFn(variables),
    onSuccess: (result) => setLastSuccess(result),
  });
  return {
    data: lastSuccess,
    error: mutation.error,
    isPending: mutation.isPending,
    mutate: mutation.mutate,
  };
}
