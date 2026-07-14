import { createAsyncThunk, createSlice, type PayloadAction } from '@reduxjs/toolkit'
import { authApi } from '@/services/authApi'
import { ApiError, clearAuthTokens, setOnAuthFailure } from '@/services/http'
import type { AuthUser } from '@/shared/types'

type AuthStatus = 'idle' | 'loading' | 'authenticated' | 'error'

type AuthState = {
  user: AuthUser | null
  accessToken: string | null
  status: AuthStatus
  error: string | null
}

const initialState: AuthState = {
  user: null,
  accessToken: null,
  status: 'idle',
  error: null,
}

export const login = createAsyncThunk(
  'auth/login',
  async (
    credentials: { email: string; password: string },
    { rejectWithValue },
  ) => {
    try {
      return await authApi.login(credentials.email, credentials.password)
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Login failed'
      return rejectWithValue(message)
    }
  },
)

export const logout = createAsyncThunk('auth/logout', async () => {
  await authApi.logout()
  return true
})

export const bootstrapSession = createAsyncThunk(
  'auth/bootstrap',
  async (_, { rejectWithValue }) => {
    try {
      const refresh = localStorage.getItem('hcp_crm_refresh_token')
      if (!refresh) {
        return rejectWithValue('No session')
      }
      const refreshed = await authApi.refresh()
      const user = refreshed.user ?? (await authApi.me())
      return { user, accessToken: refreshed.accessToken }
    } catch {
      clearAuthTokens()
      return rejectWithValue('Session expired')
    }
  },
)

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setCredentials(
      state,
      action: PayloadAction<{ user: AuthUser; accessToken: string }>,
    ) {
      state.user = action.payload.user
      state.accessToken = action.payload.accessToken
      state.status = 'authenticated'
      state.error = null
    },
    clearAuth(state) {
      state.user = null
      state.accessToken = null
      state.status = 'idle'
      state.error = null
      clearAuthTokens()
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(login.pending, (state) => {
        state.status = 'loading'
        state.error = null
      })
      .addCase(login.fulfilled, (state, action) => {
        state.user = action.payload.user
        state.accessToken = action.payload.accessToken
        state.status = 'authenticated'
        state.error = null
      })
      .addCase(login.rejected, (state, action) => {
        state.status = 'error'
        state.error = (action.payload as string) || 'Login failed'
      })
      .addCase(logout.fulfilled, (state) => {
        state.user = null
        state.accessToken = null
        state.status = 'idle'
        state.error = null
      })
      .addCase(bootstrapSession.fulfilled, (state, action) => {
        state.user = action.payload.user
        state.accessToken = action.payload.accessToken
        state.status = 'authenticated'
        state.error = null
      })
      .addCase(bootstrapSession.rejected, (state) => {
        state.user = null
        state.accessToken = null
        state.status = 'idle'
      })
  },
})

export const { setCredentials, clearAuth } = authSlice.actions

/** Wire HTTP 401 → clear auth after refresh failure. Call once from app bootstrap. */
export function bindAuthFailureHandler(dispatch: (action: { type: string }) => void): void {
  setOnAuthFailure(() => {
    dispatch(clearAuth())
  })
}

export default authSlice.reducer
