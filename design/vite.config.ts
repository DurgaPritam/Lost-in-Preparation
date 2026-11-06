import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// One page (index.html) serves both the component gallery (#/gallery) and the
// seven screens (#/, #/recipes, #/compare, …). public/data/ holds a copy of
// mock-data/ so the Data & licences download links resolve at /data/*.json.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
});
