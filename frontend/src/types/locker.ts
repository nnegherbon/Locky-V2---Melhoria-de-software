export type LockerStatus = 'available' | 'reserved' | 'occupied' | 'maintenance'

export type LockerSize = 'small' | 'medium' | 'large'

export type Locker = {
  id: number
  number: string
  status: LockerStatus
  size: LockerSize
}

export type LockerStats = {
  total: number
  available: number
  reserved: number
  occupied: number
  maintenance: number
}

export type LockerFilters = {
  status?: LockerStatus
  size?: LockerSize
  limit?: number
  offset?: number
}

/** Status que o administrador pode definir; reservado/ocupado vêm das reservas. */
export type LockerAdminStatus = Extract<LockerStatus, 'available' | 'maintenance'>

export type CreateLockerPayload = {
  number: string
  size: LockerSize
  status?: LockerAdminStatus
}

export type UpdateLockerPayload = Partial<CreateLockerPayload>
