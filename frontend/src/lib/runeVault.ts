import type { RuneCastResponse } from '../types/runes';

/**
 * 神谕秘匣：把读者掷出的一份卢恩铸石快照存进浏览器 localStorage，只在本机、不上传后端
 * （API 保持无状态，见 footer 隐私声明）。与 `lib/profiles.ts` 同一条本地持久化口径：
 * 读坏就降级成空表，写入原样 JSON，不引入 mock 或服务端账户。
 *
 * 存的是整份响应快照而不是挑字段，是为了让回看、导出都能拿到与当时一致的全文；一次铸石
 * 体积极小，整份保存不触及配额。
 */

/** 一条入匣的铸石记录：快照本体加两枚时间戳字段。 */
export interface SavedRuneCast {
  /** Stable id, generated at save (`crypto.randomUUID`). */
  id: string;
  /** ISO save time, drives newest-first sort. */
  saved_at: string;
  /** The full cast response as it was returned. */
  cast: RuneCastResponse;
}

const STORAGE_KEY = 'destiny.runeVault.v1';

/** Read the vault from localStorage; corrupt or absent data degrades to []. */
export function loadVault(): SavedRuneCast[] {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed: unknown = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as SavedRuneCast[]) : [];
  } catch {
    return [];
  }
}

/** Write the vault back to localStorage. */
export function persistVault(entries: SavedRuneCast[]): void {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
}

function newId(): string {
  return typeof crypto.randomUUID === 'function'
    ? crypto.randomUUID()
    : `r-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

/** Prepend a fresh snapshot; newest first. */
export function saveCast(entries: SavedRuneCast[], cast: RuneCastResponse): SavedRuneCast[] {
  const record: SavedRuneCast = {
    id: newId(),
    saved_at: new Date().toISOString(),
    cast,
  };
  return [record, ...entries];
}

/** Remove one saved snapshot by id. */
export function removeCast(entries: SavedRuneCast[], id: string): SavedRuneCast[] {
  return entries.filter((entry) => entry.id !== id);
}

export { STORAGE_KEY };
