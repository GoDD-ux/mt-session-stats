import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Порт, на котором мод поднимает сервер в игре (mods/configs/session_stats/config.json)
const MOD_SERVER = 'http://127.0.0.1:16150';

export default defineConfig({
  plugins: [react()],
  // файлы отдаются из корня локального сервера мода, пути должны быть относительными
  base: './',
  build: {
    outDir: 'dist',
    // во встроенном браузере клиента не самый свежий движок
    target: 'es2017',
    assetsInlineLimit: 0,
  },
  server: {
    // при запущенной игре интерфейс можно разрабатывать в обычном браузере на живых данных
    proxy: { '/api': MOD_SERVER },
  },
});
