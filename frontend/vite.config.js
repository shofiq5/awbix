import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import Icons from 'unplugin-icons/vite'
import { FileSystemIconLoader } from 'unplugin-icons/loaders'
import { webserver_port } from '../../../sites/common_site_config.json'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    Icons({
      compiler: 'vue3',
      customCollections: {
        lucide: FileSystemIconLoader(
          path.resolve(__dirname, 'node_modules/lucide-static/icons'),
          (svg) => svg.replace(/^<svg\s/, '<svg class="lucide" ')
        ),
      },
    }),
  ],
  server: {
    port: 8080,
    proxy: {
      '^/app': {
        target: `http://localhost:${webserver_port}`,
        changeOrigin: true,
      },
      '^/api': {
        target: `http://localhost:${webserver_port}`,
        changeOrigin: true,
      },
      '^/rest': {
        target: `http://localhost:${webserver_port}`,
        changeOrigin: true,
      },
      '^/login': {
        target: `http://localhost:${webserver_port}`,
        changeOrigin: true,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  build: {
    outDir: `../${path.basename(path.resolve('..'))}/public/frontend`,
    emptyOutDir: true,
    target: 'es2015',
  },
  optimizeDeps: {
    include: ['frappe-ui > feather-icons', 'showdown', 'engine.io-client', 'highlight.js/lib/core', 'lowlight', 'interactjs', 'debug'],
  },
})
