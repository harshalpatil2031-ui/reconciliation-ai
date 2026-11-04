import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg'],
      manifest: {
        name: 'शेतपाहणी अहवाल',
        short_name: 'शेतपाहणी',
        description: 'शेतातील नुकसानीचा अहवाल सुरक्षितपणे पाठवा',
        lang: 'mr-IN',
        display: 'standalone',
        orientation: 'portrait',
        theme_color: '#176b45',
        background_color: '#f5f7f2',
        icons: [
          { src: '/icon.svg', sizes: 'any', type: 'image/svg+xml', purpose: 'any' }
        ]
      },
      workbox: { globPatterns: ['**/*.{js,css,html,svg,json,woff2}'] }
    })
  ],
  server: { host: '0.0.0.0' }
});
