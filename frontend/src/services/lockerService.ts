import { api } from './api'
import type {
  CreateLockerPayload,
  Locker,
  LockerFilters,
  LockerStats,
  UpdateLockerPayload,
} from '../types/locker'

type LockerListResponse = {
  items: Locker[]
  total: number
  limit: number
  offset: number
}

export async function getLockers(filters: LockerFilters = {}): Promise<LockerListResponse> {
  const { data } = await api.get<LockerListResponse>('/lockers', { params: filters })
  return data
}

export async function getLockerStats(): Promise<LockerStats> {
  const { data } = await api.get<LockerStats>('/lockers/stats')
  return data
}

export async function createLocker(payload: CreateLockerPayload): Promise<Locker> {
  const { data } = await api.post<Locker>('/lockers', payload)
  return data
}

export async function updateLocker(id: number, payload: UpdateLockerPayload): Promise<Locker> {
  const { data } = await api.patch<Locker>(`/lockers/${id}`, payload)
  return data
}

export async function deleteLocker(id: number): Promise<void> {
  await api.delete(`/lockers/${id}`)
}
