import { describe, expect, it } from 'vitest';

import {
  loadProfiles,
  nameSliceOf,
  persistProfiles,
  profileToBirthInput,
  removeProfile,
  upsertProfile,
  STORAGE_KEY,
  type PersonProfile,
} from '../../src/lib/profiles';

/** A minimal but complete profile for CRUD assertions. */
function makeProfile(overrides: Partial<PersonProfile> = {}): PersonProfile {
  return {
    id: 'p-1',
    label: '我自己',
    name: '陆青玄',
    gender: 'male',
    birth_date: '1988-02-15',
    birth_time: '23:30',
    calendar: 'lunar',
    city: '成都',
    latitude: 30.5728,
    longitude: 104.0668,
    created_at: '2026-10-01T00:00:00.000Z',
    updated_at: '2026-10-01T00:00:00.000Z',
    ...overrides,
  };
}

describe('profile store (localStorage-backed person vault)', () => {
  it('upsert creates a new profile with an id and bumps it to the front', () => {
    const next = upsertProfile([], {
      label: '父亲',
      gender: 'male',
      birth_date: '1960-03-01',
      birth_time: '08:00',
    });
    expect(next).toHaveLength(1);
    expect(next[0].id).toBeTruthy();
    expect(next[0].label).toBe('父亲');
    expect(next[0].created_at).toBe(next[0].updated_at);
  });

  it('upsert updates an existing profile in place, keeping its creation time', () => {
    const existing = [makeProfile()];
    const next = upsertProfile(existing, {
      id: 'p-1',
      label: '我自己（新名）',
      gender: 'female',
      birth_date: '1988-02-15',
      birth_time: '23:30',
    });
    expect(next).toHaveLength(1);
    expect(next[0].label).toBe('我自己（新名）');
    expect(next[0].gender).toBe('female');
    expect(next[0].created_at).toBe('2026-10-01T00:00:00.000Z');
    expect(next[0].updated_at > next[0].created_at).toBe(true);
  });

  it('sorts the newest-edited profile first', () => {
    const older = upsertProfile([], {
      label: 'A',
      birth_date: '1990-01-01',
      birth_time: '00:00',
    });
    const newer = upsertProfile(older, {
      id: older[0].id,
      label: 'A 改',
      birth_date: '1990-01-01',
      birth_time: '00:00',
    });
    expect(newer[0].id).toBe(older[0].id);
    // Updating the only entry keeps the list size; a second add puts the new one first.
    const added = upsertProfile(newer, {
      label: 'B',
      birth_date: '1992-06-06',
      birth_time: '12:00',
    });
    expect(added).toHaveLength(2);
    expect(added[0].label).toBe('B');
  });

  it('remove deletes exactly the requested profile', () => {
    const list = [makeProfile(), makeProfile({ id: 'p-2', label: '父亲' })];
    const next = removeProfile(list, 'p-1');
    expect(next.map((p) => p.id)).toEqual(['p-2']);
  });

  it('profileToBirthInput maps onto the shared InputBar contract', () => {
    expect(profileToBirthInput(makeProfile())).toEqual({
      birth_date: '1988-02-15',
      birth_time: '23:30',
      calendar: 'lunar',
      city: '成都',
      latitude: 30.5728,
      longitude: 104.0668,
    });
    expect(profileToBirthInput(makeProfile({ birth_date: '', latitude: null }))).toEqual({
      birth_date: '',
      birth_time: '23:30',
      calendar: 'lunar',
      city: '成都',
      latitude: null,
      longitude: 104.0668,
    });
  });

  it('persist → load round-trips the list through localStorage', () => {
    const list = [makeProfile()];
    persistProfiles(list);
    expect(loadProfiles()).toEqual(list);
    expect(window.localStorage.getItem(STORAGE_KEY)).not.toBeNull();
  });

  it('load degrades to an empty list on corrupt or absent data', () => {
    window.localStorage.removeItem(STORAGE_KEY);
    expect(loadProfiles()).toEqual([]);
    window.localStorage.setItem(STORAGE_KEY, '{not json');
    expect(loadProfiles()).toEqual([]);
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify({ not: 'an array' }));
    expect(loadProfiles()).toEqual([]);
  });
});

describe('nameSliceOf (profile → 姓名学 prefill)', () => {
  it('uses the surname/given split when present', () => {
    expect(
      nameSliceOf(makeProfile({ surname: '欧阳', given: '青玄' })),
    ).toEqual({ surname: '欧阳', given: '青玄' });
  });

  it('splits a name-only profile into first char surname and the rest as given', () => {
    expect(nameSliceOf(makeProfile({ surname: undefined, given: undefined }))).toEqual({
      surname: '陆',
      given: '青玄',
    });
  });

  it('handles a single-char name by putting it in surname only', () => {
    expect(nameSliceOf(makeProfile({ name: '王', surname: undefined, given: undefined }))).toEqual(
      { surname: '王', given: undefined },
    );
  });

  it('returns null when neither split nor full name exists', () => {
    expect(nameSliceOf(makeProfile({ name: undefined, surname: undefined, given: undefined }))).toBeNull();
  });
});
