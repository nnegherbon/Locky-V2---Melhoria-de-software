import { api } from './api'
import type { User } from '../types/user'

type LoginResponse = {
  access_token: string
  token_type: string
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>('/auth/login', { email, password })
  return data
}

export async function getCurrentUser(): Promise<User> {
  const { data } = await api.get<User>('/auth/me')
  return data
}

export async function register(name: string, email: string, password: string): Promise<User> {
  const { data } = await api.post<User>('/auth/register', { name, email, password })
  return data
}
