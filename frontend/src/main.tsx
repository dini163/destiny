import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import App from './App';
import './styles/tokens.css';

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('Destiny root container "#root" was not found in the document.');
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
