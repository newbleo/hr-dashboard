import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['icon.svg', 'pwa-192x192.png', 'pwa-512x512.png'],
      manifest: {
        name: '잡줍줍',
        short_name: '잡줍줍',
        description: '채용공고 한방에 줍줍 — 사람인·원티드·점핏·피플앤잡 통합 수집',
        theme_color: '#3f51b5',
        background_color: '#f5f6fa',
        display: 'standalone',
        orientation: 'portrait',
        start_url: '/',
        icons: [
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png',
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable',
          },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
        runtimeCaching: [
          {
            urlPattern: /^https?:\/\/.*\/api\//,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: { maxEntries: 50, maxAgeSeconds: 60 * 60 },
            },
          },
        ],
      },
    }),
  ],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
