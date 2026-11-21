import { resolve } from "node:path"
import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // Mismo esquema que Nginx en Docker: /api/* → backend, sin CORS.
    proxy: {
      "/api": {
        target: process.env.API_URL ?? "http://localhost:8000",
        changeOrigin: true,
        rewrite: (ruta) => ruta.replace(/^\/api/, ""),
      },
    },
  },
  resolve: {
    alias: {
      "@": resolve(import.meta.dirname, "./src"),
    },
  },
})
