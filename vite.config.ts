import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'node:fs'

// USE ONLY FOR TESTING -- prod will use config below, iis will handle https in prod
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
});

// https://vite.dev/config/
// export default defineConfig({
//   plugins: [react()],
// })