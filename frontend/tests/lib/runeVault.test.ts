import { describe, expect, it } from 'vitest';

import {
  loadVault,
  persistVault,
  removeCast,
  saveCast,
  STORAGE_KEY,
} from '../../src/lib/runeVault';
import type { RuneCastResponse } from '../../src/types/runes';

/** A stand-in cast snapshot; the store only carries it opaquely, so no field is read. */
function makeCast(seed: string): RuneCastResponse {
  return { seed } as unknown as RuneCastResponse;
}

describe('rune vault (localStorage-backed oracle archive)', () => {
  it('saveCast prepends a snapshot with an id and save time', () => {
    const next = saveCast([], makeCast('first'));
    expect(next).toHaveLength(1);
    expect(next[0].id).toBeTruthy();
    expect(next[0].saved_at).toBeTruthy();
    expect(next[0].cast).toEqual(makeCast('first'));
  });

  it('saveCast puts the newest entry in front', () => {
    const first = saveCast([], makeCast('a'));
    const second = saveCast(first, makeCast('b'));
    expect(second).toHaveLength(2);
    expect(second[0].cast).toEqual(makeCast('b'));
    expect(second[1].cast).toEqual(makeCast('a'));
  });

  it('removeCast deletes exactly the requested entry', () => {
    const list = saveCast(saveCast([], makeCast('a')), makeCast('b'));
    const next = removeCast(list, list[1].id);
    expect(next.map((entry) => entry.cast)).toEqual([makeCast('b')]);
  });

  it('persist → load round-trips the list through localStorage', () => {
    const list = saveCast([], makeCast('a'));
    persistVault(list);
    expect(loadVault()).toEqual(list);
    expect(window.localStorage.getItem(STORAGE_KEY)).not.toBeNull();
  });

  it('load degrades to an empty list on corrupt or absent data', () => {
    window.localStorage.removeItem(STORAGE_KEY);
    expect(loadVault()).toEqual([]);
    window.localStorage.setItem(STORAGE_KEY, '{not json');
    expect(loadVault()).toEqual([]);
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify({ not: 'an array' }));
    expect(loadVault()).toEqual([]);
  });
});
