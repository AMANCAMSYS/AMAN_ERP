import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => ({
    plugins: [react()],
    esbuild: mode === 'production' ? { drop: ['console', 'debugger'] } : {},
    optimizeDeps: {
        include: ['react-grid-layout'],
    },
    build: {
        // Use Vite/Rollup default chunking to avoid runtime order issues between React and chart libs.
        chunkSizeWarningLimit: 1000,
    },
    server: {
        port: 5173,
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
                ws: true
            },
            '/uploads': {
                target: 'http://localhost:8000',
                changeOrigin: true,
            }
        }
    }
}))
