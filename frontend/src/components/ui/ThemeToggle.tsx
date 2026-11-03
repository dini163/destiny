import { useState } from 'react';
import { readTheme, saveTheme } from '../../lib/theme';
import { useI18n } from '../../i18n/context';
import { Icon } from './Icon';
export function ThemeToggle() {
  const { t } = useI18n();
  const [theme, setTheme] = useState(readTheme);
  const label = theme === 'paper' ? t('切换为曜石深色') : t('切换为暖纸白');
  return (
    <button
      type="button"
      className="theme-toggle"
      title={label}
      aria-label={label}
      onClick={() => {
        const next = theme === 'paper' ? 'obsidian' : 'paper';
        saveTheme(next);
        setTheme(next);
      }}
    >
      <Icon name="sun" size={19} />
    </button>
  );
}
