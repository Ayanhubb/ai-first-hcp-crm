/**
 * Axios HTTP client for FastAPI `/api/v1`.
 * Bearer attachment, X-Request-ID, refresh-on-401, longer `/ai/*` timeout.
 */
import axios, {
  type AxiosError,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from 'axios'

const ACCESS_KEY = 'hcp_crm_access_token'
const REFRESH_KEY = 'hcp_crm_refresh_token'

export type ApiErrorBody = {
  code: string
  message: string
  details?: unknown[]
  correlation_id?: string | null
}

export class ApiError extends Error {
  code: string
  details: unknown[]
  correlationId: string | null
  status: number

  constructor(
    message: string,
    opts: {
      code?: string
      details?: unknown[]
      correlationId?: string | null
      status?: number
    } = {},
  ) {
    super(message)
    this.name = 'ApiError'
    this.code = opts.code ?? 'INTERNAL_ERROR'
    this.details = opts.details ?? []
    this.correlationId = opts.correlationId ?? null
    this.status = opts.status ?? 500
  }
}

type RetriableConfig = InternalAxiosRequestConfig & { _retry?: boolean }

let accessTokenMemory: string | null = localStorage.getItem(ACCESS_KEY)
let refreshTokenMemory: string | null = localStorage.getItem(REFRESH_KEY)
let refreshPromise: Promise<string | null> | null = null
let onAuthFailure: (() => void) | null = null

export function setAuthTokens(access: string | null, refresh: string | null): void {
  accessTokenMemory = access
  refreshTokenMemory = refresh
  if (access) localStorage.setItem(ACCESS_KEY, access)
  else localStorage.removeItem(ACCESS_KEY)
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh)
  else localStorage.removeItem(REFRESH_KEY)
}

export function getAccessToken(): string | null {
  return accessTokenMemory ?? localStorage.getItem(ACCESS_KEY)
}

export function getRefreshToken(): string | null {
  return refreshTokenMemory ?? localStorage.getItem(REFRESH_KEY)
}

export function clearAuthTokens(): void {
  setAuthTokens(null, null)
}

export function setOnAuthFailure(handler: (() => void) | null): void {
  onAuthFailure = handler
}

function newRequestId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID()
  }
  return `req-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function normalizeError(error: AxiosError): ApiError {
  const status = error.response?.status ?? 0
  const data = error.response?.data as { error?: ApiErrorBody } | undefined
  const envelope = data?.error
  return new ApiError(envelope?.message || error.message || 'Request failed', {
    code: envelope?.code ?? 'INTERNAL_ERROR',
    details: envelope?.details ?? [],
    correlationId: envelope?.correlation_id ?? null,
    status,
  })
}

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export const http: AxiosInstance = axios.create({
  baseURL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

http.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  config.headers['X-Request-ID'] = newRequestId()
  const url = config.url ?? ''
  if (url.includes('/ai/') || url.endsWith('/ai') || url.includes('/ai?')) {
    config.timeout = 60000
  }
  return config
})

async function refreshAccessToken(): Promise<string | null> {
  const refresh = getRefreshToken()
  if (!refresh) return null
  try {
    const { data } = await axios.post<{
      access_token: string
      refresh_token: string
    }>(`${baseURL}/auth/refresh`, { refresh_token: refresh }, { timeout: 15000 })
    setAuthTokens(data.access_token, data.refresh_token)
    return data.access_token
  } catch {
    clearAuthTokens()
    onAuthFailure?.()
    return null
  }
}

http.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetriableConfig | undefined
    if (
      error.response?.status === 401 &&
      original &&
      !original._retry &&
      !original.url?.includes('/auth/login') &&
      !original.url?.includes('/auth/refresh')
    ) {
      original._retry = true
      if (!refreshPromise) {
        refreshPromise = refreshAccessToken().finally(() => {
          refreshPromise = null
        })
      }
      const newToken = await refreshPromise
      if (newToken) {
        original.headers.Authorization = `Bearer ${newToken}`
        return http(original)
      }
    }
    return Promise.reject(normalizeError(error))
  },
)
