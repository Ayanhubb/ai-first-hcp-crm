import { clearAuthTokens, http, setAuthTokens } from '@/services/http'
import type { AuthUser } from '@/shared/types'

type ApiUser = {
  id: string
  email: string
  full_name: string
  role: 'mr' | 'admin'
  is_active?: boolean
  created_at?: string
}

type TokenPayload = {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user?: ApiUser
}

function mapUser(user: ApiUser): AuthUser {
  return {
    id: user.id,
    email: user.email,
    name: user.full_name,
    role: user.role,
  }
}

export const authApi = {
  async login(email: string, password: string): Promise<{ user: AuthUser; accessToken: string }> {
    const { data } = await http.post<TokenPayload & { user: ApiUser }>('/auth/login', {
      email,
      password,
    })
    setAuthTokens(data.access_token, data.refresh_token)
    return { user: mapUser(data.user), accessToken: data.access_token }
  },

  async refresh(): Promise<{ user: AuthUser | null; accessToken: string }> {
    const refresh_token = localStorage.getItem('hcp_crm_refresh_token')
    if (!refresh_token) throw new Error('No refresh token')
    const { data } = await http.post<TokenPayload>('/auth/refresh', { refresh_token })
    setAuthTokens(data.access_token, data.refresh_token)
    return {
      user: data.user ? mapUser(data.user) : null,
      accessToken: data.access_token,
    }
  },

  async logout(): Promise<void> {
    const refresh_token = localStorage.getItem('hcp_crm_refresh_token')
    try {
      if (refresh_token) {
        await http.post('/auth/logout', { refresh_token })
      }
    } finally {
      clearAuthTokens()
    }
  },

  async me(): Promise<AuthUser> {
    const { data } = await http.get<ApiUser>('/users/me')
    return mapUser(data)
  },
}
