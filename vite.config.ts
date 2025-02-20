import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'node:fs'

// export default defineConfig({
//   plugins: [react()],
//   server: {
//     https: {
//       key: fs.readFileSync('tls_certs/test_key.pem'),
//       cert: fs.readFileSync('tls_certs/test_cert.pem'),
//     },
//     host: "localhost",
//     port: 5002,
//   },
//   build: {
//     outDir: "./dist", // ✅ Ensures no nested `dist/dist/`
//     emptyOutDir: true, // ✅ Cleans old files before building
//   }
// });

export default defineConfig({
  plugins: [react()],
  server: {
    host: "localhost",  // Ensures it's accessible on localhost
    port: 5002,         // Force Vite to use port 5002
    strictPort: true    // Prevents Vite from switching ports if 5002 is occupied
  },
  build: {
    outDir: "./dist",
    emptyOutDir: true,
  }
});
