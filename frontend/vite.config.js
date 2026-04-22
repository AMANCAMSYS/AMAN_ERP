import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => ({
    plugins: [react()],
    esbuild: mode === 'production' ? { drop: ['console', 'debugger'] } : {},
    optimizeDeps: {
        include: ['react-grid-layout'],
    },
    build: {
        // PLAT-PERF-02: تقسيم المكتبات الكبيرة لـ chunks مستقلّة لتحسين وقت التحميل الأوّل
        // والاستفادة القصوى من HTTP cache.
        chunkSizeWarningLimit: 1000,
        rollupOptions: {
            output: {
                manualChunks: {
                    // Keep react-i18n together with React runtime to avoid chunk init ordering issues.
                    'vendor-react': ['react', 'react-dom', 'react-router-dom', 'react-is', 'i18next', 'i18next-browser-languagedetector', 'react-i18next'],
                    'vendor-charts': ['echarts', 'echarts-for-react', 'recharts'],
                    'vendor-forms': ['react-hook-form', 'react-datepicker'],
                    'vendor-grid': ['react-grid-layout', 'react-window', 'react-virtualized-auto-sizer'],
                    'vendor-ui': ['lucide-react', 'react-icons', 'react-hot-toast', 'dompurify', 'dayjs', 'axios'],
                },
            },
        },
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
