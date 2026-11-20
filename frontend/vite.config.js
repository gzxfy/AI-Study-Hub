import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const backendUrl = process.env.VITE_BACKEND_URL || 'http://127.0.0.1:5000';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    // Study currently uses legacy JSON paths; keep those paths intact.
    proxy: { '/api': backendUrl, '/study_mode': backendUrl },
  },
});
