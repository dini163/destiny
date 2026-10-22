import type { CalendarType, Gender } from '../types/common';
import type { BirthInputValues } from '../components/ui/InputBar';

/**
 * Person profiles: the user's own address book of birth data, persisted only in
 * the browser's localStorage and never sent to the backend (the API stays
 * stateless — see the footer privacy seals).
 *
 * A profile is deliberately wider than any single system's console: `name` feeds
 * 姓名学/灵数, `gender` feeds the natal systems whose luck pillars depend on it,
 * and the birth/coordinate fields feed every `InputBar`. Consuming pages pick a
 * profile and map it onto their own console state via `profileToBirthInput`.
 */

/** A single saved person profile. */
export interface PersonProfile {
  /** Stable id, generated at creation (`crypto.randomUUID`). */
  id: string;
  /** Human-readable handle shown in pickers, e.g. 我自己 / 父亲 / 长子. */
  label: string;
  /** Full name, used by 姓名学 and 毕氏灵数 consoles. */
  name?: string;
  /** 姓名学 split: surname (姓) and given (名), used to seed the name consoles. */
  surname?: string;
  given?: string;
  gender?: Gender | null;
  /** Birth date, ISO `yyyy-mm-dd`. */
  birth_date?: string;
  /** Birth time, `HH:MM`. */
  birth_time?: string;
  calendar?: CalendarType;
  city?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  /** ISO timestamps, `updated_at` drives the picker sort. */
  created_at: string;
  updated_at: string;
}

/**
 * A profile being created or edited; `id` is present only when updating. `label`
 * stays optional on drafts because a 存入档案 prefill starts without one — the
 * editor form requires it before saving.
 */
export type ProfileDraft = Omit<PersonProfile, 'id' | 'created_at' | 'updated_at' | 'label'> & {
  id?: string;
  label?: string;
};

/** The name slice a profile can feed to the 姓名学 console. */
export interface ProfileName {
  surname?: string;
  given?: string;
}

const STORAGE_KEY = 'destiny.personProfiles.v1';

/** Read the profile list from localStorage; corrupt or absent data degrades to []. */
export function loadProfiles(): PersonProfile[] {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed: unknown = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as PersonProfile[]) : [];
  } catch {
    return [];
  }
}

function newId(): string {
  return typeof crypto.randomUUID === 'function'
    ? crypto.randomUUID()
    : `p-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

/** Write the profile list back to localStorage (used by the store hook). */
export function persistProfiles(profiles: PersonProfile[]): void {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(profiles));
}

/** Insert or update a profile, returning the newest-edited-first list. */
export function upsertProfile(profiles: PersonProfile[], draft: ProfileDraft): PersonProfile[] {
  const now = new Date().toISOString();
  const id = draft.id ?? newId();
  const existing = profiles.find((p) => p.id === id);
  const stored: PersonProfile = {
    ...draft,
    label: draft.label ?? '',
    id,
    // An update keeps its creation time; only the first save stamps it.
    created_at: existing?.created_at ?? now,
    updated_at: now,
  };
  const next = existing
    ? profiles.map((p) => (p.id === id ? stored : p))
    : [...profiles, stored];
  return sortByUpdated(next);
}

function sortByUpdated(profiles: PersonProfile[]): PersonProfile[] {
  return [...profiles].sort((a, b) => (a.updated_at < b.updated_at ? 1 : -1));
}

/** Remove one profile by id. */
export function removeProfile(profiles: PersonProfile[], id: string): PersonProfile[] {
  return profiles.filter((p) => p.id !== id);
}

/** Map a profile onto the shared `InputBar` birth-data contract (see `InputBar.tsx`). */
export function profileToBirthInput(profile: PersonProfile): BirthInputValues {
  return {
    birth_date: profile.birth_date ?? '',
    birth_time: profile.birth_time ?? '',
    calendar: profile.calendar,
    city: profile.city ?? null,
    latitude: profile.latitude ?? null,
    longitude: profile.longitude ?? null,
  };
}

export { STORAGE_KEY };
