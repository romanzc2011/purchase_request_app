import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'node:fs'

export default defineConfig({
  plugins: [react()],
  server: {
    https: {
      key: fs.readFileSync('tls_certs/test_key.pem'),
      cert: fs.readFileSync('tls_certs/test_cert.pem'),
    },
    host: "localhost",
    port: 5173,
  },
  build: {
    outDir: "./dist", // ✅ Ensures no nested `dist/dist/`
    emptyOutDir: true, // ✅ Cleans old files before building
  }
});
