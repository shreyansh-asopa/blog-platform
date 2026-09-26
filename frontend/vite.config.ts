import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// The API runs on port 8000 and this dev server on 5173. The proxy forwards /api and
// /uploads to the API, so the browser sees a single origin: no CORS, and the same
// relative URLs work in production behind one domain.
const API_URL = process.env.VITE_API_PROXY ?? 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': API_URL,
      '/uploads': API_URL,
    },
  },
})
