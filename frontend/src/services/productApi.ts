import { http } from '@/services/http'
import type { ProductRef } from '@/shared/types'

type ApiProduct = {
  id: string
  code: string
  name: string
  therapeutic_area?: string | null
  is_active: boolean
}

type Page<T> = {
  items: T[]
  total: number
  page: number
  page_size: number
}

export const productApi = {
  async list(params?: {
    query?: string
    page?: number
    pageSize?: number
  }): Promise<{ items: ProductRef[]; total: number }> {
    const { data } = await http.get<Page<ApiProduct>>('/products', {
      params: {
        query: params?.query,
        page: params?.page ?? 1,
        page_size: params?.pageSize ?? 50,
      },
    })
    return {
      items: data.items.map((p) => ({ id: p.id, name: p.name })),
      total: data.total,
    }
  },
}
