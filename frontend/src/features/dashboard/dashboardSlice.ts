import { createAsyncThunk, createSlice } from '@reduxjs/toolkit'
import { dashboardApi } from '@/services/dashboardApi'
import { ApiError } from '@/services/http'
import type { DashboardSummary } from '@/shared/types'

type LoadStatus = 'idle' | 'loading' | 'succeeded' | 'failed'

type DashboardState = {
  summary: DashboardSummary | null
  status: LoadStatus
  error: string | null
}

const initialState: DashboardState = {
  summary: null,
  status: 'idle',
  error: null,
}

export const fetchDashboardSummary = createAsyncThunk(
  'dashboard/fetchSummary',
  async (_, { rejectWithValue }) => {
    try {
      return await dashboardApi.getSummary()
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Failed to load dashboard'
      return rejectWithValue(message)
    }
  },
)

const dashboardSlice = createSlice({
  name: 'dashboard',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchDashboardSummary.pending, (state) => {
        state.status = 'loading'
        state.error = null
      })
      .addCase(fetchDashboardSummary.fulfilled, (state, action) => {
        state.status = 'succeeded'
        state.summary = action.payload
      })
      .addCase(fetchDashboardSummary.rejected, (state, action) => {
        state.status = 'failed'
        state.error = (action.payload as string) || 'Failed to load dashboard'
      })
  },
})

export default dashboardSlice.reducer
