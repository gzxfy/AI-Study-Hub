import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    // Study currently uses legacy JSON paths; keep those paths intact.
    proxy: { '/api': 'http://127.0.0.1:5000', '/study_mode': 'http://127.0.0.1:5000' },
  },
});
