import { createContext, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import {
  getCurrentUser,
  login as loginRequest,
  register as registerRequest,
} from '../services/authService'
import { clearToken, getToken, setToken } from '../services/tokenStorage'
import type { User } from '../types/user'

type AuthContextValue = {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (name: string, email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(() => Boolean(getToken()))

  useEffect(() => {
    if (!getToken()) {
      return
    }

    getCurrentUser()
      .then(setUser)
      .catch(() => clearToken())
      .finally(() => setLoading(false))
  }, [])

  async function login(email: string, password: string) {
    const { access_token } = await loginRequest(email, password)
    setToken(access_token)
    const me = await getCurrentUser()
    setUser(me)
  }

  async function register(name: string, email: string, password: string) {
    await registerRequest(name, email, password)
    await login(email, password)
  }

  function logout() {
    clearToken()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components -- hook precisa ficar junto do Provider
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error('useAuth deve ser usado dentro de AuthProvider')
  }

  return context
}
