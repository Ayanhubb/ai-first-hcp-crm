import { createAsyncThunk, createSlice, type PayloadAction } from '@reduxjs/toolkit'
import { interactionApi, type SaveInteractionPayload } from '@/services/interactionApi'
import { ApiError } from '@/services/http'
import type { Interaction, Sentiment } from '@/shared/types'

type LoadStatus = 'idle' | 'loading' | 'succeeded' | 'failed'

type HistoryFilters = {
  hcpName: string
  sentiment: '' | Sentiment
  fromDate: string
  toDate: string
}

type HistoryState = {
  items: Interaction[]
  selected: Interaction | null
  filters: HistoryFilters
  pagination: { page: number; pageSize: number; total: number }
  status: LoadStatus
  saveStatus: LoadStatus
  error: string | null
}

const initialState: HistoryState = {
  items: [],
  selected: null,
  filters: { hcpName: '', sentiment: '', fromDate: '', toDate: '' },
  pagination: { page: 1, pageSize: 10, total: 0 },
  status: 'idle',
  saveStatus: 'idle',
  error: null,
}

export const fetchInteractions = createAsyncThunk(
  'history/fetch',
  async (filters: HistoryFilters, { rejectWithValue }) => {
    try {
      const result = await interactionApi.list({
        page: 1,
        pageSize: 50,
        sentiment: filters.sentiment || undefined,
        visitFrom: filters.fromDate || undefined,
        visitTo: filters.toDate || undefined,
      })
      let items = result.items
      if (filters.hcpName) {
        const q = filters.hcpName.toLowerCase()
        items = items.filter((i) => i.hcpName.toLowerCase().includes(q))
      }
      return { items, total: items.length }
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Failed to load history'
      return rejectWithValue(message)
    }
  },
)

export const fetchInteractionById = createAsyncThunk(
  'history/fetchById',
  async (id: string, { rejectWithValue }) => {
    try {
      return await interactionApi.getById(id)
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Interaction not found'
      return rejectWithValue(message)
    }
  },
)

export const saveInteraction = createAsyncThunk(
  'history/save',
  async (payload: SaveInteractionPayload, { rejectWithValue }) => {
    try {
      return await interactionApi.create(payload)
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Save failed'
      return rejectWithValue(message)
    }
  },
)

const historySlice = createSlice({
  name: 'history',
  initialState,
  reducers: {
    setHistoryFilters(state, action: PayloadAction<Partial<HistoryFilters>>) {
      state.filters = { ...state.filters, ...action.payload }
    },
    clearSelected(state) {
      state.selected = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchInteractions.pending, (state) => {
        state.status = 'loading'
        state.error = null
      })
      .addCase(fetchInteractions.fulfilled, (state, action) => {
        state.status = 'succeeded'
        state.items = action.payload.items
        state.pagination.total = action.payload.total
      })
      .addCase(fetchInteractions.rejected, (state, action) => {
        state.status = 'failed'
        state.error = (action.payload as string) || 'Failed to load history'
      })
      .addCase(fetchInteractionById.pending, (state) => {
        state.status = 'loading'
        state.error = null
      })
      .addCase(fetchInteractionById.fulfilled, (state, action) => {
        state.status = 'succeeded'
        state.selected = action.payload
      })
      .addCase(fetchInteractionById.rejected, (state, action) => {
        state.status = 'failed'
        state.error = (action.payload as string) || 'Not found'
      })
      .addCase(saveInteraction.pending, (state) => {
        state.saveStatus = 'loading'
      })
      .addCase(saveInteraction.fulfilled, (state, action) => {
        state.saveStatus = 'succeeded'
        state.items = [action.payload, ...state.items]
        state.selected = action.payload
        state.pagination.total += 1
      })
      .addCase(saveInteraction.rejected, (state, action) => {
        state.saveStatus = 'failed'
        state.error = (action.payload as string) || 'Save failed'
      })
  },
})

export const { setHistoryFilters, clearSelected } = historySlice.actions
export default historySlice.reducer
