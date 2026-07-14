import { http } from '@/services/http'
import type { Hcp } from '@/shared/types'

type ApiHcp = {
  id: string
  first_name: string
  last_name: string
  specialty: string
  institution?: string | null
  city?: string | null
}

type Page<T> = {
  items: T[]
  total: number
  page: number
  page_size: number
}

function mapHcp(row: ApiHcp): Hcp {
  return {
    id: row.id,
    name: `${row.first_name} ${row.last_name}`.trim(),
    specialty: row.specialty,
    institution: row.institution ?? '',
    city: row.city ?? '',
  }
}

export type CreateHcpPayload = {
  firstName: string
  lastName: string
  specialty: string
  institution?: string
  city?: string
  state?: string
  country?: string
  email?: string
  phone?: string
}

export const hcpApi = {
  async create(payload: CreateHcpPayload): Promise<Hcp> {
    const { data } = await http.post<ApiHcp>('/hcps', {
      first_name: payload.firstName.trim(),
      last_name: payload.lastName.trim(),
      specialty: payload.specialty.trim(),
      institution: payload.institution?.trim() || null,
      city: payload.city?.trim() || null,
      state: payload.state?.trim() || null,
      country: payload.country?.trim() || null,
      email: payload.email?.trim() || null,
      phone: payload.phone?.trim() || null,
    })
    return mapHcp(data)
  },

  async search(params: {
    query?: string
    specialty?: string
    city?: string
    institution?: string
    page?: number
    pageSize?: number
    sort?: string
  }): Promise<{ results: Hcp[]; total: number; page: number; pageSize: number }> {
    const { data } = await http.get<Page<ApiHcp>>('/hcps', {
      params: {
        query: params.query || undefined,
        specialty: params.specialty || undefined,
        city: params.city || undefined,
        institution: params.institution || undefined,
        page: params.page ?? 1,
        page_size: params.pageSize ?? 10,
        sort: params.sort,
      },
    })
    return {
      results: data.items.map(mapHcp),
      total: data.total,
      page: data.page,
      pageSize: data.page_size,
    }
  },

  async getById(id: string): Promise<Hcp> {
    const { data } = await http.get<ApiHcp>(`/hcps/${id}`)
    return mapHcp(data)
  },
}
