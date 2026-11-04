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
 * - For default Simplified Chinese (`zh-Hans`), translations are pure identity
 *   with zero dictionary bundle payload. The ~186KB `zh-Hant` and `en` dictionaries
 *   in `messages.ts` are dynamically loaded on-demand only when a non-default
 *   locale is requested, keeping the initial client bundle lightweight.
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
import type { MessageDict } from './messages';

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
  t: (key, vars) => interpolate(key, vars),
};

function buildTranslator(dict: MessageDict): (key: string, vars?: Vars) => string {
  return (key, vars) => interpolate(dict[key] ?? key, vars);
}

let cachedMessages: Partial<Record<AppLocale, MessageDict>> | null = null;

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<AppLocale>(() => detectLocale());
  const [dict, setDict] = useState<MessageDict>(() => {
    const loc = detectLocale();
    if (loc === 'zh-Hans' || !cachedMessages) return {};
    return cachedMessages[loc] ?? {};
  });

  useEffect(() => {
    applyLocale(locale);
    if (locale === 'zh-Hans') {
      setDict({});
      return;
    }
    if (cachedMessages) {
      setDict(cachedMessages[locale] ?? {});
      return;
    }
    import('./messages').then((mod) => {
      cachedMessages = mod.MESSAGES;
      setDict(mod.MESSAGES[locale] ?? {});
    });
  }, [locale]);

  const setLocale = useCallback((next: AppLocale) => {
    setLocaleState(next);
    saveLocale(next);
  }, []);

  const t = useMemo(() => buildTranslator(dict), [dict]);
  const value = useMemo<I18nValue>(() => ({ locale, setLocale, t }), [locale, setLocale, t]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nValue {
  return useContext(I18nContext) ?? FALLBACK;
}
