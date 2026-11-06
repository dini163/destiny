import { computeZiwei, computeZiweiAnalysis } from '../api/ziwei';
import type { ApiError } from '../api/client';
import type { ZiweiAnalysisRequest, ZiweiAnalysisResponse, ZiweiChart, ZiweiRequest } from '../types/ziwei';
import { useLastSuccessMutation } from './useLastSuccessMutation';

/**
 * Compute a 紫微斗数 chart on demand.
 *
 * A mutation (never a cached query): the board is cast exactly when the user
 * submits the birth-data console, so every chart reflects the current inputs.
 *
 * 走 {@link useLastSuccessMutation}：控制台每一项（生辰、历法、造向、经纬度、真太阳时）
 * 都是下一次安星的入参，改哪一项都会换掉整张盘；裸 `useMutation` 在重发那一下把 `data`
 * 清成 `undefined`，于是十二宫整块卸载再挂回 —— 在途时读者该看见的仍是上一张盘。
 */
export function useZiwei() {
  return useLastSuccessMutation<ZiweiChart, ApiError, ZiweiRequest>(computeZiwei);
}

/** Compute a 紫微斗数 chart + 13-dimension deep analysis on demand. */
export function useZiweiAnalysis() {
  return useLastSuccessMutation<ZiweiAnalysisResponse, ApiError, ZiweiAnalysisRequest>(computeZiweiAnalysis);
}

