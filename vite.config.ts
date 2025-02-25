import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'node:fs'

const useHTTPS: boolean = false;

export default defineConfig({
  plugins: [react()],
  server: {
    // Conditionally add the https configuration if useHttps is true
    ...(useHTTPS ? {
      https: {
        key: fs.readFileSync('tls_certs/test_key.pem'),
        cert: fs.readFileSync('tls_certs/test_cert.pem'),
      },
    } : {}),
    host: "localhost",
    port: 5002,
  },
  build: {
    outDir: "./dist",
    emptyOutDir: true,
  },
});