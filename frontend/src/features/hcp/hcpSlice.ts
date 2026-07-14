import { createAsyncThunk, createSlice, type PayloadAction } from '@reduxjs/toolkit'
import { hcpApi } from '@/services/hcpApi'
import { ApiError } from '@/services/http'
import type { Hcp } from '@/shared/types'

type LoadStatus = 'idle' | 'loading' | 'succeeded' | 'failed'

type HcpState = {
  query: string
  filters: { specialty: string; city: string }
  results: Hcp[]
  selectedHcp: Hcp | null
  pagination: { page: number; pageSize: number; total: number }
  status: LoadStatus
  error: string | null
}

const initialState: HcpState = {
  query: '',
  filters: { specialty: '', city: '' },
  results: [],
  selectedHcp: null,
  pagination: { page: 1, pageSize: 10, total: 0 },
  status: 'idle',
  error: null,
}

export const searchHcps = createAsyncThunk(
  'hcp/search',
  async (
    args: {
      query: string
      specialty?: string
      city?: string
      page?: number
      pageSize?: number
    },
    { rejectWithValue },
  ) => {
    try {
      return await hcpApi.search({
        query: args.query,
        specialty: args.specialty,
        city: args.city,
        page: args.page ?? 1,
        pageSize: args.pageSize ?? 10,
      })
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'HCP search failed'
      return rejectWithValue(message)
    }
  },
)

const hcpSlice = createSlice({
  name: 'hcp',
  initialState,
  reducers: {
    setQuery(state, action: PayloadAction<string>) {
      state.query = action.payload
    },
    setFilters(
      state,
      action: PayloadAction<Partial<{ specialty: string; city: string }>>,
    ) {
      state.filters = { ...state.filters, ...action.payload }
    },
    setSelectedHcp(state, action: PayloadAction<Hcp | null>) {
      state.selectedHcp = action.payload
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(searchHcps.pending, (state) => {
        state.status = 'loading'
        state.error = null
      })
      .addCase(searchHcps.fulfilled, (state, action) => {
        state.status = 'succeeded'
        state.results = action.payload.results
        state.pagination = {
          page: action.payload.page,
          pageSize: action.payload.pageSize,
          total: action.payload.total,
        }
      })
      .addCase(searchHcps.rejected, (state, action) => {
        state.status = 'failed'
        state.error = (action.payload as string) || 'Search failed'
      })
  },
})

export const { setQuery, setFilters, setSelectedHcp } = hcpSlice.actions
export default hcpSlice.reducer
