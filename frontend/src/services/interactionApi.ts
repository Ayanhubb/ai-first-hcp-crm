import { http } from '@/services/http'
import type {
  Channel,
  FollowUp,
  Interaction,
  ProductRef,
  Sentiment,
} from '@/shared/types'

type ApiProductLink = {
  product_id: string
  confidence?: string | number | null
  source?: string
  product?: { id: string; name: string; code?: string } | null
}

type ApiFollowUp = {
  id: string
  title: string
  description?: string | null
  due_at?: string | null
  priority?: string
  status?: string
}

type ApiInteractionDetail = {
  id: string
  hcp_id: string
  user_id: string
  visit_at: string
  channel: Channel
  notes: string
  summary?: string | null
  sentiment?: Sentiment | 'mixed' | null
  sentiment_score?: string | number | null
  medical_topics?: string[]
  created_at: string
  products?: ApiProductLink[]
  follow_ups?: ApiFollowUp[]
  hcp?: {
    first_name?: string
    last_name?: string
    full_name?: string
  } | null
}

type ApiInteractionSummary = {
  id: string
  hcp_id: string
  user_id: string
  visit_at: string
  channel: Channel
  status: string
  sentiment?: Sentiment | 'mixed' | null
  summary?: string | null
  created_at: string
  hcp_name?: string | null
}

type Page<T> = {
  items: T[]
  total: number
  page: number
  page_size: number
}

function mapSentiment(value: string | null | undefined): Sentiment {
  if (value === 'positive' || value === 'neutral' || value === 'negative') return value
  return 'neutral'
}

function mapProducts(rows: ApiProductLink[] | undefined): ProductRef[] {
  return (rows ?? []).map((p) => ({
    id: p.product?.id ?? p.product_id,
    name: p.product?.name ?? p.product_id,
  }))
}

function mapFollowUps(rows: ApiFollowUp[] | undefined): FollowUp[] {
  return (rows ?? []).map((f) => ({
    id: f.id,
    text: f.title,
    dueDate: f.due_at ?? undefined,
  }))
}

function mapDetail(row: ApiInteractionDetail): Interaction {
  const hcpName =
    row.hcp?.full_name ||
    [row.hcp?.first_name, row.hcp?.last_name].filter(Boolean).join(' ') ||
    ''
  return {
    id: row.id,
    hcpId: row.hcp_id,
    hcpName,
    visitAt: row.visit_at,
    channel: row.channel,
    notes: row.notes,
    summary: row.summary ?? '',
    sentiment: mapSentiment(row.sentiment),
    sentimentScore: Number(row.sentiment_score ?? 0),
    products: mapProducts(row.products),
    topics: row.medical_topics ?? [],
    followUps: mapFollowUps(row.follow_ups),
    createdAt: row.created_at,
  }
}

function mapSummary(row: ApiInteractionSummary): Interaction {
  return {
    id: row.id,
    hcpId: row.hcp_id,
    hcpName: row.hcp_name ?? '',
    visitAt: row.visit_at,
    channel: row.channel,
    notes: '',
    summary: row.summary ?? '',
    sentiment: mapSentiment(row.sentiment),
    sentimentScore: 0,
    products: [],
    topics: [],
    followUps: [],
    createdAt: row.created_at,
  }
}

export type SaveInteractionPayload = {
  hcpId: string
  visitAt: string
  channel: Channel
  notes: string
  summary?: string
  sentiment?: Sentiment
  sentimentScore?: number
  topics?: string[]
  productIds?: string[]
  followUps?: Array<{ text: string; dueDate?: string }>
  aiRunId?: string | null
}

export const interactionApi = {
  async list(params?: {
    page?: number
    pageSize?: number
    hcpId?: string
    sentiment?: string
    visitFrom?: string
    visitTo?: string
    sort?: string
  }): Promise<{ items: Interaction[]; total: number; page: number; pageSize: number }> {
    const { data } = await http.get<Page<ApiInteractionSummary>>('/interactions', {
      params: {
        page: params?.page ?? 1,
        page_size: params?.pageSize ?? 20,
        hcp_id: params?.hcpId,
        sentiment: params?.sentiment || undefined,
        visit_from: params?.visitFrom || undefined,
        visit_to: params?.visitTo || undefined,
        sort: params?.sort ?? 'visit_at:desc',
      },
    })
    return {
      items: data.items.map(mapSummary),
      total: data.total,
      page: data.page,
      pageSize: data.page_size,
    }
  },

  async getById(id: string): Promise<Interaction> {
    const { data } = await http.get<ApiInteractionDetail>(`/interactions/${id}`)
    return mapDetail(data)
  },

  async create(payload: SaveInteractionPayload): Promise<Interaction> {
    const { data } = await http.post<ApiInteractionDetail>('/interactions', {
      hcp_id: payload.hcpId,
      visit_at: payload.visitAt,
      channel: payload.channel,
      notes: payload.notes,
      summary: payload.summary,
      sentiment: payload.sentiment,
      sentiment_score: payload.sentimentScore,
      medical_topics: payload.topics ?? [],
      product_ids: payload.productIds ?? [],
      follow_ups: (payload.followUps ?? []).map((f) => ({
        title: f.text,
        due_at: f.dueDate ?? null,
        priority: 'medium',
      })),
      ai_run_id: payload.aiRunId ?? null,
      status: 'saved',
    })
    return mapDetail(data)
  },
}
