import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'


export default defineConfig({
  plugins: [react()],
  server: {
    host: "localhost",
    port: 5002,
  },
  build: {
    outDir: "./dist",
    emptyOutDir: true,
  },
});