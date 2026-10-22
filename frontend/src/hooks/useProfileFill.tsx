import { useCallback, useState } from 'react';

import { ProfileEditor } from '../components/profiles/ProfileEditor';
import { ProfilePicker } from '../components/profiles/ProfilePicker';
import { useProfiles } from '../hooks/useProfiles';
import { profileToBirthInput, type PersonProfile, type ProfileDraft } from '../lib/profiles';
import type { BirthInputValues } from '../components/ui/InputBar';

interface UseProfileFillOptions {
  /** Extra per-page sync when a profile is picked, e.g. seeding `gender`/`name`. */
  onPick?: (profile: PersonProfile | null) => void;
  /** Picker button label. */
  pickerLabel?: string;
}

/**
 * Page-side boilerplate shared by every birth-data console: a profile picker
 * that maps the chosen profile onto the `InputBar` `preset`, and the 存入档案
 * dialog seeded from the current inputs. One call gives a page its `preset`,
 * `picker` and `editor`; pages with extra fields (gender, name) pass `onPick`.
 *
 * This is the single copy of the fill/save wiring so a ninth console never
 * re-implements it by hand (and the pages ratchet in `conventions.test.ts`
 * stays flat).
 */
export function useProfileFill({ onPick, pickerLabel = '选择档案' }: UseProfileFillOptions = {}) {
  const { profiles, upsert } = useProfiles();
  const [preset, setPreset] = useState<BirthInputValues | null>(null);
  const [draftPrefill, setDraftPrefill] = useState<ProfileDraft | null>(null);
  const [editorOpen, setEditorOpen] = useState(false);

  const pick = useCallback(
    (profile: PersonProfile | null) => {
      onPick?.(profile);
      setPreset(profile ? profileToBirthInput(profile) : null);
    },
    [onPick],
  );

  const openSave = useCallback((draft: ProfileDraft) => {
    setDraftPrefill(draft);
    setEditorOpen(true);
  }, []);

  const editor = editorOpen ? (
    <ProfileEditor
      initial={draftPrefill}
      onSave={(draft) => upsert(draft)}
      onClose={() => setEditorOpen(false)}
    />
  ) : null;

  return {
    profiles,
    preset,
    pick,
    openSave,
    editor,
    picker: <ProfilePicker label={pickerLabel} profiles={profiles} onPick={pick} />,
  };
}
