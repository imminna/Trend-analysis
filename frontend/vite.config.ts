import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  // GitHub Pages 部署時的 base path（設定為 repo 名稱）
  base: process.env.VITE_BASE_PATH || '/',
})
