import { useCallback, useState } from 'react';

import {
  loadProfiles,
  persistProfiles,
  removeProfile as removeProfilePure,
  upsertProfile as upsertProfilePure,
  type PersonProfile,
  type ProfileDraft,
} from '../lib/profiles';

/**
 * Profile store for the app session, backed by localStorage.
 *
 * One hook per page so every mounted console sees the same list; each write
 * persists the whole list under `destiny.personProfiles.v1`. Storage errors are
 * swallowed on read (degrade to an empty list) but surface on write through the
 * thrown exception, so a full/quarantined localStorage is never silently lost.
 */
export function useProfiles() {
  const [profiles, setProfiles] = useState<PersonProfile[]>(loadProfiles);

  const upsert = useCallback((draft: ProfileDraft) => {
    setProfiles((prev) => {
      const next = upsertProfilePure(prev, draft);
      persistProfiles(next);
      return next;
    });
  }, []);

  const remove = useCallback((id: string) => {
    setProfiles((prev) => {
      const next = removeProfilePure(prev, id);
      persistProfiles(next);
      return next;
    });
  }, []);

  return { profiles, upsert, remove };
}
