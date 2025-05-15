import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    proxy: {
        '/api': {
            target: 'http://127.0.0.1:8000', // URL вашего локального бекенда
            changeOrigin: true, // Устанавливает заголовок `Host` как у целевого URL
            rewrite: (path) => path.replace(/^\/api/, '') // Убирает `/api` из пути запроса
        },
        '/docs': { // Прокси для Swagger UI
            target: 'http://127.0.0.1:8000',
            changeOrigin: true,
            rewrite: (path) => path.replace(/^\/docs/, '/docs')
        },
        '/openapi.json': { // Прокси для OpenAPI схемы
            target: 'http://127.0.0.1:8000',
            changeOrigin: true,
        }
    }
  }
})
