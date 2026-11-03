export type Theme = 'paper' | 'obsidian';
const KEY = 'destiny.theme.v1';
export function readTheme(): Theme {
  try {
    // Default is obsidian: overseas metaphysics audiences skew toward dark cosmic
    // surfaces, and a fresh install has no explicit choice yet. Only a stored
    // 'paper' — i.e. a user who consciously toggled to the light theme — reads
    // back as paper; anything else (null, unknown value) falls to obsidian.
    return localStorage.getItem(KEY) === 'paper' ? 'paper' : 'obsidian';
  } catch {
    return 'obsidian';
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
