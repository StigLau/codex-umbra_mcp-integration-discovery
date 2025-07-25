import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',  // Allow external connections
    port: 5173,
    strictPort: true,
    watch: {
      usePolling: true  // Needed for Docker on some systems
    }
  }
})
