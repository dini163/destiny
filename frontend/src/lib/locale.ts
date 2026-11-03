/**
 * Locale detection + persistence for the three supported UI languages.
 *
 * The stored key is `destiny.locale.v1`. Priority is (1) explicit choice, then
 * (2) `navigator.languages` — the full ordered list, because a zh-TW user with
 * English as a secondary language still reads Chinese UI best — then (3)
 * Simplified Chinese as the neutral fallback.
 *
 * Normalization rules:
 *   - Any `en*` tag (en, en-US, en-GB, en-AU, …) collapses to `en`.
 *   - `zh-Hant` / `zh-TW` / `zh-HK` / `zh-MO` collapse to `zh-Hant`.
 *   - Everything else starting with `zh` (zh, zh-CN, zh-SG, zh-Hans, …) collapses
 *     to `zh-Hans`.
 *   - Any other language (ja, ko, es, …) falls back to `en`: those users will
 *     not read either Chinese script, so English is the least-bad common option
 *     for an overseas audience.
 */
export type AppLocale = 'zh-Hans' | 'zh-Hant' | 'en';

const KEY = 'destiny.locale.v1';

/** Enumeration order drives both the switcher UI and the type-guard on stored values. */
export const SUPPORTED_LOCALES: readonly AppLocale[] = ['zh-Hans', 'zh-Hant', 'en'];

export const DEFAULT_LOCALE: AppLocale = 'zh-Hans';

/** Map a BCP-47 tag to one of the supported app locales, or null if unrecognized. */
export function normalizeTag(tag: string | undefined | null): AppLocale | null {
  if (!tag) return null;
  const lower = tag.toLowerCase();
  if (lower.startsWith('en')) return 'en';
  if (lower.startsWith('zh')) {
    if (/-(hant|tw|hk|mo)/.test(lower)) return 'zh-Hant';
    return 'zh-Hans';
  }
  return null;
}

/**
 * Resolve the active locale: stored value wins, then navigator (any entry in the
 * list that maps to a supported locale), then the Simplified fallback. Other
 * languages (ja/ko/es/…) intentionally fall to `en`.
 */
export function detectLocale(): AppLocale {
  try {
    const stored = localStorage.getItem(KEY);
    if (stored && (SUPPORTED_LOCALES as readonly string[]).includes(stored)) {
      return stored as AppLocale;
    }
  } catch {
    /* A blocked store must not block detection. */
  }
  if (typeof navigator !== 'undefined') {
    const tags = navigator.languages ?? [navigator.language];
    for (const tag of tags) {
      const hit = normalizeTag(tag);
      if (hit) return hit;
    }
  }
  return DEFAULT_LOCALE;
}

/** Reflect the locale onto `<html lang>` so screen readers and hyphenation follow it. */
export function applyLocale(locale: AppLocale): void {
  if (typeof document !== 'undefined') {
    document.documentElement.lang = locale;
  }
}

/** Persist an explicit choice; also mirrors it onto `<html lang>` immediately. */
export function saveLocale(locale: AppLocale): void {
  applyLocale(locale);
  try {
    localStorage.setItem(KEY, locale);
  } catch {
    /* Same rationale as readTheme: a blocked store must not block reading. */
  }
}
