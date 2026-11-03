/**
 * Minimal fetch wrapper for the Destiny computation API.
 *
 * Every endpoint lives under `/api/v1` — proxied to the backend by Vite in dev and
 * by nginx in prod, so the client only ever uses a relative base. The backend
 * speaks snake_case JSON end-to-end, so payloads pass through untransformed.
 *
 * Non-2xx responses are normalised into a typed {@link ApiError} carrying the
 * backend's `{ error: { code, message } }` envelope (see backend/app/core/errors.py)
 * or FastAPI's 422 `{ detail }` validation shape, so callers handle a single type.
 */

import { DEFAULT_LOCALE, detectLocale } from '../lib/locale';

/** Relative base path of the versioned API. */
export const API_BASE = '/api/v1';

/** Query-string parameter values; null/undefined entries are omitted. */
export type QueryParams = Record<string, string | number | boolean | null | undefined>;

/** The backend domain-error envelope. */
interface ErrorEnvelope {
  error?: { code?: string; message?: string; context?: Record<string, unknown> };
  detail?: unknown;
}

/** A single FastAPI validation error entry. */
interface ValidationError {
  loc?: unknown[];
  msg?: string;
}

/** A typed error thrown for any non-2xx API response or network failure. */
export class ApiError extends Error {
  /** HTTP status, or 0 for a network-level failure. */
  readonly status: number;
  /** Stable machine code from the backend envelope. */
  readonly code: string;
  /** 机器可读的补充事实（如 `ambiguous_traditional` 的候选字列表）。 */
  readonly context: Record<string, unknown> | undefined;

  constructor(
    status: number,
    code: string,
    message: string,
    context?: Record<string, unknown>,
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.context = context;
  }
}

interface RequestOptions {
  method?: 'GET' | 'POST';
  query?: QueryParams;
  body?: unknown;
  signal?: AbortSignal;
}

/** Perform an API request and decode the JSON body, or throw an {@link ApiError}. */
async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const hasBody = options.body !== undefined;
  let response: Response;
  try {
    response = await fetch(buildUrl(path, options.query), {
      method: options.method ?? 'GET',
      headers: hasBody ? { 'Content-Type': 'application/json' } : undefined,
      body: hasBody ? JSON.stringify(options.body) : undefined,
      signal: options.signal,
    });
  } catch (cause) {
    // Let TanStack Query see cancellations; everything else is a network failure.
    if (cause instanceof Error && cause.name === 'AbortError') {
      throw cause;
    }
    throw new ApiError(0, 'network_error', '无法连接到 Destiny 计算服务，请确认后端已启动后重试。');
  }

  if (!response.ok) {
    throw await toApiError(response);
  }
  return (await response.json()) as T;
}

/** Issue a GET request, optionally with query params and an abort signal. */
export function apiGet<T>(path: string, query?: QueryParams, signal?: AbortSignal): Promise<T> {
  return apiFetch<T>(path, { method: 'GET', query, signal });
}

/** Issue a POST request with a JSON body and an optional abort signal. */
export function apiPost<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
  return apiFetch<T>(path, { method: 'POST', body, signal });
}

/** Build a `/api/v1`-relative URL, appending defined query params plus the active locale. */
function buildUrl(path: string, query?: QueryParams): string {
  const url = `${API_BASE}${path}`;
  const search = new URLSearchParams();
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null) {
        search.set(key, String(value));
      }
    }
  }
  // The backend localizes structured labels only when an explicit non-default locale is
  // requested; sending `zh-Hans` (or nothing) keeps the default byte-for-byte pass-through.
  const locale = detectLocale();
  if (locale !== DEFAULT_LOCALE) {
    search.set('locale', locale);
  }
  const qs = search.toString();
  return qs ? `${url}?${qs}` : url;
}

/** Convert a failed response into an {@link ApiError}, parsing the error body. */
async function toApiError(response: Response): Promise<ApiError> {
  let code = 'http_error';
  let message = `请求失败（HTTP ${response.status}）。`;
  let context: Record<string, unknown> | undefined;

  try {
    const payload = (await response.json()) as ErrorEnvelope;
    if (payload.error?.message) {
      code = payload.error.code ?? code;
      message = payload.error.message;
      context = payload.error.context;
    } else if (Array.isArray(payload.detail)) {
      // FastAPI request-validation error: an array of { loc, msg, type } entries.
      code = 'validation_error';
      message = formatValidationDetail(payload.detail);
    } else if (typeof payload.detail === 'string' && payload.detail.trim()) {
      // A bare string detail (e.g. a 404 "Not Found") is not a parameter problem —
      // report it honestly instead of blaming the user's inputs. A stale backend
      // that predates this route is the usual cause of a 404 here.
      if (response.status === 404) {
        code = 'not_found';
        message = '接口不存在或后端服务未更新，请重启后端服务后重试。';
      } else {
        message = `请求失败（HTTP ${response.status}）：${payload.detail}`;
      }
    }
  } catch {
    // Non-JSON error body — keep the generic status message.
  }

  return new ApiError(response.status, code, message, context);
}

/** Render FastAPI's `{ detail: [...] }` validation payload as a readable message. */
function formatValidationDetail(detail: unknown): string {
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as ValidationError;
    if (first.msg) {
      const field = Array.isArray(first.loc) ? first.loc.slice(1).join('.') : '';
      return field ? `${field}：${first.msg}` : first.msg;
    }
  }
  return '请求参数校验未通过。';
}
