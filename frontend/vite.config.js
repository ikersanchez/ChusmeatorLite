import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    commonjsOptions: {
      include: [/leaflet-draw/, /node_modules/],
      transformMixedEsModules: true,
    },
  },
})
