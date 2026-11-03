import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import App from './App';
import './styles/tokens.css';
import './styles/experience.css';
import './styles/report.css';
import { applyTheme, readTheme } from './lib/theme';
import { applyLocale, detectLocale } from './lib/locale';

// Reflect stored/detected settings on <html> before the first paint, so a
// fresh visit renders in the right theme and lang without a flash from the
// defaults; LocaleProvider will re-apply after mount as the state owner.
applyTheme(readTheme());
applyLocale(detectLocale());

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('Destiny root container "#root" was not found in the document.');
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
