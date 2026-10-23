import type { Gender, PlainSection } from '../types/common';

/** Full 造向 label: the classical term plus the sex it denotes. */
export const GENDER_LABEL: Record<Gender, string> = {
  male: '乾造（男）',
  female: '坤造（女）',
};

/** Compact form for table heads and inline badges where the full label is too wide. */
export const GENDER_SHORT: Record<Gender, string> = {
  male: '乾（男）',
  female: '坤（女）',
};

/** The shared gender selector options, so every system uses the same copy. */
export const GENDER_OPTIONS: ReadonlyArray<{ value: Gender; label: string }> = [
  { value: 'male', label: GENDER_LABEL.male },
  { value: 'female', label: GENDER_LABEL.female },
];

/**
 * Add the sex annotation to 造向 words in backend-authored hehun copy.
 *
 * The API keeps its canonical terms (乾/坤, 乾视坤, 乾独宜, 乾年×坤时); the page
 * adds the gloss at render time. Only role-bearing contexts are matched, so
 * classical uses such as 乾坤 or 乾为天 are left untouched.
 */
export function annotateGenderTerms(text: string): string {
  return text
    .replace(/乾造(?!（男）)/g, GENDER_LABEL.male)
    .replace(/坤造(?!（女）)/g, GENDER_LABEL.female)
    .replaceAll('乾视坤', `${GENDER_SHORT.male}视${GENDER_SHORT.female}`)
    .replaceAll('坤视乾', `${GENDER_SHORT.female}视${GENDER_SHORT.male}`)
    .replaceAll('乾独', `${GENDER_SHORT.male}独`)
    .replaceAll('坤独', `${GENDER_SHORT.female}独`)
    .replace(/乾(?=[年月日时木火土金水·这递想给岁四])/g, GENDER_SHORT.male)
    .replace(/坤(?=[年月日时木火土金水·这递想给岁四])/g, GENDER_SHORT.female);
}

/** Apply the same annotation to the prose sections of the hehun overview. */
export function annotatePlainSections(sections: PlainSection[]): PlainSection[] {
  return sections.map((section) => ({ ...section, text: annotateGenderTerms(section.text) }));
}
