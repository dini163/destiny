import { useState } from 'react';
import { readTheme, saveTheme } from '../../lib/theme';
import { Icon } from './Icon';
export function ThemeToggle() {
  const [theme, setTheme] = useState(readTheme);
  const label = theme === 'paper' ? '切换为曜石深色' : '切换为暖纸白';
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
