import { SUPPORTED_LOCALES, type AppLocale } from '../../lib/locale';
import { useI18n } from '../../i18n/context';

/**
 * Chrome language picker rendered in the header next to the theme toggle.
 *
 * Each button label is written in **its own language** (简体中文 / 繁體中文 /
 * English), which is the standard i18n pattern: a user who cannot read the
 * current UI can still recognise their language by name. The compact short
 * forms (简 / 繁 / EN) show up on small viewports where the header bar
 * tightens.
 */
const LABEL: Record<AppLocale, { long: string; short: string }> = {
  'zh-Hans': { long: '简体中文', short: '简' },
  'zh-Hant': { long: '繁體中文', short: '繁' },
  en: { long: 'English', short: 'EN' },
};

export function LocaleSwitcher() {
  const { locale, setLocale } = useI18n();
  return (
    <div
      className="locale-switcher flex items-center gap-0.5 rounded-element border border-rim bg-surface/60 p-0.5"
      role="group"
      aria-label="Language / 语言 / 語言"
    >
      {SUPPORTED_LOCALES.map((code) => {
        const active = code === locale;
        return (
          <button
            key={code}
            type="button"
            aria-pressed={active}
            title={LABEL[code].long}
            onClick={() => setLocale(code)}
            className={
              active
                ? 'rounded-element bg-gold/15 px-2 py-1 text-xs text-gold transition'
                : 'rounded-element px-2 py-1 text-xs text-ink-muted transition hover:text-ink'
            }
          >
            <span className="hidden sm:inline">{LABEL[code].long}</span>
            <span className="sm:hidden">{LABEL[code].short}</span>
          </button>
        );
      })}
    </div>
  );
}
