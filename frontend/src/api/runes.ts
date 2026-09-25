import type { RuneCastRequest, RuneCastResponse } from '../types/runes';
import { apiPost } from './client';

/**
 * 北欧卢恩铸石（`POST /api/v1/runes/cast`）：一次请求给全一页。
 *
 * 端点无历法库、无星历，但**有随机**：抽石走后端 `secrets`（OS 熵源 CSPRNG），故同一份
 * 入参两次调用给出两批不同的石。这正是本页该有的样子，也是它只能是 mutation、不能是
 * 按 key 复用的 query 的原因 —— 「重新掷符」必须真去后端重抽，缓存命中就等于把上一次
 * 的结果冒充成这一次的天意。
 *
 * 响应里连一份全典（`codex`）一起回来，所以抽屉与出处卡不必再打第二个端点。
 */
export function fetchRuneCast(
  request: RuneCastRequest,
  signal?: AbortSignal,
): Promise<RuneCastResponse> {
  return apiPost<RuneCastResponse>('/runes/cast', request, signal);
}
