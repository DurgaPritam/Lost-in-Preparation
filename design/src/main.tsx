import { StrictMode, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';
import Gallery from './gallery/Gallery';
import App from './screens/App';

/**
 * Entry point for local review.
 *   #/gallery            → component gallery (every component, every state)
 *   #/ … #/data          → the seven screens (see src/screens/App.tsx)
 * Append ?theme=dark or ?theme=light to force a theme; otherwise the system
 * preference applies.
 */
const theme = new URLSearchParams(location.search).get('theme');
if (theme === 'dark' || theme === 'light') document.documentElement.dataset.theme = theme;

function Root() {
  const [hash, setHash] = useState(location.hash);
  useEffect(() => {
    const on = () => setHash(location.hash);
    window.addEventListener('hashchange', on);
    return () => window.removeEventListener('hashchange', on);
  }, []);
  return hash.startsWith('#/gallery') ? <Gallery /> : <App />;
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Root />
  </StrictMode>,
);
