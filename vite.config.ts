import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'


export default defineConfig({
  plugins: [react()],
  server: {
    host: "localhost",
    port: 5002,
    proxy: {
      '/communicate': {
        target: 'http://localhost:5004',
        ws: true, // WebSocket support
      },
    },
  },
  build: {
    outDir: "./dist",
    emptyOutDir: true,
  },
});
