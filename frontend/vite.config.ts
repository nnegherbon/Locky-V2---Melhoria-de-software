import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  // No Vercel, sem VITE_API_URL o build usaria http://localhost:8080 e o site
  // publicado não conseguiria falar com a API. Melhor falhar o deploy.
  if (process.env.VERCEL && !env.VITE_API_URL) {
    throw new Error(
      'Defina a variável VITE_API_URL no projeto do Vercel (URL da API, sem barra no final).',
    )
  }

  return {
    plugins: [react()],
  }
})
