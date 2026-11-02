import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import App from './App';
import './styles/tokens.css';
import './styles/experience.css';
import './styles/report.css';
import { applyTheme, readTheme } from './lib/theme';

applyTheme(readTheme());

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('Destiny root container "#root" was not found in the document.');
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
