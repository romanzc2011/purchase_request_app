import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [react()],

  // App is served from the root of the site
  base: "/",

  server: {
    port: 5002,
    host: true,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:5004",
        changeOrigin: true,
      },
      "/sse": {
        target: "http://127.0.0.1:5004", // stays http://
        changeOrigin: true,
      },
    },
},

  build: {
    outDir: "dist",
    emptyOutDir: true,
    assetsDir: "assets",
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          mui: ['@mui/material', '@mui/icons-material'],
        },
      },
    },
  },

  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
      "@assets": fileURLToPath(new URL("./src/assets", import.meta.url)),
    },
  },
})