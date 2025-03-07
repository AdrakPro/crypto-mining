import { defineConfig } from 'vite'
import { createHtmlPlugin } from 'vite-plugin-html'

export default defineConfig({
  root: 'src',
  plugins: [createHtmlPlugin()],
  build: {
    outDir: '../dist',
    emptyOutDir: true
  },
  server: {
    open: true
  }
})