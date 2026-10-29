import axios from 'axios'
import { clearToken, getToken } from './tokenStorage'

// Fallback garante que o projeto funcione mesmo sem o .env copiado.
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8080',
  timeout: 10000,
})

api.interceptors.request.use((config) => {
  const token = getToken()

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

type UnauthorizedHandler = () => void

let onUnauthorized: UnauthorizedHandler | null = null

/** Registrado pelo AuthProvider para encerrar a sessão quando o token expira. */
export function setUnauthorizedHandler(handler: UnauthorizedHandler | null): void {
  onUnauthorized = handler
}

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const isLoginRequest = error.config?.url === '/auth/login'

    // 401 fora do login significa token ausente, inválido ou expirado.
    if (axios.isAxiosError(error) && error.response?.status === 401 && !isLoginRequest) {
      if (getToken()) {
        clearToken()
        onUnauthorized?.()
      }
    }

    return Promise.reject(error)
  },
)

export function getErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail

    if (typeof detail === 'string') {
      return detail
    }

    if (!error.response) {
      return 'Não foi possível conectar ao servidor. Verifique se a API está em execução.'
    }
  }

  return fallback
}
