import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// En développement (`npm run dev`), les appels API passent par la passerelle locale
// pour conserver le même chemin (WAF + rate limiting) qu'en démonstration.
const gateway = process.env.VITE_DEV_GATEWAY ?? 'http://localhost:8080'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': gateway,
      '/auth': gateway,
    },
  },
})
