import type { NumerologyChart, NumerologyChartRequest } from '../types/numerology';
import { apiPost } from './client';

/**
 * 毕达哥拉斯灵数全盘（`POST /api/v1/numerology/chart`）：一次请求给全一页。
 *
 * 端点无历法库、无星历、无随机，同输入恒同输出，故不必像八字诸页那样先探真太阳时。
 */
export function fetchNumerologyChart(
  request: NumerologyChartRequest,
  signal?: AbortSignal,
): Promise<NumerologyChart> {
  return apiPost<NumerologyChart>('/numerology/chart', request, signal);
}
