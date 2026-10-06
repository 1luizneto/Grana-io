import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    // Escuta em 0.0.0.0 dentro do container: acessível por localhost e pelo IP da rede (FR-018).
    host: true,
    port: 5173,
    strictPort: true,
    // Eventos de arquivo do Windows não chegam ao container pelo bind mount (FR-015).
    watch: { usePolling: true, interval: 300 },
    // A interface chama a API por /api no mesmo endereço; o Vite repassa ao backend
    // pela rede interna do Compose (research R-06).
    proxy: {
      '/api': {
        target: process.env.API_PROXY_TARGET ?? 'http://backend:8000',
        changeOrigin: true,
        // Envia X-Forwarded-For com o endereço de quem abriu a interface, para o limite de
        // tentativas de login contar por dispositivo (specs/003-login-logout, research R-08).
        xfwd: true,
      },
    },
  },
  // Testes da interface (specs/005-telas-login-cadastro, research R-07):
  // docker compose run --rm frontend npm test
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/testes/preparacao.js'],
    restoreMocks: true,
  },
})
