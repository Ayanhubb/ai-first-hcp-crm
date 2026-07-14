import { createAsyncThunk, createSlice, type PayloadAction } from '@reduxjs/toolkit'
import { aiApi } from '@/services/aiApi'
import { ApiError } from '@/services/http'
import type { FollowUp, ProductRef, Sentiment } from '@/shared/types'

type RunStatus = 'idle' | 'loading' | 'succeeded' | 'failed'

type AiAssistantState = {
  runStatus: RunStatus
  aiRunId: string | null
  summary: string
  sentiment: Sentiment | null
  sentimentScore: number | null
  products: ProductRef[]
  topics: string[]
  followUps: FollowUp[]
  historySummary: string
  errors: string[]
  panelOpen: boolean
}

const initialState: AiAssistantState = {
  runStatus: 'idle',
  aiRunId: null,
  summary: '',
  sentiment: null,
  sentimentScore: null,
  products: [],
  topics: [],
  followUps: [],
  historySummary: '',
  errors: [],
  panelOpen: true,
}

export const runAssist = createAsyncThunk(
  'aiAssistant/assist',
  async (args: { notes: string; hcpId: string }, { rejectWithValue }) => {
    try {
      return await aiApi.assist({ hcpId: args.hcpId, notes: args.notes })
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'AI assist unavailable'
      return rejectWithValue(message)
    }
  },
)

export const runEditAssist = createAsyncThunk(
  'aiAssistant/edit',
  async (
    args: {
      instruction: string
      currentSummary: string
      hcpId: string
      notes: string
    },
    { rejectWithValue },
  ) => {
    try {
      const result = await aiApi.edit({
        hcpId: args.hcpId,
        notes: args.notes,
        editInstruction: args.instruction,
        currentAiFields: { summary: args.currentSummary },
      })
      return { summary: result.summary || args.currentSummary }
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Edit assist failed'
      return rejectWithValue(message)
    }
  },
)

const aiAssistantSlice = createSlice({
  name: 'aiAssistant',
  initialState,
  reducers: {
    clearAiAssistant() {
      return initialState
    },
    setPanelOpen(state, action: PayloadAction<boolean>) {
      state.panelOpen = action.payload
    },
    setSummary(state, action: PayloadAction<string>) {
      state.summary = action.payload
    },
    setSentiment(
      state,
      action: PayloadAction<{ sentiment: Sentiment; sentimentScore: number }>,
    ) {
      state.sentiment = action.payload.sentiment
      state.sentimentScore = action.payload.sentimentScore
    },
    setProducts(state, action: PayloadAction<ProductRef[]>) {
      state.products = action.payload
    },
    setTopics(state, action: PayloadAction<string[]>) {
      state.topics = action.payload
    },
    setFollowUps(state, action: PayloadAction<FollowUp[]>) {
      state.followUps = action.payload
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(runAssist.pending, (state) => {
        state.runStatus = 'loading'
        state.errors = []
      })
      .addCase(runAssist.fulfilled, (state, action) => {
        state.runStatus = 'succeeded'
        state.aiRunId = action.payload.aiRunId
        state.summary = action.payload.summary
        state.sentiment = action.payload.sentiment
        state.sentimentScore = action.payload.sentimentScore
        state.products = action.payload.products
        state.topics = action.payload.topics
        state.followUps = action.payload.followUps
        state.historySummary = action.payload.historySummary
        state.errors = action.payload.errors
      })
      .addCase(runAssist.rejected, (state, action) => {
        state.runStatus = 'failed'
        state.errors = [(action.payload as string) || 'AI assist unavailable']
      })
      .addCase(runEditAssist.pending, (state) => {
        state.runStatus = 'loading'
      })
      .addCase(runEditAssist.fulfilled, (state, action) => {
        state.runStatus = 'succeeded'
        state.summary = action.payload.summary
      })
      .addCase(runEditAssist.rejected, (state, action) => {
        state.runStatus = 'failed'
        state.errors = [(action.payload as string) || 'Edit assist failed']
      })
  },
})

export const {
  clearAiAssistant,
  setPanelOpen,
  setSummary,
  setSentiment,
  setProducts,
  setTopics,
  setFollowUps,
} = aiAssistantSlice.actions
export default aiAssistantSlice.reducer
