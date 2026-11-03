/**
 * Locale context + `useI18n()` hook.
 *
 * Design notes:
 * - Missing Provider is a graceful no-op: `useI18n()` returns an identity
 *   fallback (`t(key) => key`, locale = zh-Hans). Existing tests that render
 *   components directly (e.g. `compliance_disclaimer.test.tsx`) keep passing
 *   because they see the source Chinese string unchanged.
 * - `t()` interpolates `{{name}}` placeholders using the supplied vars object,
 *   which covers the small number of parameterised strings in phase 1
 *   (e.g. `t('探索全部 {{count}} 个体系', { count: 15 })`).
 * - The value is memoised on `locale` alone; changing locale re-renders every
 *   consumer, which is exactly what we want for a chrome-wide language switch.
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

import {
  applyLocale,
  DEFAULT_LOCALE,
  detectLocale,
  saveLocale,
  type AppLocale,
} from '../lib/locale';
import { MESSAGES } from './messages';

type Vars = Readonly<Record<string, string | number>>;

interface I18nValue {
  locale: AppLocale;
  setLocale: (next: AppLocale) => void;
  t: (key: string, vars?: Vars) => string;
}

const I18nContext = createContext<I18nValue | null>(null);

/** Substitute `{{name}}` placeholders from `vars` (empty string when absent). */
function interpolate(raw: string, vars?: Vars): string {
  if (!vars) return raw;
  return raw.replace(/\{\{(\w+)\}\}/g, (_, name: string) =>
    Object.prototype.hasOwnProperty.call(vars, name) ? String(vars[name]) : '',
  );
}

const FALLBACK: I18nValue = {
  locale: DEFAULT_LOCALE,
  setLocale: () => undefined,
  // Identity for the string itself, but placeholders are still filled — a
  // parameterised key (e.g. `{{label}}的赋分账本`) has no user-facing meaning
  // left unsubstituted, and zh-Hans carries no dict so this is its render path.
  t: (key, vars) => interpolate(key, vars),
};

function buildTranslator(locale: AppLocale): (key: string, vars?: Vars) => string {
  const dict = MESSAGES[locale];
  return (key, vars) => interpolate(dict?.[key] ?? key, vars);
}

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<AppLocale>(() => detectLocale());
  useEffect(() => {
    applyLocale(locale);
  }, [locale]);

  const setLocale = useCallback((next: AppLocale) => {
    setLocaleState(next);
    saveLocale(next);
  }, []);

  const t = useMemo(() => buildTranslator(locale), [locale]);
  const value = useMemo<I18nValue>(() => ({ locale, setLocale, t }), [locale, setLocale, t]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nValue {
  return useContext(I18nContext) ?? FALLBACK;
}
