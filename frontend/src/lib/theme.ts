export type Theme = 'paper' | 'obsidian';
const KEY = 'destiny.theme.v1';
export function readTheme(): Theme {
  try {
    return localStorage.getItem(KEY) === 'obsidian' ? 'obsidian' : 'paper';
  } catch {
    return 'paper';
  }
}
export function applyTheme(theme: Theme): void {
  document.documentElement.dataset.theme = theme;
  document.documentElement.classList.toggle('dark', theme === 'obsidian');
}
export function saveTheme(theme: Theme): void {
  applyTheme(theme);
  try {
    localStorage.setItem(KEY, theme);
  } catch {
    /* A blocked store must not block reading. */
  }
}
