import { http } from '@/services/http'
import type { DashboardSummary, Interaction, Sentiment } from '@/shared/types'

type ApiDashboard = {
  interactions_this_week: number
  open_follow_ups: number
  recent_interactions: Array<{
    id: string
    hcp_name: string
    visit_at: string
    sentiment?: Sentiment | 'mixed' | null
  }>
  pending_follow_ups: Array<{
    id: string
    title: string
    due_at?: string | null
    priority: string
  }>
}

function mapSentiment(value: string | null | undefined): Sentiment {
  if (value === 'positive' || value === 'neutral' || value === 'negative') return value
  return 'neutral'
}

export const dashboardApi = {
  async getSummary(): Promise<DashboardSummary> {
    const { data } = await http.get<ApiDashboard>('/dashboard/summary')
    const recentInteractions: Interaction[] = data.recent_interactions.map((row) => ({
      id: row.id,
      hcpId: '',
      hcpName: row.hcp_name,
      visitAt: row.visit_at,
      channel: 'in_person',
      notes: '',
      summary: '',
      sentiment: mapSentiment(row.sentiment),
      sentimentScore: 0,
      products: [],
      topics: [],
      followUps: [],
      createdAt: row.visit_at,
    }))
    return {
      interactionsThisWeek: data.interactions_this_week,
      openFollowUps: data.open_follow_ups,
      recentInteractions,
      pendingFollowUps: data.pending_follow_ups.map((f) => ({
        id: f.id,
        text: f.title,
        hcpName: '',
        interactionId: '',
        dueDate: f.due_at ?? undefined,
      })),
    }
  },
}
