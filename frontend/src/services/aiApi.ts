import { http } from '@/services/http'
import type { AiAssistantResult, FollowUp, ProductRef, Sentiment } from '@/shared/types'

type ApiAiAssist = {
  ai_run_id: string
  status: string
  summary?: string | null
  sentiment?: Sentiment | 'mixed' | null
  sentiment_score?: number | null
  products?: Array<{
    product_id: string
    name: string
    code?: string | null
    confidence?: number
  }>
  medical_topics?: string[]
  follow_ups?: Array<{
    title: string
    description?: string | null
    priority?: string
    due_in_days?: number | null
  }>
  history_summary?: string | null
  notes?: string | null
  errors?: Array<{ message?: string } | string>
}

function mapSentiment(value: string | null | undefined): Sentiment {
  if (value === 'positive' || value === 'neutral' || value === 'negative') return value
  return 'neutral'
}

function mapResult(data: ApiAiAssist): AiAssistantResult & { aiRunId: string; notes?: string } {
  const products: ProductRef[] = (data.products ?? []).map((p) => ({
    id: p.product_id,
    name: p.name,
  }))
  const followUps: FollowUp[] = (data.follow_ups ?? []).map((f, idx) => {
    const due =
      f.due_in_days != null
        ? new Date(Date.now() + f.due_in_days * 86400000).toISOString().slice(0, 10)
        : undefined
    return {
      id: `ai-fu-${idx}`,
      text: f.title,
      dueDate: due,
    }
  })
  const errors = (data.errors ?? []).map((e) =>
    typeof e === 'string' ? e : e.message || 'AI error',
  )
  return {
    aiRunId: data.ai_run_id,
    summary: data.summary ?? '',
    sentiment: mapSentiment(data.sentiment),
    sentimentScore: data.sentiment_score ?? 0,
    products,
    topics: data.medical_topics ?? [],
    followUps,
    historySummary: data.history_summary ?? '',
    errors,
    notes: data.notes ?? undefined,
  }
}

export const aiApi = {
  async assist(args: {
    hcpId: string
    notes: string
    interactionId?: string
    includeHistory?: boolean
  }): Promise<AiAssistantResult & { aiRunId: string }> {
    const { data } = await http.post<ApiAiAssist>('/ai/assist', {
      hcp_id: args.hcpId,
      notes: args.notes,
      interaction_id: args.interactionId,
      include_history: args.includeHistory ?? true,
    })
    return mapResult(data)
  },

  async edit(args: {
    hcpId: string
    notes: string
    editInstruction: string
    currentAiFields?: Record<string, unknown>
    regenerateDerived?: boolean
  }): Promise<AiAssistantResult & { aiRunId: string; notes?: string }> {
    const { data } = await http.post<ApiAiAssist>('/ai/edit', {
      hcp_id: args.hcpId,
      notes: args.notes,
      edit_instruction: args.editInstruction,
      current_ai_fields: args.currentAiFields,
      regenerate_derived: args.regenerateDerived ?? true,
    })
    return mapResult(data)
  },

  async historySummary(hcpId: string): Promise<{
    aiRunId: string
    historySummary: string
    interactionsConsidered: number
  }> {
    const { data } = await http.post<{
      ai_run_id: string
      history_summary?: string | null
      interactions_considered: number
    }>('/ai/history-summary', { hcp_id: hcpId })
    return {
      aiRunId: data.ai_run_id,
      historySummary: data.history_summary ?? '',
      interactionsConsidered: data.interactions_considered,
    }
  },
}
